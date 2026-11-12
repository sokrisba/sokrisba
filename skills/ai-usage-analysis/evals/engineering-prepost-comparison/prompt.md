---
tags: [ai-usage-analysis]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Can you do the "more with less" bit for engineering? I have merged_prs.csv (one row per merged PR with author, merge date and cycle time in hours, Nov 2025 to Aug 2026) and seat_grants.csv (when each engineer got their Claude Code seat). Compare throughput and cycle time before vs after the rollout and tell me what we can and can't claim from it. Note the column in merged_prs.csv is called merged_date, not date.

Input files: merged_prs.csv, seat_grants.csv
