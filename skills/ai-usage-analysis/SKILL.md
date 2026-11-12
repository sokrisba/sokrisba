---
name: ai-usage-analysis
description: Analyse who holds which AI seat or licence (Claude.ai, Claude Code, Anthropic Console API, ChatGPT, OpenAI API, Cursor, Copilot, Gemini, Midjourney, ElevenLabs and similar) and how much they actually use it, using a three-lens method (adoption, intensity, breadth) plus a separate team-level output measure (GitHub PRs and cycle time for engineering, HubSpot deals for RevOps) with a pre-AI baseline. Use this skill whenever someone asks about AI seats, AI licences, AI tool adoption or engagement, token usage or "token maxing", who uses Claude/ChatGPT/Cursor, dormant or unused AI seats, AI spend per user, AI ROI or productivity, or wants to compare output before and after AI rollout, even if they only say "usage report", "licence mapping" or "are we getting value from these tools".
---

# AI usage and engagement analysis

You are helping an operations or finance lead answer two questions that are
easy to conflate: *who has an AI seat and uses it* (an input question) and
*is the company getting more done because of it* (an output question). The
skill exists because the naive answer to both, "look at token counts", is wrong
in ways that embarrass the analyst in front of finance. Keep the two questions
separate in every table, chart and sentence you produce.

## The method in one paragraph

Measure **activity** from three angles and never from token counts alone.
**Adoption**: who holds a seat and has actually been active in the window.
**Intensity**: how often they use it, in active days and sessions, with tokens
only as a third, caveated signal where the product bills by token.
**Breadth**: how many distinct AI tools each person uses. Then, separately and
only at team level, put an **output measure** next to the activity picture,
using data that already has a pre-AI history: merged pull requests and cycle
time from GitHub for engineering, deals created, won and influenced from
HubSpot for RevOps. State plainly which part of a role those measures cover,
because stretching a narrow metric over a whole role is the second way to
embarrass yourself in front of finance.

## Why tokens alone mislead (say this in the report)

- Only API products (Anthropic Console, OpenAI Platform) bill by token. Seat
  products (Claude.ai Team/Enterprise, ChatGPT Team/Enterprise, Cursor,
  Copilot) report active days, messages or sessions, not tokens, so a
  token-only view silently drops most of the company.
- High token counts can come from running the largest model at high effort or
  long context on routine tasks. That is spend, not engagement. Call it
  "token maxing" if the reader uses that phrase, and report tokens per
  session alongside raw tokens so the reader can see it.
- Activity is an input. "More with less" needs an output next to it.

## Scope the deliverable to the question

Not every request is the full review. Match the output to what was asked:

- **Methodology only** ("explain how we'll measure it", "set expectations
  with finance before we pull numbers"): write a short note from the method
  paragraph above, the definitions in `references/metrics.md` and the caveats
  below. Do not run the workflow or invent figures. Spend figures from Notion
  may be quoted if dated ("USD 5,700 per year as recorded in Notion on
  2026-03-30"), otherwise leave them out.
- **Seat map and usage only**: steps 1 to 4 and report sections 1 to 5, 7, 8.
- **Output only** ("do the more-with-less bit", "before and after for
  engineering"): step 5 and report sections 1, 6, 7, 8. Say in one line that
  the usage lenses were not in scope; do not pad the report with empty
  sections.
- **Full review**: everything.

## Workflow

Work through these steps in order. Steps 1 to 3 build the seat map, 4 scores
it, 5 adds output, 6 writes it up. Skip a step only when the user has already
supplied its result or it is out of scope as above.

### 1. Establish the tool inventory and seat counts

Start from the systems of record rather than memory:

- **Notion "Third-Party Vendor List"** (data source
  `collection://218fe6fe-f1c3-814a-ae70-000b6382c5ce`): one page per tool with
  Price, Annual spend, License type, Admin(s), Team, Subscription type and the
  linked quarterly access-review ticket. Known AI entries include Claude ai
  (Anthropic, USD 5,700/yr, yearly), ChatGPT (OpenAI; notes say USD 5,000 is
  API and USD 3,900 is ChatGPT). Query it for anything AI-related rather than
  assuming the list is complete.
- **Vanta access systems** (`listAccessSystems`): lists Anthropic Console
  (API), Claude.ai, OpenAI (ChatGPT), OpenAI (API/Console), Cursor,
  Midjourney, ElevenLabs, Peec.ai. Vanta does not currently sync per-user
  accounts for these AI systems (the Anthropic integration returns zero
  accounts), so use Vanta for the inventory and risk tier, not for seat
  holders.
- **Vendor admin consoles** are the only reliable source of who holds a seat
  and what they did. They are not connected as tools, so ask the user for the
  exports named in `references/data-sources.md`, or work from the exports
  attached to the Notion access-review tickets.

Record per tool: seats purchased, seats assigned, price per seat or annual
cost, billing model (seat or token), and who the admin is.

### 2. Build the people and team dimension

Every per-person number must roll up to a team, because the output measure is
only meaningful at team level and because individual AI usage figures are
sensitive. Get the person to team mapping from, in order of preference: an HR
export the user provides (Rippling or Payfit), Vanta `listPersonnel`, or the
Google Workspace directory. Join on company email. Keep a column for start
date so new joiners are not read as dormant, and for leavers so their seats
show up as reclaimable.

### 3. Normalise the usage exports

Each vendor export has its own shape. Normalise everything into one long table
with one row per person per tool per window, using the schema in
`assets/usage_template.csv`:

```
person_email, team, tool, seat, active_days, sessions, tokens, window_days
```

`seat` is 1 if the person had a seat for the whole window. `tokens` is blank
for seat products. `sessions` means whatever the vendor's nearest concept is
(conversations, messages, Claude Code sessions, Cursor requests); say which in
the report. Claude Code is a feature of the Claude.ai seat, not a seat of its
own: give it its own `tool = claude_code` row so it shows in breadth and
intensity, and the script (via its default `--feature claude_code=claude_ai`)
will not count it as a second seat or a second dormant seat.
`references/data-sources.md` maps each vendor's export columns to this schema
and lists the gaps.

### 4. Score adoption, intensity and breadth

Run the bundled script rather than hand-computing, so thresholds are explicit
and repeatable:

```bash
python3 scripts/ai_usage.py score usage.csv --people people.csv --out-dir out/
```

It writes per-person, per-team and per-tool tables plus a markdown summary.
Definitions it applies (override with flags, and state them in the report):

- **Active** in the window: at least one active day on that tool.
- **Adoption rate** (per tool and per team): active seat holders divided by
  seat holders. Count people active without a seat separately; they are
  usually API key users or shared logins and are a finding on their own.
- **Intensity tier** from active days as a share of working days in the
  window: Power at or above 60 percent, Regular at or above 25 percent, Light
  above zero, Dormant at zero with a seat.
- **Breadth**: number of distinct tools with activity in the window.
- **Tokens**: reported only for token-billed tools, as raw tokens and tokens
  per session, never summed with seat products.

Read `references/metrics.md` before changing a definition. It explains why
each one is set the way it is and what the common objections are.

### 5. Add the output measure (team level, with a baseline)

Pick the team's natural output and pull its history from the system that
already has it:

- **Engineering, from GitHub**: pull requests merged per author per month and
  cycle time from PR opened to merged. Use the GitHub tools
  (`list_pull_requests`, `pull_request_read`) or a user-provided export.
- **RevOps, from HubSpot**: deals created, deals won, deal cycle length, and
  deals flagged as AI-powered or AI-influenced if such a property exists.
  Use `query_crm_data` for aggregates. Check `get_properties` on deals first
  for an AI-attribution field; if none exists, say so and propose one rather
  than inferring attribution.

Define a cutover date per team (the first month in which at least half the
team held a seat) and compare equal windows before and after with the script:

```bash
python3 scripts/ai_usage.py prepost events.csv --cutover 2026-03-01 --people people.csv --window-days 90 --out-dir out/
```

Report medians for cycle time, counts per person-month for throughput, and the
number of people in each window. Pass the people file so joiners and leavers
are prorated rather than counted as whole people. Then run the two cheap
robustness checks in `references/metrics.md` (seasonality in the before
window, and seated versus not-yet-seated people in the same month when the
rollout was staggered) and report the headline as a range if they move it. A team with fewer than five people in either
window gets a direction, not a percentage.

### 6. Write the report

Use the structure in `references/report-template.md`. The reader is a CFO or
COO who will forward it. Lead with the seat map and the dormant-seat money,
then adoption, intensity and breadth by team, then the output comparison, then
the caveats. Put every number in a table, not in prose.

## Caveats the report must carry

Include these in the Limitations section in your own words, adapted to what
you actually found. They are the points the finance reviewer will raise if
you do not:

1. Usage is an input. Nothing in the adoption, intensity or breadth tables
   proves productivity.
2. The output measure covers only part of each role. State roughly what share
   of the role's value the measured task represents, and do not extrapolate.
3. Before-and-after comparisons are confounded by headcount changes, product
   cycles, seasonality and anything else that changed at the same time. Name
   the confounders you know about.
4. Token figures exist only for API products and are inflated by model choice
   and effort settings.
5. Seat products report activity differently from each other. Say which
   "session" definition each column uses.
6. Individual-level usage is sensitive. Share per-person tables only with the
   people who manage seats, and keep the forwarded version at team level.

## Privacy and tone

Per-person rows are for the seat administrator, not for a company-wide post.
Do not rank individuals by token spend in the headline. When a seat is
dormant, present it as a reclaimable cost or a training gap, not as a
performance judgement, because the analyst does not know why it is dormant.

## Files in this skill

- `references/data-sources.md`: where each tool's seat list and usage export
  lives, which columns map to the normalised schema, and known gaps. Read it
  in step 1 and 3.
- `references/metrics.md`: full metric definitions, thresholds, and the
  reasoning behind them. Read it before changing a definition or when the
  user challenges one.
- `references/report-template.md`: the report structure. Read it in step 6.
- `scripts/ai_usage.py`: scoring (`score`) and before-and-after comparison
  (`prepost`). Run `python3 scripts/ai_usage.py --help`.
- `assets/usage_template.csv`, `assets/people_template.csv`,
  `assets/events_template.csv`: the input schemas with one example row each.
