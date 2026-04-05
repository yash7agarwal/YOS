from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse

from store.database import get_jobs, get_skills, add_skill, update_job_status, get_latest_resume

BASE = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
router = APIRouter()


@router.get("/career")
def career_page(request: Request):
    jobs = get_jobs(status="new")
    applied = get_jobs(status="applied")
    skills = get_skills()
    resume = get_latest_resume()

    grouped_skills: dict[str, list] = {}
    for s in skills:
        grouped_skills.setdefault(s["category"] or "General", []).append(s)

    return templates.TemplateResponse("career.html", {
        "request": request,
        "jobs": jobs,
        "applied": applied,
        "grouped_skills": grouped_skills,
        "resume": resume,
    })


@router.post("/api/career/jobs/{job_id}/apply")
def apply_job(job_id: int):
    update_job_status(job_id, "applied")
    return JSONResponse({"ok": True})


@router.post("/api/career/skill/add")
def add_skill_api(name: str = Form(...), category: str = Form("General"), level: str = Form("learning")):
    add_skill(name=name, category=category, level=level)
    return RedirectResponse(url="/career", status_code=303)
