from __future__ import annotations

import feedparser

from agents.base import run_agent
from utils.claude_client import ask

AGENT_NAME = "geo_intel"

FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.reuters.com/Reuters/worldNews",
]


def _fetch() -> str:
    headlines = []
    seen = set()

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()[:120]
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
    prompt = f"""You are an intelligence agent briefing a globally-aware product builder and founder on today's geopolitical landscape.

Today's world news:
{raw}

Extract the 4 most important geopolitical developments. Focus on:
- Developments that affect global tech supply chains, AI regulation, or market access
- Trade policy shifts, sanctions, or major diplomatic events
- Regional instability that could affect global business
- AI governance or data privacy legislation

Format each as a single bullet:
• [Region/Topic] — one sharp sentence on the development and why it matters to a builder

Return ONLY the 4 bullets, nothing else."""

    return ask(prompt, max_tokens=400)


def run() -> str:
    return run_agent(AGENT_NAME, _fetch, _synthesize)
