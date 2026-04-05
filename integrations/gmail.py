from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta

from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

GMAIL_DB = os.getenv("GMAIL_ORG_DB_PATH", "../GmailOrganization/learning/db/gmail_org.db")


def _conn() -> sqlite3.Connection | None:
    path = os.path.abspath(GMAIL_DB)
    if not os.path.exists(path):
        logger.warning(f"GmailOrg DB not found at {path}")
        return None
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_must_reads(limit: int = 5) -> list[dict]:
    """Return today's Must Read emails from GmailOrg classifications."""
    conn = _conn()
    if not conn:
        return []
    today = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        rows = conn.execute(
            """SELECT subject, sender, label FROM classifications
               WHERE priority_tier = 'Must Read' AND run_date = ?
               ORDER BY rowid DESC LIMIT ?""",
            (today, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Gmail must-reads query failed: {e}")
        return []
    finally:
        conn.close()


def get_recent_charges(hours: int = 24) -> list[dict]:
    """Return expenses logged in the last N hours."""
    conn = _conn()
    if not conn:
        return []
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d")
    try:
        rows = conn.execute(
            """SELECT merchant, amount, currency, date, description
               FROM expenses WHERE date >= ? ORDER BY date DESC LIMIT 10""",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Gmail charges query failed: {e}")
        return []
    finally:
        conn.close()


def get_upcoming_renewals(days: int = 7) -> list[dict]:
    """Return subscriptions renewing within N days."""
    conn = _conn()
    if not conn:
        return []
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cutoff = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        rows = conn.execute(
            """SELECT service, amount, currency, billing_cycle, renewal_date, status
               FROM subscriptions
               WHERE renewal_date BETWEEN ? AND ? AND status != 'expired'
               ORDER BY renewal_date ASC""",
            (today, cutoff),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Gmail renewals query failed: {e}")
        return []
    finally:
        conn.close()


def get_briefing_snippet() -> str:
    """Compose a compact inbox summary for inclusion in the daily briefing."""
    must_reads = get_must_reads(limit=5)
    charges = get_recent_charges(hours=24)
    renewals = get_upcoming_renewals(days=7)

    lines = []

    if must_reads:
        lines.append(f"📬 *Must Read ({len(must_reads)})*")
        for m in must_reads:
            subject = (m["subject"] or "")[:60]
            lines.append(f"  • {subject}")

    if charges:
        lines.append("💳 *Recent Charges*")
        for c in charges:
            amt = f"{c['currency']} {c['amount']:.2f}" if c.get("amount") else "—"
            lines.append(f"  • {c.get('merchant', '?')} — {amt}")

    if renewals:
        lines.append("🔔 *Upcoming Renewals*")
        for r in renewals:
            days_left = (
                datetime.strptime(r["renewal_date"], "%Y-%m-%d") - datetime.utcnow()
            ).days
            amt = f"{r['currency']} {r['amount']:.2f}" if r.get("amount") else ""
            lines.append(f"  ⚠️  {r['service']} in {days_left}d {amt}")

    return "\n".join(lines) if lines else ""
