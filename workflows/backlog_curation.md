# Workflow: Backlog Curation

## Objective
Prioritize the ideas backlog using Claude AI scoring — assign a 0–10 priority score with justification to each unscored idea.

## Inputs
- `ideas` table rows where `priority_score = 0` or triggered by `/prioritize <id>`
- User profile from `memory/user_context.md` (goals, current focus)

## Outputs
- Updated `priority_score` and `priority_reason` in `ideas` table
- Telegram confirmation message

## Tools Used
- `utils/claude_client.py:ask()` (Sonnet — simple scoring, no tool-use needed)
- `store/database.py:update_idea_priority()`
- `utils/telegram.py:send_message()`

## Steps

1. **Fetch unscored ideas**
   - `get_backlog(status='inbox')` filtered where `priority_score == 0`

2. **Score each idea** (single Claude call per idea or batch)
   - Prompt: "Given this person's current focus [context], score this idea 0–10 for priority and explain in one sentence."
   - Parse JSON response: `{"score": 7.5, "reason": "..."}`

3. **Update DB**
   - `conn.execute("UPDATE ideas SET priority_score=?, priority_reason=?, updated_at=? WHERE id=?", ...)`

4. **Confirm**
   - Reply via Telegram: "Scored: [title] → 7.5/10 — [reason]"

## Edge Cases
- If Claude returns malformed JSON: re-try once; if still fails, set score to 5.0 with reason "Auto-score failed"
- If idea text is too short (<10 chars): skip and reply "Idea too brief to score"

## Quality Bar
- Score reflects actual user priorities, not generic "this is cool" reasoning
- Reason is one sentence, specific to the idea

## Trigger
- `/prioritize <id>` Telegram command
- `agents/claude/backlog_curator.py` weekly curation pass
