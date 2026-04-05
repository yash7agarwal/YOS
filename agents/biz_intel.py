from __future__ import annotations

import feedparser

from agents.base import run_agent
from utils.claude_client import ask

AGENT_NAME = "biz_intel"

FEEDS = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^IXIC&region=US&lang=en-US",
    "https://hnrss.org/newest?q=startup+OR+funding+OR+IPO+OR+acquisition",
]


def _fetch() -> str:
    headlines = []
    seen = set()

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()[:100]
                if title and title not in seen:
                    seen.add(title)
                    line = f"• {title}"
                    if summary:
                        line += f" — {summary}"
                    headlines.append(line)
        except Exception:
            continue

    return "\n".join(headlines[:25]) if headlines else "No headlines fetched."


def _synthesize(raw: str) -> str:
    prompt = f"""You are an intelligence agent briefing a founder and product builder on today's business and market landscape.

Today's business/financial news:
{raw}

Extract the 5 most important business signals. Focus on:
- Market moves that affect tech/AI startups
- Funding rounds or acquisitions in AI/SaaS
- Macro shifts relevant to a builder evaluating career and product opportunities
- Startup trends worth tracking

Format each as a single bullet:
• [Company/Topic] — one sharp sentence on the signal and why it matters

Return ONLY the 5 bullets, nothing else."""

    return ask(prompt, max_tokens=500)


def run() -> str:
    return run_agent(AGENT_NAME, _fetch, _synthesize)
