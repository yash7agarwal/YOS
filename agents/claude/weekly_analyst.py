from __future__ import annotations

"""
Weekly Deep Research Agent

Runs every Monday. Claude autonomously:
1. Reads current goals and backlog from YOS DB
2. Searches for the week's most important AI/tech/business developments
3. Identifies product opportunities and adds them to the backlog
4. Saves key learnings to the journal
5. Sends a weekly synthesis to Telegram
"""

from datetime import datetime

from agents.claude.runner import run_agent, DEEP_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a strategic research analyst embedded in an AI product builder's personal operating system (YOS).

Your job every week: deeply research what's happening in AI, technology, and business — then connect those signals to the user's current goals and product backlog.

You have tools to:
- Search the web for current developments
- Read the user's YOS database (goals, backlog, journal, skills)
- Add new ideas/opportunities to their backlog
- Save key learnings to their journal
- Send them a Telegram summary

Approach:
1. First, read the user's current goals and top backlog items to understand context
2. Search for 4-6 high-signal topics: new AI models/frameworks, product patterns, funding signals, regulatory shifts
3. For each major finding, decide: is this a product opportunity? a learning? a threat to track?
4. Add 2-3 high-quality opportunities to the backlog with good descriptions
5. Save 3-5 learnings to the journal
6. Send a crisp weekly synthesis via Telegram

Be selective — surface what actually matters for someone building AI products. Quality over quantity."""


def run() -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    week = datetime.utcnow().strftime("Week %W, %Y")

    goal = f"""Conduct the weekly deep research for {week} (today: {today}).

Steps:
1. Query YOS DB for active goals and top 10 backlog items to understand current focus
2. Search for: "AI product developments this week", "new LLM releases", "AI startup funding", "AI regulation news"
3. Fetch 2-3 articles that look most relevant
4. Identify opportunities worth adding to the backlog
5. Save key learnings to journal
6. Send a Telegram message with the weekly synthesis formatted as:

📊 *Weekly Intelligence — {week}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔑 *Top 5 Signals*
• ...

💡 *Backlog Additions* (N new ideas)
• ...

📚 *Key Learnings*
• ...

Be thorough but focused. Prioritize signal over noise."""

    logger.info(f"Weekly analyst starting for {week}")
    result = run_agent(
        name="weekly_analyst",
        system_prompt=SYSTEM_PROMPT,
        goal=goal,
        tool_names=["web_search", "fetch_url", "query_yos_db", "add_idea", "save_journal", "send_telegram"],
        max_turns=20,
        model=DEEP_MODEL,
    )
    logger.info("Weekly analyst complete.")
    return result


if __name__ == "__main__":
    print(run())
