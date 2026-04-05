from __future__ import annotations

import os
import sqlite3
import textwrap
from datetime import datetime
from urllib.parse import quote_plus

import feedparser
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from store.database import (
    add_idea, add_journal_entry, update_idea_priority, get_conn,
)
from utils.telegram import send_message
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

DB_PATH = os.getenv("DB_PATH", "db/yos.db")


# ── Tool Implementations ────────────────────────────────────────────────────

def web_search(query: str, max_results: int = 8) -> str:
    """Search Google News RSS + DuckDuckGo for recent results."""
    results = []

    # Google News RSS
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "").strip()[:200]
            link = entry.get("link", "")
            results.append(f"• {title}\n  {summary}\n  {link}")
    except Exception as e:
        logger.warning(f"Google News search failed: {e}")

    # DuckDuckGo instant answers as fallback
    if not results:
        try:
            r = httpx.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1"},
                timeout=8,
            )
            data = r.json()
            if data.get("Abstract"):
                results.append(f"Summary: {data['Abstract']}")
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"• {topic['Text']}")
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")

    return "\n\n".join(results[:max_results]) if results else "No results found."


def fetch_url(url: str, max_chars: int = 3000) -> str:
    """Fetch a URL and return cleaned text content."""
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (compatible; YOS/1.0)"})
        soup = BeautifulSoup(r.text, "html.parser")
        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text[:max_chars]
    except Exception as e:
        return f"[fetch_url error: {e}]"


def query_yos_db(sql: str) -> str:
    """Run a read-only SELECT query against the YOS database."""
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT"):
        return "Error: only SELECT queries are allowed."
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchall()
        conn.close()
        if not rows:
            return "No results."
        headers = rows[0].keys()
        lines = [" | ".join(headers)]
        lines += [" | ".join(str(r[h]) for h in headers) for r in rows[:20]]
        return "\n".join(lines)
    except Exception as e:
        return f"[query_yos_db error: {e}]"


def tool_add_idea(title: str, description: str = "", tags: str = "") -> str:
    """Add a new idea to the product backlog."""
    idea_id = add_idea(title=title, description=description, tags=tags, source="claude_agent")
    return f"Idea #{idea_id} added to backlog: {title}"


def tool_save_journal(content: str, category: str = "learning") -> str:
    """Save a research finding or insight to the journal."""
    valid = {"moment", "win", "learning", "idea", "reflection", "insight"}
    if category not in valid:
        category = "learning"
    entry_id = add_journal_entry(content=content, category=category)
    return f"Journal entry #{entry_id} saved."


def tool_send_telegram(message: str) -> str:
    """Send a message to the user via Telegram."""
    ok = send_message(message)
    return "Sent." if ok else "Failed to send."


def tool_set_idea_priority(idea_id: int, score: float, reason: str) -> str:
    """Update the priority score of a backlog idea."""
    update_idea_priority(idea_id, min(10.0, max(0.0, score)), reason)
    return f"Idea #{idea_id} priority set to {score}."


# ── Tool dispatch ────────────────────────────────────────────────────────────

TOOL_MAP = {
    "web_search": lambda inp: web_search(inp["query"], inp.get("max_results", 8)),
    "fetch_url": lambda inp: fetch_url(inp["url"]),
    "query_yos_db": lambda inp: query_yos_db(inp["sql"]),
    "add_idea": lambda inp: tool_add_idea(inp["title"], inp.get("description", ""), inp.get("tags", "")),
    "save_journal": lambda inp: tool_save_journal(inp["content"], inp.get("category", "learning")),
    "send_telegram": lambda inp: tool_send_telegram(inp["message"]),
    "set_idea_priority": lambda inp: tool_set_idea_priority(inp["idea_id"], inp["score"], inp["reason"]),
}


def execute_tool(name: str, inputs: dict) -> str:
    fn = TOOL_MAP.get(name)
    if not fn:
        return f"[Unknown tool: {name}]"
    try:
        return str(fn(inputs))
    except Exception as e:
        logger.error(f"Tool {name} error: {e}")
        return f"[{name} error: {e}]"


# ── Anthropic tool schemas ───────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": "Search Google News and DuckDuckGo for recent information on any topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default 8)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": "Fetch and read the text content of a URL.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "query_yos_db",
        "description": "Run a SELECT query on the YOS SQLite database. Tables: ideas, goals, journal, health_logs, job_listings, skills, agent_runs, briefings.",
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "SELECT query only"}},
            "required": ["sql"],
        },
    },
    {
        "name": "add_idea",
        "description": "Add a new idea or opportunity to the product backlog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "tags": {"type": "string"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "save_journal",
        "description": "Save a research finding, insight, or learning to the journal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": ["learning", "insight", "win", "reflection", "moment"],
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "set_idea_priority",
        "description": "Set the priority score (0-10) of a backlog idea.",
        "input_schema": {
            "type": "object",
            "properties": {
                "idea_id": {"type": "integer"},
                "score": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": ["idea_id", "score", "reason"],
        },
    },
    {
        "name": "send_telegram",
        "description": "Send a message to the user via Telegram.",
        "input_schema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    },
]
