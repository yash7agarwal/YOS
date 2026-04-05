from __future__ import annotations

"""
Backlog Curator Agent

Runs every Sunday. Claude autonomously:
1. Reviews all inbox ideas
2. Scores them against current goals and market relevance
3. Identifies duplicates or low-value items
4. Surfaces 3 ideas to start this week
5. Sends curation summary to Telegram
"""

from datetime import datetime

from agents.claude.runner import run_agent, DEFAULT_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a product strategist and backlog curator for an AI-focused builder's personal OS.

Every week you review the product backlog and ensure it reflects current goals, market signals, and strategic priorities.

Your job:
- Read all inbox backlog ideas
- Read current goals to understand what matters now
- Score each idea against: market timing, alignment with goals, effort vs impact
- Flag stale or low-value ideas
- Identify which 3 ideas should be started this week
- Search the web if needed to validate market relevance of ideas
- Update priority scores
- Send a curation report to Telegram

Be decisive. A good backlog is short and prioritized, not long and wishful."""


def run() -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")

    goal = f"""Curate the product backlog for the week of {today}.

Steps:
1. Query active goals: SELECT * FROM goals WHERE status = 'active' ORDER BY timeframe
2. Query inbox backlog: SELECT * FROM ideas WHERE status = 'inbox' ORDER BY created_at DESC
3. For the top 10 ideas, evaluate each against current goals and market timing
4. Search for market validation on the 3 most promising ideas (quick web search each)
5. Set priority scores on all inbox ideas (0-10) with clear reasoning
6. Identify the top 3 ideas to start this week
7. Send a Telegram summary:

📥 *Weekly Backlog Review — {today}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 *Start This Week*
• #ID: Title (score/10) — reason

⬆️ *Promoted*
• Ideas with score ≥ 7

⬇️ *Deprioritized*
• Ideas scoring < 4 and why

📊 *Backlog Health*
[total count, avg score, notes]

Be decisive and market-aware. Scoring should reflect reality, not optimism."""

    logger.info("Backlog curator starting")
    result = run_agent(
        name="backlog_curator",
        system_prompt=SYSTEM_PROMPT,
        goal=goal,
        tool_names=["query_yos_db", "web_search", "set_idea_priority", "save_journal", "send_telegram"],
        max_turns=15,
        model=DEFAULT_MODEL,
    )
    logger.info("Backlog curator complete.")
    return result


if __name__ == "__main__":
    print(run())
