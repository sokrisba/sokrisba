#!/usr/bin/env python3
"""AI usage scoring and before/after comparison.

Subcommands
  score    usage.csv [--people people.csv] [--out-dir DIR] [--window-days N]
           [--power 0.6] [--regular 0.25] [--working-day-ratio 0.714]
           [--feature claude_code=claude_ai ...]
           --feature marks a tool that is a feature of another tool's seat
           (default: claude_code=claude_ai). Feature rows count for breadth
           and intensity but never as seats of their own, so they cannot
           inflate seat-holder or dormant counts.
  prepost  events.csv --cutover YYYY-MM-DD | --cutover-file cutovers.csv
           [--people people.csv] [--window-days 90] [--ramp-days 30]
           [--min-people 5] [--out-dir DIR]
           With --people, each person's share of a window is prorated by
           start_date/end_date, so joiners and leavers do not distort
           per person-month rates.

Input schemas (see assets/*_template.csv):
  usage.csv   person_email, team, tool, seat, active_days, sessions, tokens, window_days
  people.csv  person_email, name, team, role, start_date, end_date
  events.csv  person_email, team, date, <metric columns...>
              A metric column named *_hours or *_days is summarised by median
              (a duration); any other numeric column is summed per
              person-month (a count).
  cutovers.csv team, cutover_date

Only the standard library is used so the script runs anywhere.
"""
import argparse
import csv
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import date, timedelta


# ----------------------------------------------------------------- helpers

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"{path}: no rows")
    return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in rows]


def num(v, default=0.0):
    if v in ("", None):
        return default
    try:
        return float(v)
    except ValueError:
        return default


def truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes", "y", "t")


def pct(n, d):
    return f"{round(100 * n / d)}%" if d else "n/a"


def fmt_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def write_csv(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def parse_date(s):
    return date.fromisoformat(s[:10])


# ------------------------------------------------------------------- score

def cmd_score(a):
    usage = read_csv(a.usage)
    need = {"person_email", "tool", "seat", "active_days"}
    missing = need - set(usage[0])
    if missing:
        sys.exit(f"usage.csv is missing columns: {sorted(missing)}")

    people = {}
    if a.people:
        for p in read_csv(a.people):
            people[p["person_email"].lower()] = p

    def team_of(email, row_team):
        p = people.get(email)
        if p and p.get("team"):
            return p["team"]
        return row_team or "unassigned"

    # per person x tool
    per = {}
    for r in usage:
        email = r["person_email"].lower()
        if not email:
            continue
        tool = r["tool"].lower()
        wd = num(r.get("window_days"), a.window_days) or a.window_days
        key = (email, tool)
        rec = per.setdefault(key, {
            "email": email, "tool": tool, "team": team_of(email, r.get("team", "")),
            "seat": False, "active_days": 0.0, "sessions": 0.0, "tokens": 0.0,
            "has_tokens": False, "window_days": wd})
        rec["seat"] = rec["seat"] or truthy(r["seat"])
        rec["active_days"] = max(rec["active_days"], num(r["active_days"]))
        rec["sessions"] += num(r.get("sessions"))
        if r.get("tokens", "") != "":
            rec["tokens"] += num(r["tokens"])
            rec["has_tokens"] = True

    working = lambda wd: max(1.0, wd * a.working_day_ratio)
    features = {}
    for f in a.feature or []:
        if "=" in f:
            child, parent = f.split("=", 1)
            features[child.strip().lower()] = parent.strip().lower()
    # a feature row never carries a seat of its own
    for (email, tool), rec in per.items():
        if tool in features:
            rec["seat"] = False
            rec["feature_of"] = features[tool]

    def tier(share, seat):
        if share >= a.power:
            return "Power"
        if share >= a.regular:
            return "Regular"
        if share > 0:
            return "Light"
        return "Dormant" if seat else "No seat, inactive"

    # per person
    persons = {}
    for (email, tool), rec in per.items():
        p = persons.setdefault(email, {
            "email": email, "team": rec["team"], "seat_tools": set(), "active_tools": set(),
            "best_share": 0.0, "best_tool": "", "sessions": 0.0, "tokens": 0.0,
            "has_tokens": False, "active_without_seat": set(), "any_seat": False})
        active = rec["active_days"] > 0
        if rec["seat"]:
            p["seat_tools"].add(tool)
            p["any_seat"] = True
        if active:
            p["active_tools"].add(tool)
            if not rec["seat"] and tool not in features:
                p["active_without_seat"].add(tool)
        share = min(1.0, rec["active_days"] / working(rec["window_days"]))
        if share > p["best_share"]:
            p["best_share"], p["best_tool"] = share, tool
        p["sessions"] += rec["sessions"]
        if rec["has_tokens"]:
            p["tokens"] += rec["tokens"]
            p["has_tokens"] = True

    person_rows = []
    for email, p in sorted(persons.items()):
        info = people.get(email, {})
        person_rows.append([
            email, info.get("name", ""), p["team"], info.get("role", ""),
            ";".join(sorted(p["seat_tools"])), ";".join(sorted(p["active_tools"])),
            len(p["active_tools"]), p["best_tool"], f"{p['best_share']:.2f}",
            tier(p["best_share"], p["any_seat"]), int(p["sessions"]),
            f"{p['tokens'] / 1e6:.2f}" if p["has_tokens"] else "",
            ";".join(sorted(p["active_without_seat"])),
        ])
    person_headers = ["person_email", "name", "team", "role", "seat_tools", "active_tools",
                      "breadth", "most_used_tool", "active_day_share", "tier", "sessions",
                      "tokens_m", "active_without_seat"]

    # per tool
    tool_rows = []
    tools = sorted({t for (_, t) in per})
    for t in tools:
        recs = [r for (_, tt), r in per.items() if tt == t]
        if t in features:
            # seats belong to the parent tool; adoption = parent seat holders using the feature
            parent_seats = {e for (e, tt), r in per.items() if tt == features[t] and r["seat"]}
            seats = [r for r in recs if r["email"] in parent_seats]
            active_seats = [r for r in seats if r["active_days"] > 0]
            dormant, no_seat_active = [], []
            label = f"{t} (feature of {features[t]})"
        else:
            seats = [r for r in recs if r["seat"]]
            active_seats = [r for r in seats if r["active_days"] > 0]
            dormant = [r for r in seats if r["active_days"] == 0]
            no_seat_active = [r for r in recs if not r["seat"] and r["active_days"] > 0]
            label = t
        shares = [min(1.0, r["active_days"] / working(r["window_days"])) for r in active_seats]
        tok = [r for r in recs if r["has_tokens"]]
        tokens = sum(r["tokens"] for r in tok)
        sess = sum(r["sessions"] for r in recs)
        tool_rows.append([
            label, len(seats), len(active_seats), pct(len(active_seats), len(seats)),
            "n/a" if t in features else len(dormant),
            "n/a" if t in features else len(no_seat_active), f"{statistics.median(shares):.2f}" if shares else "n/a",
            int(sess), f"{tokens / 1e6:.2f}" if tok else "",
            f"{tokens / sess:,.0f}" if tok and sess else "",
            ";".join(sorted(r["email"] for r in dormant)),
        ])
    tool_headers = ["tool", "seat_holders", "active", "adoption_rate", "dormant",
                    "active_without_seat", "median_active_day_share", "sessions", "tokens_m",
                    "tokens_per_session", "dormant_emails"]

    # per team
    team_rows = []
    teams = sorted({p["team"] for p in persons.values()})
    for team in teams:
        ps = [p for p in persons.values() if p["team"] == team]
        seated = [p for p in ps if p["any_seat"]]
        active_seated = [p for p in seated if p["active_tools"]]
        tiers = defaultdict(int)
        for p in ps:
            tiers[tier(p["best_share"], p["any_seat"])] += 1
        breadth = defaultdict(int)
        for p in ps:
            breadth[min(3, len(p["active_tools"]))] += 1
        shares = [p["best_share"] for p in active_seated]
        team_rows.append([
            team, len(ps), len(seated), len(active_seated), pct(len(active_seated), len(seated)),
            tiers["Power"], tiers["Regular"], tiers["Light"], tiers["Dormant"],
            f"{statistics.median(shares):.2f}" if shares else "n/a",
            breadth[0], breadth[1], breadth[2], breadth[3],
        ])
    team_headers = ["team", "people", "seat_holders", "active", "adoption_rate", "power",
                    "regular", "light", "dormant", "median_active_day_share",
                    "breadth_0", "breadth_1", "breadth_2", "breadth_3plus"]

    os.makedirs(a.out_dir, exist_ok=True)
    write_csv(os.path.join(a.out_dir, "per_person.csv"), person_headers, person_rows)
    write_csv(os.path.join(a.out_dir, "per_tool.csv"), tool_headers, tool_rows)
    write_csv(os.path.join(a.out_dir, "per_team.csv"), team_headers, team_rows)

    total_seated = sum(1 for p in persons.values() if p["any_seat"])
    total_active = sum(1 for p in persons.values() if p["any_seat"] and p["active_tools"])
    md = [
        "# AI usage scoring",
        "",
        f"Window: {a.window_days} days (per row where given); working days = {a.working_day_ratio:.3f} x calendar days.",
        f"Tiers by active-day share on most-used tool: Power >= {a.power:.0%}, Regular >= {a.regular:.0%}, Light > 0, Dormant = 0 with seat. Share is capped at 1.0.",
        ("Feature tools (" + ", ".join(f"{c} within {p}" for c, p in features.items()) + ") count for breadth and intensity but not as seats; their adoption rate is the share of parent seat holders using the feature.") if features else "",
        f"People with a seat on any tool: {total_seated}; active on at least one: {total_active} ({pct(total_active, total_seated)}).",
        "",
        "## Per tool", "",
        fmt_table(tool_headers[:-1], [r[:-1] for r in tool_rows]),
        "",
        "## Per team", "",
        fmt_table(team_headers, team_rows),
        "",
        "Per-person detail is in per_person.csv (restricted distribution).",
        "Tokens are reported only for rows that carry a tokens value (API products) and are never added to seat-product activity.",
    ]
    with open(os.path.join(a.out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nWrote per_person.csv, per_tool.csv, per_team.csv, summary.md to {a.out_dir}")


# ----------------------------------------------------------------- prepost

def cmd_prepost(a):
    events = read_csv(a.events)
    need = {"person_email", "team", "date"}
    missing = need - set(events[0])
    if missing:
        sys.exit(f"events.csv is missing columns: {sorted(missing)}")
    metric_cols = [c for c in events[0] if c not in need]
    if not metric_cols:
        sys.exit("events.csv has no metric columns")

    cutovers = {}
    if a.cutover_file:
        for r in read_csv(a.cutover_file):
            cutovers[r["team"]] = parse_date(r["cutover_date"])
    default_cut = parse_date(a.cutover) if a.cutover else None
    if not cutovers and not default_cut:
        sys.exit("give --cutover or --cutover-file")

    tenure = {}
    if a.people:
        for r in read_csv(a.people):
            tenure[r["person_email"].lower()] = (
                parse_date(r["start_date"]) if r.get("start_date") else None,
                parse_date(r["end_date"]) if r.get("end_date") else None)

    def person_equiv(emails, lo, hi):
        """Sum of each person's share of the window, from tenure if known."""
        total = 0.0
        span = (hi - lo).days
        for em in emails:
            st, en = tenure.get(em, (None, None))
            s = max(lo, st) if st else lo
            e = min(hi, en) if en else hi
            total += max(0, (e - s).days) / span if span else 1
        return total

    by_team = defaultdict(list)
    for e in events:
        e["_d"] = parse_date(e["date"])
        by_team[e["team"]].append(e)

    is_duration = lambda c: c.endswith("_hours") or c.endswith("_days")
    rows, notes = [], []
    for team, evs in sorted(by_team.items()):
        cut = cutovers.get(team, default_cut)
        if not cut:
            notes.append(f"{team}: no cutover date, skipped")
            continue
        before = (cut - timedelta(days=a.window_days), cut)
        after = (cut + timedelta(days=a.ramp_days), cut + timedelta(days=a.ramp_days + a.window_days))
        months = a.window_days / 30.44

        def window(lo, hi):
            return [e for e in evs if lo <= e["_d"] < hi]

        wb, wa = window(*before), window(*after)
        pb = {e["person_email"].lower() for e in wb}
        pa = {e["person_email"].lower() for e in wa}
        small = len(pb) < a.min_people or len(pa) < a.min_people
        for c in metric_cols:
            vb = [num(e[c]) for e in wb if e.get(c, "") != ""]
            va = [num(e[c]) for e in wa if e.get(c, "") != ""]
            if is_duration(c):
                stat = "median"
                b = statistics.median(vb) if vb else None
                af = statistics.median(va) if va else None
            else:
                stat = "per person-month"
                peb, pea = person_equiv(pb, *before), person_equiv(pa, *after)
                b = sum(vb) / (peb * months) if peb else None
                af = sum(va) / (pea * months) if pea else None
            if b is None or af is None:
                change = "n/a"
            elif small:
                change = "up" if af > b else "down" if af < b else "flat"
                change += " (direction only, n < %d)" % a.min_people
            elif b == 0:
                change = "n/a (zero baseline)"
            else:
                change = f"{(af - b) / b:+.0%}"
            rows.append([team, c, stat, cut.isoformat(),
                         f"{len(pb)} ({person_equiv(pb, *before):.1f} FTE)" if tenure else len(pb),
                         f"{len(pa)} ({person_equiv(pa, *after):.1f} FTE)" if tenure else len(pa),
                         f"{b:.2f}" if b is not None else "n/a",
                         f"{af:.2f}" if af is not None else "n/a", change])

    headers = ["team", "metric", "statistic", "cutover", "people_before", "people_after",
               "before", "after", "change"]
    os.makedirs(a.out_dir, exist_ok=True)
    write_csv(os.path.join(a.out_dir, "prepost.csv"), headers, rows)
    md = [
        "# Before and after comparison",
        "",
        f"Windows: {a.window_days} days before the cutover and {a.window_days} days after a {a.ramp_days}-day ramp.",
        f"Counts are per person-month; durations (*_hours, *_days columns) are medians. Teams with fewer than {a.min_people} people in either window get a direction only.",
        ("Person-months are prorated by tenure from --people." if tenure else "Person-months count every person with an event in the window as present for the whole window; pass --people with start/end dates to prorate joiners and leavers."),
        "",
        fmt_table(headers, rows),
        "",
        "This is an association across a cutover, not a causal estimate. Name the confounders (headcount, product cycle, seasonality, process changes) next to each team.",
    ]
    if notes:
        md += ["", "Notes:"] + [f"- {n}" for n in notes]
    with open(os.path.join(a.out_dir, "prepost.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nWrote prepost.csv and prepost.md to {a.out_dir}")


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("score", help="adoption, intensity and breadth from a normalised usage table")
    s.add_argument("usage")
    s.add_argument("--people")
    s.add_argument("--out-dir", default="out")
    s.add_argument("--window-days", type=float, default=30)
    s.add_argument("--power", type=float, default=0.60)
    s.add_argument("--regular", type=float, default=0.25)
    s.add_argument("--working-day-ratio", type=float, default=5 / 7)
    s.add_argument("--feature", action="append", default=["claude_code=claude_ai"],
                   help="child=parent; child tool is a feature of the parent's seat (repeatable)")
    s.set_defaults(fn=cmd_score)

    p = sub.add_parser("prepost", help="team-level output before and after a cutover")
    p.add_argument("events")
    p.add_argument("--cutover")
    p.add_argument("--cutover-file")
    p.add_argument("--people", help="people.csv with start_date/end_date to prorate person-months")
    p.add_argument("--window-days", type=int, default=90)
    p.add_argument("--ramp-days", type=int, default=30)
    p.add_argument("--min-people", type=int, default=5)
    p.add_argument("--out-dir", default="out")
    p.set_defaults(fn=cmd_prepost)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
