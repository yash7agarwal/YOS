from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse

from store.database import get_backlog, add_idea, update_idea_status

BASE = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
router = APIRouter()

STATUSES = ["inbox", "in_progress", "done", "archived"]


@router.get("/backlog")
def backlog_page(request: Request):
    columns = {s: get_backlog(status=s, limit=30) for s in STATUSES}
    return templates.TemplateResponse("backlog.html", {
        "request": request,
        "columns": columns,
        "statuses": STATUSES,
    })


@router.post("/api/backlog/add")
def add_idea_api(title: str = Form(...), description: str = Form("")):
    idea_id = add_idea(title=title, description=description, source="web")
    return RedirectResponse(url="/backlog", status_code=303)


@router.post("/api/backlog/{idea_id}/status")
def update_status_api(idea_id: int, status: str = Form(...)):
    if status not in STATUSES:
        return JSONResponse({"error": f"Invalid status. Must be one of: {STATUSES}"}, status_code=400)
    update_idea_status(idea_id, status)
    return JSONResponse({"ok": True})
