from __future__ import annotations

"""
Monthly OS Report Agent

Runs on the 1st of each month. Claude autonomously:
1. Reviews all goals, journal entries, health logs, and intel from the past month
2. Identifies patterns in productivity, focus areas, and blind spots
3. Assesses career trajectory vs market trends
4. Suggests next month's priorities and backlog re-ordering
5. Sends a comprehensive monthly report to Telegram
"""

from datetime import datetime, timedelta

from agents.claude.runner import run_agent, DEEP_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the monthly OS analyst for a personal AI operating system (YOS).

Once a month, you perform a comprehensive review of the user's operating data — goals, journal, health, career — and generate a strategic monthly report.

Your analysis covers:
- Goal completion rates and patterns
- What the user actually spent time on (from journal)
- Health trends and gaps
- Career progression signals
- Alignment between stated goals and actual activity
- What the market is doing vs what the user is focused on

You then:
- Identify 3-5 key insights from the month
- Flag any concerning patterns (goal drift, health neglect, missed opportunities)
- Suggest next month's top 3 priorities
- Re-prioritize the backlog based on learnings
- Send a comprehensive monthly report via Telegram

Be honest and direct. The user wants signal, not affirmation."""


def run() -> str:
    now = datetime.utcnow()
    last_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1).strftime("%Y-%m-%d")
    last_month_end = now.replace(day=1).strftime("%Y-%m-%d")
    month_name = (now.replace(day=1) - timedelta(days=1)).strftime("%B %Y")

    goal = f"""Generate the monthly OS report for {month_name}.

Steps:
1. Query goals: SELECT * FROM goals WHERE created_at >= '{last_month_start}' OR status != 'archived'
2. Query journal entries from last month: SELECT * FROM journal WHERE entry_date >= '{last_month_start}' AND entry_date < '{last_month_end}' ORDER BY created_at DESC LIMIT 50
3. Query health logs: SELECT * FROM health_logs WHERE log_date >= '{last_month_start}' ORDER BY log_date DESC
4. Query agent runs to see what intel was generated: SELECT agent, COUNT(*) as runs, MAX(run_date) as last_run FROM agent_runs WHERE run_date >= '{last_month_start}' GROUP BY agent
5. Query top backlog items: SELECT * FROM ideas WHERE status IN ('inbox','in_progress') ORDER BY priority_score DESC LIMIT 15
6. Search for: "AI industry trends {month_name}" to contextualize against market
7. Based on all findings, compose and send a monthly report via Telegram:

📅 *Monthly OS Report — {month_name}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 *Goal Summary*
[completion rates, patterns]

💭 *Activity Patterns*
[what journal shows about actual focus]

🩺 *Health Snapshot*
[trends, gaps]

🔍 *Key Insights*
[3-5 honest observations]

⚡ *Next Month Priorities*
[top 3 recommendations]

📥 *Backlog Recommendations*
[what to prioritize, drop, or add]

8. Set priority scores on top 5 backlog ideas based on your analysis

Be analytical and honest. Surface what the data actually shows."""

    logger.info(f"Monthly reporter starting for {month_name}")
    result = run_agent(
        name="monthly_reporter",
        system_prompt=SYSTEM_PROMPT,
        goal=goal,
        tool_names=["query_yos_db", "web_search", "save_journal", "set_idea_priority", "send_telegram"],
        max_turns=20,
        model=DEEP_MODEL,
    )
    logger.info("Monthly reporter complete.")
    return result


if __name__ == "__main__":
    print(run())
