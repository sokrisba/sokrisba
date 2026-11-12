# Data sources for AI usage analysis

What exists, where it lives, what it can and cannot tell you. Verified against
the connected tools on 2026-11-12; re-check the tool list before assuming a
connector is or is not available.

## 1. Seat inventory (who is entitled to what)

| Source | What it gives | Access | Gaps |
|---|---|---|---|
| Notion "Third-Party Vendor List" (`collection://218fe6fe-f1c3-814a-ae70-000b6382c5ce`) | One page per tool: Vendor Name, Tool Name, Price, Annual spend (formula), Currency, Subscription type, License type, Admin(s), Team, Access type, linked quarterly access-review ticket, renewal date | Notion connector (`notion-query-data-sources`, `notion-fetch`) | No per-user seat list on the page itself. Seat counts may be in the access-review ticket or the "attached exports of user access". Prices may be out of date; confirm against the latest invoice. |
| Vanta access systems (`listAccessSystems`) | Inventory of SaaS systems with risk tier and owner. AI entries seen: Anthropic Console (API), Claude.ai (Anthropic Web Interface), OpenAI (ChatGPT), OpenAI (API/Console), Cursor, Midjourney, ElevenLabs, Peec.ai | Vanta connector | `listAccessAccounts` returns no accounts for these AI systems (checked for `anthropic`). Use Vanta for the inventory, not for seat holders. |
| Vanta quarterly access-review tickets (linked from Notion, e.g. "Claude + Console - quarterly access review (October, 2025)", "Open AI - quarterly access review (February, 2026)") | Point-in-time list of users per system, with approve/revoke decisions | Notion page fetch | A snapshot, not continuous. Good for seat holders at that date. |
| Vendor admin consoles (below) | Authoritative current seat list | Not connected; ask the user for an export | None, this is the source of truth. |

Always reconcile the three. A seat in the admin console that is missing from
Notion or the last access review is a compliance finding as well as a cost one.

## 2. Usage exports per vendor

None of these consoles are connected as tools. Ask the user for the export,
name the exact screen, and tell them which columns you need. Column names
drift between vendor releases; match on meaning, not exact header text.

### Claude.ai Team / Enterprise (seat product)

- Where: Admin settings, Analytics (Enterprise) or Members list (Team).
  Enterprise admins can export member activity as CSV; Team plans show
  members with last-active date.
- Columns to map: email, role, last active, active days (where present),
  messages or conversations in period, Claude Code sessions and lines of code
  accepted (Enterprise analytics shows Claude Code separately).
- Normalise: `tool = claude_ai`, `sessions = conversations` (or messages if
  that is all there is; say which), `tokens` blank.
- Claude Code: treat as a separate `tool = claude_code` row when the export
  breaks it out, because engineering adoption usually hides there. It shares
  the Claude.ai seat, so leave the script's default feature mapping in place
  and it will not be counted as a second seat.

### Anthropic Console (API, token-billed)

- Where: Console, Usage and Cost pages, grouped by workspace and API key.
  Export CSV.
- Columns to map: workspace, API key name, model, input tokens, output
  tokens, cache read/write tokens, requests, cost.
- Attribution: API keys belong to workspaces or services, not people. Map a
  key to a person only when the key name or the Notion access review says
  who owns it; otherwise book it to the team or service and say so.
- Normalise: `tool = anthropic_api`, `sessions = requests`, `tokens = input +
  output + cache tokens`, and keep a side table of model mix so "token
  maxing" (large model, high effort, routine task) is visible.

### ChatGPT Team / Enterprise (seat product)

- Where: Workspace settings, Members (Team) or Analytics / Compliance API
  (Enterprise). Team plans show last active per member; Enterprise shows
  active users, messages, GPT usage over time.
- Columns to map: email, status, last active, messages in period, active days
  if present.
- Normalise: `tool = chatgpt`, `sessions = messages` (state this), `tokens`
  blank.

### OpenAI Platform (API, token-billed)

- Where: Platform, Usage, grouped by project and API key. Export CSV.
- Same attribution rule as Anthropic Console: keys map to projects, not
  people, unless named.
- Normalise: `tool = openai_api`, `sessions = requests`, `tokens` summed.

### Cursor (seat product)

- Where: Team dashboard, Usage / Members, export CSV. Shows per-member
  requests, active days, model usage, and tab completions.
- Normalise: `tool = cursor`, `sessions = requests`, `active_days` from the
  export. Cursor reports its own token-equivalent "usage" for some plans;
  do not add that to API tokens.

### GitHub Copilot (seat product, if licensed)

- Where: Organisation settings, Copilot, Usage metrics, or the Copilot
  metrics API. Shows active users, suggestions shown and accepted, chat
  turns.
- Normalise: `tool = copilot`, `sessions = chat turns + accepted suggestions`
  (say which), `active_days` from daily metrics.

### Gemini in Google Workspace (bundled)

- Where: Admin console, Reports, Apps, Gemini. Shows active users per app.
- Often bundled into the Workspace plan, so there is no seat cost to reclaim,
  but it counts towards breadth.

### Midjourney, ElevenLabs, Peec.ai and other niche tools

- Usually a shared login or a single admin; treat as a team tool with one
  row per actual user if the console shows them, otherwise book to the team.

## 3. People and teams

| Source | Use | Notes |
|---|---|---|
| HR export (Rippling for US, Payfit for non-US) | Email, name, team or department, manager, start date, end date | Not connected; ask the user. Best source for team. |
| Vanta `listPersonnel` | Personnel records with email and status, sometimes group | Connected. Groups may be security groups rather than org teams. |
| Google Workspace directory | Email, org unit, title | Only if the Google Admin connector exists; otherwise ask. |

Join everything on lowercase company email. People with a seat but no HR
record are usually contractors or leavers; list them separately.

## 4. Output measures

### Engineering, GitHub

- Tools: `list_pull_requests` (state merged, sorted by updated), then
  `pull_request_read` for created and merged timestamps, author, and
  additions. Scope is whatever repositories the session's GitHub access
  covers; if the org repositories are not attached, ask for them or for a
  PR export.
- Metrics: PRs merged per author per month; cycle time (hours from opened to
  merged, median); review turnaround if review events are available.
- Attribution to AI: PR bodies or commit trailers generated by AI tools
  (for example a Claude Code co-author trailer) let you tag AI-assisted PRs.
  Report the tagged share, but do not treat untagged PRs as AI-free.

### RevOps, HubSpot

- Tools: `get_properties` on deals first, to look for an AI-attribution
  property (anything named like "AI assisted", "AI influenced",
  "Sequence/Agent generated"). Then `query_crm_data` for aggregates by owner
  and month: deals created, deals won, amount, days to close.
- If no attribution property exists, say so in the report and recommend one.
  Do not infer AI influence from notes or activity type.
- Owners map to people by HubSpot owner email (`search_owners`).

## 5. Known gaps to state in every report

- No connected source gives per-person AI usage directly; everything
  depends on vendor exports the user supplies, so date the exports.
- Vanta's per-user account sync does not cover the AI systems.
- API usage attaches to keys and workspaces, not people.
- Notion prices may be stale; the Annual spend formula is only as good as
  the Price field.
