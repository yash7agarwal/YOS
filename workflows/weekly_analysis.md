# Workflow: Weekly Intelligence Analysis

## Objective
Run a deep-research Claude agent every Monday to synthesize patterns from the past week, surface backlog insights, and send a structured weekly digest to Telegram.

## Inputs
- `agent_runs` table (last 7 days of briefings)
- `ideas` table (inbox backlog items)
- `goals` table (active goals, progress)
- `journal` table (last 7 days of notes)
- Web search via Claude tool-use loop

## Outputs
- Saved `agent_runs` row for `weekly_analyst`
- Telegram message with weekly digest
- Possible auto-prioritization of backlog ideas

## Tools Used
- `agents/claude/weekly_analyst.py` — multi-turn Opus tool-use agent
- `agents/claude/runner.py` — generic tool-use loop
- `agents/claude/tools.py` — web_search, query_yos_db, add_idea, send_telegram

## Steps

1. **Gather context**
   - Query last 7 days of agent summaries from `agent_runs`
   - Query active goals with progress < 50%
   - Query journal entries from last 7 days
   - Query inbox backlog items (status='inbox')

2. **Run weekly analyst agent** (claude-opus-4-6, multi-turn)
   - Goal: "Analyze this week's intelligence. What patterns emerged? What should be prioritized? What should be dropped from backlog?"
   - Agent can call web_search for context enrichment
   - Agent can call query_yos_db for additional data
   - Agent produces structured markdown output

3. **Send digest**
   - Agent calls send_telegram with the digest
   - Save agent run to DB

## Edge Cases
- If fewer than 3 agent runs in last 7 days: note the gap, still run analysis on what exists
- If Opus API unavailable: fall back to Sonnet with reduced scope

## Quality Bar
- Analysis references specific items from the week (not generic)
- At least one actionable recommendation produced
- Completes within 15 agent turns

## Trigger
- `scheduler/weekly.py` → APScheduler CronTrigger(day_of_week='mon', hour=8, minute=15)
- Manual: `python3 -m scheduler.main --weekly`
