from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "db/yos.db")


def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
        -- ── IDEAS & BACKLOG ─────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS ideas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            description     TEXT,
            source          TEXT DEFAULT 'telegram',
            status          TEXT DEFAULT 'inbox',
            priority_score  REAL DEFAULT 0.0,
            priority_reason TEXT,
            tags            TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        -- ── GOALS ───────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS goals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            timeframe   TEXT NOT NULL,
            quarter     TEXT,
            status      TEXT DEFAULT 'active',
            progress    INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS checkins (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            checkin_date    TEXT NOT NULL,
            type            TEXT NOT NULL,
            notes           TEXT,
            goals_reviewed  TEXT,
            mood            TEXT,
            created_at      TEXT NOT NULL
        );

        -- ── JOURNAL ─────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS journal (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date  TEXT NOT NULL,
            content     TEXT NOT NULL,
            tags        TEXT,
            category    TEXT DEFAULT 'moment',
            created_at  TEXT NOT NULL
        );

        -- ── HEALTH ──────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS health_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date    TEXT NOT NULL,
            sleep_hours REAL,
            exercise    TEXT,
            diet_notes  TEXT,
            energy      INTEGER,
            stress      INTEGER,
            notes       TEXT,
            created_at  TEXT NOT NULL
        );

        -- ── CAREER ──────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS job_listings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            company         TEXT NOT NULL,
            location        TEXT,
            url             TEXT,
            source          TEXT,
            match_score     REAL,
            match_reason    TEXT,
            status          TEXT DEFAULT 'new',
            found_at        TEXT NOT NULL,
            expires_at      TEXT
        );

        CREATE TABLE IF NOT EXISTS resume_versions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            version     INTEGER NOT NULL,
            content     TEXT NOT NULL,
            change_log  TEXT,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS skills (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            category    TEXT,
            level       TEXT DEFAULT 'learning',
            evidence    TEXT,
            added_at    TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        -- ── INTELLIGENCE ─────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS agent_runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date    TEXT NOT NULL,
            agent       TEXT NOT NULL,
            raw_output  TEXT,
            summary     TEXT,
            item_count  INTEGER DEFAULT 0,
            status      TEXT DEFAULT 'ok',
            duration_ms INTEGER,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS briefings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL UNIQUE,
            content     TEXT NOT NULL,
            sent_at     TEXT,
            created_at  TEXT NOT NULL
        );

        -- ── BOT INTERACTIONS ─────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS bot_interactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT NOT NULL,
            type            TEXT NOT NULL,
            input_text      TEXT,
            command_name    TEXT,
            status          TEXT NOT NULL,
            error_message   TEXT,
            response_sent   INTEGER DEFAULT 0
        );

        -- ── EVALUATIONS (AOS compounding loop) ──────────────────────
        CREATE TABLE IF NOT EXISTS evaluations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            agent           TEXT NOT NULL,
            goal            TEXT,
            correctness     INTEGER NOT NULL,
            efficiency      INTEGER NOT NULL,
            reusability     INTEGER NOT NULL,
            clarity         INTEGER NOT NULL,
            notes           TEXT,
            evaluated_at    TEXT NOT NULL
        );

        -- ── INDEXES ──────────────────────────────────────────────────
        CREATE INDEX IF NOT EXISTS idx_ideas_status    ON ideas (status, priority_score DESC);
        CREATE INDEX IF NOT EXISTS idx_journal_date    ON journal (entry_date DESC);
        CREATE INDEX IF NOT EXISTS idx_goals_timeframe ON goals (timeframe, status);
        CREATE INDEX IF NOT EXISTS idx_jobs_status     ON job_listings (status, match_score DESC);
        CREATE INDEX IF NOT EXISTS idx_agent_runs_date ON agent_runs (run_date, agent);
        CREATE INDEX IF NOT EXISTS idx_health_date     ON health_logs (log_date DESC);
        CREATE INDEX IF NOT EXISTS idx_briefings_date  ON briefings (date DESC);
        CREATE INDEX IF NOT EXISTS idx_evals_agent     ON evaluations (agent, evaluated_at DESC);

        -- ── PRODUCT OS ───────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS idea_clusters (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT,
            idea_ids    TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prds (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id      INTEGER,
            title           TEXT NOT NULL,
            status          TEXT DEFAULT 'draft',
            overview        TEXT,
            problem         TEXT,
            goals           TEXT,
            non_goals       TEXT,
            user_stories    TEXT,
            requirements    TEXT,
            success_metrics TEXT,
            open_questions  TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prd_comments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            prd_id      INTEGER NOT NULL,
            author      TEXT DEFAULT 'user',
            type        TEXT DEFAULT 'comment',
            content     TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_prds_cluster   ON prds (cluster_id, status);
        CREATE INDEX IF NOT EXISTS idx_prd_comments   ON prd_comments (prd_id, created_at);

        -- ── DOMAIN AGENT STATE ───────────────────────────────────────
        CREATE TABLE IF NOT EXISTS user_agent_state (
            id             INTEGER PRIMARY KEY DEFAULT 1,
            agent_name     TEXT NOT NULL DEFAULT 'product',
            conversation   TEXT NOT NULL DEFAULT '[]',
            active_project TEXT NOT NULL DEFAULT 'jobs-os',
            updated_at     TEXT NOT NULL
        );

        -- ── PROJECT-SCOPED CONVERSATIONS ────────────────────────────
        -- One thread per project. Switching projects swaps the thread;
        -- switching agents within the same project preserves it.
        CREATE TABLE IF NOT EXISTS project_conversations (
            project      TEXT PRIMARY KEY,
            conversation TEXT NOT NULL DEFAULT '[]',
            updated_at   TEXT NOT NULL
        );
        """)

        # Idempotent column add for older DBs that pre-date active_project.
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(user_agent_state)").fetchall()}
        if "active_project" not in cols:
            conn.execute(
                "ALTER TABLE user_agent_state ADD COLUMN active_project TEXT NOT NULL DEFAULT 'jobs-os'"
            )

    print(f"YOS database initialized at {DB_PATH}")


# ── IDEAS ─────────────────────────────────────────────────────────────────────

def add_idea(title: str, description: str = "", tags: str = "", source: str = "telegram") -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO ideas (title, description, tags, source, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (title, description, tags, source, now, now),
        )
        return cur.lastrowid


def get_backlog(status: str = "inbox", limit: int = 10) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM ideas WHERE status=? ORDER BY priority_score DESC, created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_idea(idea_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM ideas WHERE id=?", (idea_id,)).fetchone()
    return dict(row) if row else None


def update_idea_status(idea_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE ideas SET status=?, updated_at=? WHERE id=?",
            (status, datetime.utcnow().isoformat(), idea_id),
        )


def update_idea_priority(idea_id: int, score: float, reason: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE ideas SET priority_score=?, priority_reason=?, updated_at=? WHERE id=?",
            (score, reason, datetime.utcnow().isoformat(), idea_id),
        )


# ── GOALS ─────────────────────────────────────────────────────────────────────

def add_goal(title: str, timeframe: str, description: str = "", quarter: str = "") -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO goals (title, description, timeframe, quarter, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (title, description, timeframe, quarter, now, now),
        )
        return cur.lastrowid


def get_goals(status: str = "active") -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM goals WHERE status=? ORDER BY timeframe, created_at DESC",
            (status,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_goal_progress(goal_id: int, progress: int) -> None:
    status = "completed" if progress >= 100 else "active"
    with get_conn() as conn:
        conn.execute(
            "UPDATE goals SET progress=?, status=?, updated_at=? WHERE id=?",
            (progress, status, datetime.utcnow().isoformat(), goal_id),
        )


def log_checkin(checkin_date: str, checkin_type: str, notes: str, mood: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO checkins (checkin_date, type, notes, mood, created_at) VALUES (?,?,?,?,?)",
            (checkin_date, checkin_type, notes, mood, now),
        )
        return cur.lastrowid


def get_checkins(days: int = 7) -> list[dict]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM checkins WHERE checkin_date >= ? ORDER BY checkin_date DESC",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── JOURNAL ───────────────────────────────────────────────────────────────────

def add_journal_entry(content: str, category: str = "moment", tags: str = "") -> int:
    now = datetime.utcnow().isoformat()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO journal (entry_date, content, category, tags, created_at) VALUES (?,?,?,?,?)",
            (today, content, category, tags, now),
        )
        return cur.lastrowid


def get_journal_entries(days: int = 2) -> list[dict]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM journal WHERE entry_date >= ? ORDER BY created_at DESC",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_journal_for_context(days: int = 7) -> list[dict]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT entry_date, content, category, tags FROM journal WHERE entry_date >= ? ORDER BY created_at DESC LIMIT 30",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── HEALTH ────────────────────────────────────────────────────────────────────

def add_health_log(log_date: str, sleep_hours: float | None, exercise: str,
                   diet_notes: str, energy: int | None, stress: int | None, notes: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT OR REPLACE INTO health_logs
               (log_date, sleep_hours, exercise, diet_notes, energy, stress, notes, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (log_date, sleep_hours, exercise, diet_notes, energy, stress, notes, now),
        )
        return cur.lastrowid


def get_health_logs(days: int = 7) -> list[dict]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM health_logs WHERE log_date >= ? ORDER BY log_date DESC",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def days_since_health_log() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT MAX(log_date) as last FROM health_logs").fetchone()
    if not row or not row["last"]:
        return 999
    last = datetime.strptime(row["last"], "%Y-%m-%d")
    return (datetime.utcnow() - last).days


# ── CAREER ────────────────────────────────────────────────────────────────────

def add_job(title: str, company: str, location: str, url: str, source: str,
            match_score: float, match_reason: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO job_listings
               (title, company, location, url, source, match_score, match_reason, found_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (title, company, location, url, source, match_score, match_reason, now),
        )
        return cur.lastrowid


def get_jobs(status: str = "new", min_score: float = 0.0) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM job_listings WHERE status=? AND match_score>=? ORDER BY match_score DESC",
            (status, min_score),
        ).fetchall()
    return [dict(r) for r in rows]


def update_job_status(job_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE job_listings SET status=? WHERE id=?", (status, job_id))


def add_skill(name: str, category: str = "", level: str = "learning", evidence: str = "") -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO skills (name, category, level, evidence, added_at, updated_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET
                 level=excluded.level, evidence=excluded.evidence, updated_at=excluded.updated_at""",
            (name, category, level, evidence, now, now),
        )
        return cur.lastrowid


def get_skills() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM skills ORDER BY category, name").fetchall()
    return [dict(r) for r in rows]


def get_latest_resume() -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM resume_versions ORDER BY version DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def save_resume_version(content: str, change_log: str = "") -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        row = conn.execute("SELECT MAX(version) as v FROM resume_versions").fetchone()
        version = (row["v"] or 0) + 1
        cur = conn.execute(
            "INSERT INTO resume_versions (version, content, change_log, created_at) VALUES (?,?,?,?)",
            (version, content, change_log, now),
        )
        return version


# ── INTELLIGENCE ──────────────────────────────────────────────────────────────

def save_agent_run(run_date: str, agent: str, raw_output: str, summary: str,
                   item_count: int, status: str, duration_ms: int) -> None:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO agent_runs
               (run_date, agent, raw_output, summary, item_count, status, duration_ms, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (run_date, agent, raw_output[:5000], summary, item_count, status, duration_ms, now),
        )


def get_latest_agent_summaries() -> dict[str, str]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT agent, summary FROM agent_runs
               WHERE run_date = (SELECT MAX(run_date) FROM agent_runs)
               AND status = 'ok'""",
        ).fetchall()
    return {r["agent"]: r["summary"] for r in rows}


def save_briefing(date: str, content: str) -> None:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO briefings (date, content, created_at) VALUES (?,?,?)",
            (date, content, now),
        )


def get_briefing(date: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT content FROM briefings WHERE date=?", (date,)).fetchone()
    return row["content"] if row else None


def mark_briefing_sent(date: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE briefings SET sent_at=? WHERE date=?",
            (datetime.utcnow().isoformat(), date),
        )


def get_last_agent_run_times() -> dict[str, str]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT agent, MAX(run_date) as last_run, MAX(status) as status
               FROM agent_runs GROUP BY agent""",
        ).fetchall()
    return {r["agent"]: f"{r['last_run']} ({r['status']})" for r in rows}


# ── BOT INTERACTIONS ──────────────────────────────────────────────────────────

def log_bot_interaction(interaction_type: str, input_text: str, command_name: str | None,
                        status: str, error_message: str | None = None,
                        response_sent: bool = False) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO bot_interactions
               (timestamp, type, input_text, command_name, status, error_message, response_sent)
               VALUES (?,?,?,?,?,?,?)""",
            (datetime.utcnow().isoformat(), interaction_type, input_text,
             command_name, status, error_message, int(response_sent)),
        )


# ── EVALUATIONS (AOS compounding loop) ───────────────────────────────────────

def save_evaluation(scores: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO evaluations
               (agent, goal, correctness, efficiency, reusability, clarity, notes, evaluated_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                scores.get("agent", "unknown"),
                scores.get("goal", ""),
                int(scores.get("correctness", 3)),
                int(scores.get("efficiency", 3)),
                int(scores.get("reusability", 3)),
                int(scores.get("clarity", 3)),
                scores.get("notes", ""),
                scores.get("evaluated_at", datetime.utcnow().isoformat()),
            ),
        )


def get_evaluation_summary(agent: str | None = None, days: int = 30) -> list[dict]:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        if agent:
            rows = conn.execute(
                """SELECT * FROM evaluations WHERE agent=? AND evaluated_at >= ?
                   ORDER BY evaluated_at DESC""",
                (agent, since),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM evaluations WHERE evaluated_at >= ? ORDER BY evaluated_at DESC",
                (since,),
            ).fetchall()
    return [dict(r) for r in rows]


# ── PRODUCT OS ────────────────────────────────────────────────────────────────

def save_cluster(name: str, description: str, idea_ids: list) -> int:
    import json as _json
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO idea_clusters (name, description, idea_ids, created_at, updated_at) VALUES (?,?,?,?,?)",
            (name, description, _json.dumps(idea_ids), now, now),
        )
        return cur.lastrowid


def get_clusters() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM idea_clusters ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def save_prd(cluster_id: int | None, title: str, overview: str = "", problem: str = "",
             goals: str = "", non_goals: str = "", user_stories: str = "",
             requirements: str = "", success_metrics: str = "", open_questions: str = "") -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO prds
               (cluster_id, title, overview, problem, goals, non_goals, user_stories,
                requirements, success_metrics, open_questions, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cluster_id, title, overview, problem, goals, non_goals, user_stories,
             requirements, success_metrics, open_questions, now, now),
        )
        return cur.lastrowid


def get_prd(prd_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM prds WHERE id=?", (prd_id,)).fetchone()
    return dict(row) if row else None


def get_all_prds() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM prds ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_prds_for_cluster(cluster_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM prds WHERE cluster_id=? ORDER BY created_at DESC", (cluster_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_prd_section(prd_id: int, field: str, value: str) -> None:
    allowed = {"overview", "problem", "goals", "non_goals", "user_stories",
               "requirements", "success_metrics", "open_questions", "title"}
    if field not in allowed:
        return
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(f"UPDATE prds SET {field}=?, updated_at=? WHERE id=?", (value, now, prd_id))


def update_prd_status(prd_id: int, status: str) -> None:
    allowed = {"draft", "active", "shipped", "archived"}
    if status not in allowed:
        return
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("UPDATE prds SET status=?, updated_at=? WHERE id=?", (status, now, prd_id))


def add_prd_comment(prd_id: int, author: str, comment_type: str, content: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO prd_comments (prd_id, author, type, content, created_at) VALUES (?,?,?,?,?)",
            (prd_id, author, comment_type, content, now),
        )
        return cur.lastrowid


def get_prd_comments(prd_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM prd_comments WHERE prd_id=? ORDER BY created_at ASC", (prd_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── DOMAIN AGENT STATE ────────────────────────────────────────────────────────

def get_agent_state() -> dict:
    """Return {agent_name, conversation, active_project} for the single-user session."""
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM user_agent_state WHERE id=1").fetchone()
        if not row:
            conn.execute(
                "INSERT INTO user_agent_state (id, agent_name, conversation, active_project, updated_at) "
                "VALUES (1,'product','[]','jobs-os',?)",
                (now,),
            )
            return {"agent_name": "product", "conversation": [], "active_project": "jobs-os"}
        return {
            "agent_name": row["agent_name"],
            "conversation": json.loads(row["conversation"]),
            "active_project": row["active_project"] if "active_project" in row.keys() else "jobs-os",
        }


def set_agent(name: str) -> None:
    """Switch active agent. Preserves active_project + agent-thread + project threads."""
    now = datetime.utcnow().isoformat()
    state = get_agent_state()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_agent_state (id, agent_name, conversation, active_project, updated_at) "
            "VALUES (1,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET agent_name=excluded.agent_name, conversation='[]', updated_at=excluded.updated_at",
            (name, "[]", state["active_project"], now),
        )


def set_active_project(project: str) -> None:
    """Switch the active project for plain-text messages. Preserves agent + threads."""
    now = datetime.utcnow().isoformat()
    state = get_agent_state()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_agent_state (id, agent_name, conversation, active_project, updated_at) "
            "VALUES (1,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET active_project=excluded.active_project, updated_at=excluded.updated_at",
            (state["agent_name"], json.dumps(state["conversation"]), project, now),
        )


def append_agent_message(role: str, content: str) -> None:
    """Append a message to conversation history, keeping last 10 exchanges."""
    now = datetime.utcnow().isoformat()
    state = get_agent_state()
    history = state["conversation"]
    history.append({"role": role, "content": content})
    history = history[-20:]  # keep last 20 turns (10 exchanges)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_agent_state (id, agent_name, conversation, active_project, updated_at) "
            "VALUES (1,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET conversation=excluded.conversation, updated_at=excluded.updated_at",
            (state["agent_name"], json.dumps(history), state["active_project"], now),
        )


def clear_agent_conversation() -> None:
    """Reset conversation history for the current agent."""
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "UPDATE user_agent_state SET conversation='[]', updated_at=? WHERE id=1", (now,)
        )


# ── PROJECT-SCOPED CONVERSATIONS ──────────────────────────────────────────────

def get_project_conversation(project: str) -> list[dict]:
    """Return the conversation thread for a project (plain-text channel)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT conversation FROM project_conversations WHERE project=?", (project,)
        ).fetchone()
        if not row:
            return []
        return json.loads(row["conversation"])


def append_project_message(project: str, role: str, content: str) -> None:
    """Append to a project's conversation, keeping last 20 turns (10 exchanges)."""
    now = datetime.utcnow().isoformat()
    history = get_project_conversation(project)
    history.append({"role": role, "content": content})
    history = history[-20:]
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO project_conversations (project, conversation, updated_at) "
            "VALUES (?,?,?) "
            "ON CONFLICT(project) DO UPDATE SET conversation=excluded.conversation, updated_at=excluded.updated_at",
            (project, json.dumps(history), now),
        )


def clear_project_conversation(project: str) -> None:
    """Reset a project's conversation thread."""
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO project_conversations (project, conversation, updated_at) "
            "VALUES (?, '[]', ?) "
            "ON CONFLICT(project) DO UPDATE SET conversation='[]', updated_at=excluded.updated_at",
            (project, now),
        )
