"""
tools/feeds.py — RSS feed ingestion tool

Deterministic RSS/Atom feed fetcher using feedparser.
Returns normalized list of {title, summary, url, published} dicts.
"""
from __future__ import annotations

import feedparser
from utils.logger import get_logger

logger = get_logger(__name__)


def fetch_feed(url: str, max_entries: int = 10) -> list[dict]:
    """Fetch and normalize an RSS/Atom feed."""
    try:
        feed = feedparser.parse(url)
        entries = []
        for e in feed.entries[:max_entries]:
            entries.append({
                "title": e.get("title", "").strip(),
                "summary": e.get("summary", e.get("description", ""))[:300].strip(),
                "url": e.get("link", ""),
                "published": e.get("published", ""),
            })
        return entries
    except Exception as exc:
        logger.warning("feed fetch failed url=%s error=%s", url, exc)
        return []


def fetch_feeds(urls: list[str], max_per_feed: int = 5) -> list[dict]:
    """Fetch multiple feeds and merge results."""
    results = []
    for url in urls:
        results.extend(fetch_feed(url, max_per_feed))
    return results


def format_for_prompt(entries: list[dict], max_chars: int = 200) -> str:
    """Format feed entries as a compact string for Claude prompt context."""
    lines = []
    for e in entries:
        title = e["title"]
        summary = e["summary"][:max_chars] if e["summary"] else ""
        lines.append(f"• {title}" + (f" — {summary}" if summary else ""))
    return "\n".join(lines)
