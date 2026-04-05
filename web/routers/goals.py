from __future__ import annotations

from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse

from store.database import get_goals, add_goal, update_goal_progress, get_checkins

BASE = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
router = APIRouter()

TIMEFRAMES = ["daily", "weekly", "quarterly", "yearly"]
TIMEFRAME_EMOJI = {"daily": "📅", "weekly": "🗓️", "quarterly": "📊", "yearly": "🎯"}


@router.get("/goals")
def goals_page(request: Request):
    goals = get_goals(status="active")
    grouped = {tf: [g for g in goals if g["timeframe"] == tf] for tf in TIMEFRAMES}
    checkins = get_checkins(days=7)
    return templates.TemplateResponse("goals.html", {
        "request": request,
        "grouped": grouped,
        "timeframes": TIMEFRAMES,
        "emoji": TIMEFRAME_EMOJI,
        "checkins": checkins,
    })


@router.post("/api/goals/add")
def add_goal_api(title: str = Form(...), timeframe: str = Form(...)):
    now = datetime.utcnow()
    quarter = f"Q{(now.month - 1) // 3 + 1} {now.year}" if timeframe == "quarterly" else ""
    add_goal(title=title, timeframe=timeframe, quarter=quarter)
    return RedirectResponse(url="/goals", status_code=303)


@router.post("/api/goals/{goal_id}/progress")
def update_progress_api(goal_id: int, progress: int = Form(...)):
    update_goal_progress(goal_id, progress)
    return JSONResponse({"ok": True})
