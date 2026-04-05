from __future__ import annotations

import json
import feedparser

from agents.base import run_agent
from store.database import get_skills, get_latest_resume, add_job
from utils.claude_client import ask
from utils.logger import get_logger

AGENT_NAME = "career_scanner"
logger = get_logger(__name__)

FEEDS = [
    "https://hnrss.org/jobs",
    "https://remoteok.io/remote-jobs.rss",
    "https://weworkremotely.com/remote-jobs.rss",
]


def _build_profile() -> str:
    """Build a compact user profile from skills + latest resume."""
    skills = get_skills()
    resume = get_latest_resume()

    lines = []
    if resume:
        lines.append(f"Resume summary:\n{resume['content'][:800]}")
    if skills:
        by_cat: dict[str, list] = {}
        for s in skills:
            by_cat.setdefault(s["category"] or "General", []).append(f"{s['name']} ({s['level']})")
        lines.append("Skills: " + " | ".join(
            f"{cat}: {', '.join(names)}" for cat, names in by_cat.items()
        ))

    return "\n".join(lines) if lines else "AI/ML product builder with product management and software background."


def _fetch() -> str:
    listings = []
    seen = set()

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:25]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()[:200]
                link = entry.get("link", "")
                if title and title not in seen:
                    seen.add(title)
                    listings.append(f"TITLE: {title}\nSUMMARY: {summary}\nURL: {link}")
        except Exception as e:
            logger.warning(f"Feed {url} failed: {e}")

    return "\n\n---\n\n".join(listings[:30]) if listings else "No job listings fetched."


def _synthesize(raw: str) -> str:
    profile = _build_profile()

    prompt = f"""You are a career intelligence agent helping an AI-focused product builder find relevant job opportunities.

User profile:
{profile}

Job listings:
{raw[:4000]}

Identify the top 5 most relevant job opportunities for this person. For each job:
- Score fit from 0.0 to 1.0 based on alignment with their skills/background
- Extract: title, company (from listing), url, match_reason (one sentence)

Return ONLY valid JSON array:
[{{"title": "", "company": "", "url": "", "match_score": 0.8, "match_reason": "one sentence"}}]"""

    raw_response = ask(prompt, max_tokens=800)

    try:
        jobs = json.loads(raw_response.strip())
        saved = 0
        for job in jobs:
            try:
                add_job(
                    title=job.get("title", ""),
                    company=job.get("company", ""),
                    location="Remote",
                    url=job.get("url", ""),
                    source="career_scanner",
                    match_score=float(job.get("match_score", 0)),
                    match_reason=job.get("match_reason", ""),
                )
                saved += 1
            except Exception:
                pass

        summary_lines = [f"🎯 Top {len(jobs)} career matches saved:"]
        for j in jobs:
            score_pct = int(float(j.get("match_score", 0)) * 100)
            summary_lines.append(f"• {j.get('title', '?')} @ {j.get('company', '?')} — {score_pct}% match")
        return "\n".join(summary_lines)

    except (json.JSONDecodeError, ValueError):
        return "[career_scanner] Could not parse job matches."


def run() -> str:
    return run_agent(AGENT_NAME, _fetch, _synthesize)
