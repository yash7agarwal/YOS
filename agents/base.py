from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from store.database import save_agent_run
from utils.logger import get_logger

logger = get_logger(__name__)


def run_agent(
    name: str,
    fetch_fn: Callable[[], str],
    synthesize_fn: Callable[[str], str],
) -> str:
    """
    Standard agent runner. Fetches raw content, synthesizes with Claude,
    saves to agent_runs table, returns summary string.
    """
    start = time.time()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        raw = fetch_fn()
        summary = synthesize_fn(raw)
        duration_ms = int((time.time() - start) * 1000)
        item_count = len([l for l in raw.splitlines() if l.strip()])
        save_agent_run(today, name, raw, summary, item_count, "ok", duration_ms)
        logger.info(f"Agent [{name}] OK — {duration_ms}ms, {item_count} items")
        return summary

    except Exception as exc:
        duration_ms = int((time.time() - start) * 1000)
        save_agent_run(today, name, str(exc), "", 0, "error", duration_ms)
        logger.error(f"Agent [{name}] FAILED: {exc}")
        return f"[{name} unavailable today]"
