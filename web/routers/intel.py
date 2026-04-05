from __future__ import annotations

from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from store.database import get_briefing, get_last_agent_run_times, get_latest_agent_summaries

BASE = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
router = APIRouter()


@router.get("/intel")
def intel_page(request: Request):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    briefing = get_briefing(today) or ""
    agent_times = get_last_agent_run_times()
    summaries = get_latest_agent_summaries()
    return templates.TemplateResponse("intel.html", {
        "request": request,
        "briefing": briefing,
        "agent_times": agent_times,
        "summaries": summaries,
        "today": today,
    })


@router.get("/api/intel/briefing")
def api_briefing():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return JSONResponse({"date": today, "briefing": get_briefing(today) or ""})
