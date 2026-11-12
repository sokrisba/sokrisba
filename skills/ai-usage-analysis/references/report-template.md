# Report structure

Use this order. The reader is a finance or operations leader who will forward
the document without reading the appendix, so the first page must stand on
its own. Every figure sits in a table; prose carries the interpretation.
Drop the sections that are out of scope for the request (see "Scope the
deliverable" in SKILL.md) and say so in one line of the summary; an empty
section headed "not covered" wastes the reader's first page.

```
# AI seat and usage review, <window start> to <window end>

## 1. Summary
Three to five sentences: seats held and annual cost, adoption rate overall,
reclaimable cost from dormant seats, the one output finding worth repeating,
and the main caveat.

## 2. Seat map
Table per tool: seats purchased, seats assigned, billing model, price per
seat or annual cost, admin, source and export date.
Table per team: seats by tool.

## 3. Adoption
Table per tool and per team: seat holders, active, adoption rate, dormant,
reclaimable annual cost (range), active without seat.
One paragraph on what stands out.

## 4. Intensity
Table per team: tier distribution (Power / Regular / Light / Dormant),
median active-day share, sessions with the unit named.
API products only: tokens (millions), tokens per session, model mix. One
paragraph on any token-maxing pattern.

## 5. Breadth
Table per team: share at 0, 1, 2, 3+ tools; most common tool pairs.
One paragraph on overlap and consolidation candidates.

## 6. Output next to input (team level)
Per team with a baseline: cutover date, window length, people in each
window, metric before, metric after, change, direction-only flag when n is
small. Engineering: throughput and cycle time. RevOps: pipeline created, win
rate, days to close, AI-influenced deals if the property exists.
One paragraph per team on what share of the role the metric covers.

## 7. Recommendations
Numbered. Each one names an owner and a date. Typical items: reclaim or
reassign dormant seats after confirming with managers, add an AI attribution
property to HubSpot deals, standardise API key naming so usage maps to
people, re-run in 90 days.

## 8. Limitations
The six caveats from SKILL.md, adapted to what was actually found, plus the
confounders named for each before-and-after comparison.

## Appendix A. Definitions
Window, working days, active, tiers and thresholds, session unit per tool.

## Appendix B. Data sources and export dates
One line per source with the date of the export and who supplied it.

## Appendix C. Per-person table
Restricted distribution. Only in the version sent to seat administrators.
```

Formatting rules:
- Currency with the code (USD 5,700), dates as YYYY-MM-DD.
- Percentages to the nearest whole number unless the base is under 20, then
  show the fraction (3 of 7).
- Never put a person's name next to a token count in sections 1 to 7.
