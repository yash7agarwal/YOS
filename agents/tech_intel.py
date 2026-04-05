from __future__ import annotations

import feedparser
import httpx

from agents.base import run_agent
from utils.claude_client import ask

AGENT_NAME = "tech_intel"

# HN front page RSS + AI/ML news
FEEDS = [
    "https://hnrss.org/frontpage",
    "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+Claude+OR+agent",
]


def _fetch() -> str:
    headlines = []
    seen = set()

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                if title and title not in seen:
                    seen.add(title)
                    headlines.append(f"• {title} ({link})")
        except Exception:
            continue

    return "\n".join(headlines[:30]) if headlines else "No headlines fetched."


def _synthesize(raw: str) -> str:
    prompt = f"""You are an intelligence agent briefing an AI product builder and builder who is deeply invested in the AI ecosystem.

Today's Hacker News + AI news feed:
{raw}

Extract the 6 most signal-rich items. Focus on:
- New AI models, tools, or frameworks released
- Significant product launches or pivots
- Research breakthroughs worth knowing
- Developer workflow changes or new patterns
- Anything an AI-focused product manager should act on

Format each as a single bullet:
• [Tool/Topic] — one sharp sentence on why it matters

Return ONLY the 6 bullets, nothing else."""

    return ask(prompt, max_tokens=600)


def run() -> str:
    return run_agent(AGENT_NAME, _fetch, _synthesize)
