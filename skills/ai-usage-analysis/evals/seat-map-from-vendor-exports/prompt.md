---
tags: [ai-usage-analysis]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I'm mapping who has which AI seat and whether they actually use it. I've pulled the exports for the last 30 days (ending 2026-11-11): Claude Team members, ChatGPT workspace members, Cursor team usage, Anthropic Console usage by API key, an HR export for teams, and an excerpt of our vendor list with seat counts and prices. Build me the seat map and an adoption / intensity / breadth view by team, flag dormant seats with the cost we could reclaim, and write it up as a short report I can send to our finance lead. Please don't just rank people by tokens, he already said that's not a reliable measure.

Input files: hr_export.csv, claude_team_members.csv, chatgpt_workspace_members.csv, cursor_team_usage.csv, anthropic_console_usage.csv, vendor_list_excerpt.csv
