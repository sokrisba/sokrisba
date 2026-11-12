# Metric definitions and the reasoning behind them

Every number in the report should trace back to a definition on this page.
When a reader challenges a figure, the answer is "here is the definition and
here is the threshold", not "the script said so".

## Window

Default window is the last 30 full days ending on the latest date common to
all exports. Longer windows (90 days) smooth holidays and are better for the
output comparison; 30 days is better for a seat clean-up. State the window
and its end date on every table. Working days in the window are counted as
5/7 of calendar days unless the user gives a holiday calendar.

## Lens 1: Adoption

| Term | Definition |
|---|---|
| Seat holder | Person with a seat on the tool for the whole window (`seat = 1`). People who gained a seat mid-window are excluded from rates and listed as "new this window". |
| Active | At least one active day on the tool in the window. |
| Adoption rate | Active seat holders / seat holders, per tool and per team. |
| Dormant seat | Seat holder with zero active days in the window. |
| Reclaimable cost | Dormant seats x price per seat, annualised. Always show this as a range: dormant for 30 days might be holiday; dormant for 90 days is a decision. |
| Active without seat | Activity on a tool with `seat = 0`. Usually API keys or shared logins. Report as a separate line; it is a governance finding. |

Why "one active day" and not something stricter: the adoption lens answers
"is the seat used at all". Depth belongs to the intensity lens. Mixing the two
produces an adoption rate nobody can reproduce.

## Lens 2: Intensity

| Term | Definition |
|---|---|
| Active days | Days with any activity on the tool, from the vendor export. Where the export only has "last active", active days cannot be computed; mark the column as unavailable rather than inventing it. |
| Active-day share | Active days / working days in the window. |
| Sessions | The vendor's nearest unit of work: conversations (Claude.ai), messages (ChatGPT), requests (Cursor, APIs), Claude Code sessions. Never compare session counts across tools without saying the units differ. |
| Tokens | API products only. Input + output + cache tokens. Reported in millions. |
| Tokens per session | Tokens / requests, the simplest "token maxing" indicator. A person or key with very high tokens per session but few sessions is spending, not necessarily engaging. |
| Model mix | Share of tokens by model, for API products. Flag where the largest model dominates routine traffic. |

Intensity tiers, by active-day share on the person's most-used tool:

| Tier | Threshold | Reading |
|---|---|---|
| Power | at or above 60 percent of working days | Daily habit |
| Regular | at or above 25 percent | Weekly habit |
| Light | above 0 percent | Occasional |
| Dormant | 0 with a seat | Reclaim or train |

Why a share of working days and not raw counts: it makes a 30-day and a
90-day window comparable, and it stops part-time or newly started people from
being misread. Why the most-used tool and not the sum: active days across
tools overlap and cannot be de-duplicated from separate exports.

Thresholds are deliberately round. If the user wants different ones, change
the flags and state the new values; do not tune them to make a team look good.

## Lens 3: Breadth

| Term | Definition |
|---|---|
| Breadth | Number of distinct tools with at least one active day in the window. |
| Breadth distribution | Share of people at 0, 1, 2, 3+ tools, per team. |

Why breadth matters: a person on three tools is usually either exploring
(early rollout) or has found distinct jobs for each (mature use). A team
where everyone has one tool and it is the one they were given suggests the
rollout was a push, not a pull. Breadth also exposes overlap: paying for two
chat assistants per person is a consolidation candidate.

Count bundled tools (Gemini in Workspace) in breadth but not in cost. Count
Claude Code in breadth as its own tool, since it is a different way of
working, but never as a seat: it comes with the Claude.ai seat.

## Output measures (team level only)

These are not usage metrics. Keep them in a separate section of the report.

### Engineering

| Metric | Definition | Statistic |
|---|---|---|
| Throughput | Merged PRs per active author per month | Mean per person-month |
| Cycle time | Hours from PR opened to merged | Median (means are dominated by stale PRs) |
| AI-assisted share | PRs with an AI co-author trailer or label / all merged PRs | Share |

### RevOps

| Metric | Definition | Statistic |
|---|---|---|
| Pipeline created | Deals created per owner per month | Mean per person-month |
| Win rate | Won / (won + lost) in the window | Share |
| Days to close | Create date to close date for won deals | Median |
| AI-influenced deals | Deals with the agreed attribution property set | Count and share, only if the property exists |

### Before-and-after design

- Cutover per team: the first month in which at least half the team held a
  seat. Using a per-team date avoids comparing a team that got tools in March
  against one that got them in September.
- Equal windows on both sides, default 90 days, excluding the cutover month
  itself as a ramp.
- Compare like with like: throughput per person-month, not totals, so
  headcount changes do not masquerade as productivity.
- Minimum sample: five people in each window for a percentage; otherwise
  report direction only.
- Confounders to list by name: headcount changes, product launches or
  freezes, quarter-end effects, process changes (new review policy, new CRM
  stages), and tool changes unrelated to AI.
- Robustness checks, both cheap and both worth a line in the report:
  - Seasonality: look at the monthly series. If the before window holds a
    holiday month (December, August) re-base on the surrounding months and
    report the headline as a range. A same-season baseline (this November to
    December against last November to December) removes the problem outright
    when the history exists.
  - Staggered rollout: where seats arrived over several weeks, compare seated
    and not-yet-seated people within the same month. If both groups move
    together, the change is calendar-driven (a process or product change)
    rather than seat-driven, and the report must say so.
  - Also show the per-person direction count (how many of the people present
    in both windows moved the same way), without names.
- Weighting: say what share of the role the measured task covers. For an
  engineer, PR throughput is a large part; for a sales lead, deals created is
  a small part of a quarter dominated by a few late-stage conversations. The
  number must not be stretched beyond that share.

## What the method does not claim

- It does not measure quality of output.
- It does not attribute causation; it shows an association across a cutover.
- It does not rank individuals; per-person rows exist for seat
  administration only.
