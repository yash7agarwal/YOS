"""
tools/db.py — Database execution tool

Thin wrapper over store/database.py. All DB reads/writes go through here.
"""
from __future__ import annotations

from store.database import (
    # Ideas
    add_idea,
    get_backlog,
    update_idea_priority,
    mark_idea_done,
    # Goals
    add_goal,
    get_goals,
    update_goal_progress,
    add_checkin,
    # Journal
    add_journal_entry,
    get_journal,
    # Health
    add_health_log,
    get_health_summary,
    days_since_health_log,
    # Career
    add_job,
    get_top_jobs,
    add_skill,
    get_skills,
    get_resume,
    save_resume,
    # Intelligence
    save_agent_run,
    get_latest_agent_summaries,
    save_briefing,
    get_briefing,
    # Evaluations
    save_evaluation,
    # Init
    init_db,
)

__all__ = [
    "add_idea", "get_backlog", "update_idea_priority", "mark_idea_done",
    "add_goal", "get_goals", "update_goal_progress", "add_checkin",
    "add_journal_entry", "get_journal",
    "add_health_log", "get_health_summary", "days_since_health_log",
    "add_job", "get_top_jobs", "add_skill", "get_skills", "get_resume", "save_resume",
    "save_agent_run", "get_latest_agent_summaries", "save_briefing", "get_briefing",
    "save_evaluation",
    "init_db",
]
