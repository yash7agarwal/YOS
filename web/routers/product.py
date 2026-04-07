from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from store.database import (
    get_clusters, get_all_prds, get_prds_for_cluster,
    get_prd, get_prd_comments,
    add_prd_comment, update_prd_section, update_prd_status,
)
from utils.claude_client import ask
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

PRD_SECTIONS = ["overview", "problem", "goals", "non_goals",
                "user_stories", "requirements", "success_metrics", "open_questions"]
STATUS_OPTIONS = ["draft", "active", "shipped", "archived"]


# ── List view ─────────────────────────────────────────────────────────────────

@router.get("/product", response_class=HTMLResponse)
def product_page(request: Request):
    clusters = get_clusters()
    all_prds = get_all_prds()

    # Attach PRDs to their cluster; collect unclustered
    prd_by_cluster: dict[int, list] = {}
    unclustered: list = []
    for prd in all_prds:
        cid = prd.get("cluster_id")
        if cid:
            prd_by_cluster.setdefault(cid, []).append(prd)
        else:
            unclustered.append(prd)

    # Parse idea_ids JSON on each cluster
    for c in clusters:
        try:
            c["idea_ids_list"] = json.loads(c.get("idea_ids", "[]"))
        except Exception:
            c["idea_ids_list"] = []
        c["prds"] = prd_by_cluster.get(c["id"], [])

    return templates.TemplateResponse("product.html", {
        "request": request,
        "clusters": clusters,
        "unclustered": unclustered,
        "total_prds": len(all_prds),
        "status_options": STATUS_OPTIONS,
    })


# ── PRD detail ────────────────────────────────────────────────────────────────

@router.get("/product/prd/{prd_id}", response_class=HTMLResponse)
def prd_detail(request: Request, prd_id: int):
    prd = get_prd(prd_id)
    if not prd:
        return HTMLResponse("<h1>PRD not found</h1>", status_code=404)
    comments = get_prd_comments(prd_id)
    return templates.TemplateResponse("prd_detail.html", {
        "request": request,
        "prd": prd,
        "comments": comments,
        "sections": PRD_SECTIONS,
        "status_options": STATUS_OPTIONS,
    })


# ── Comment ───────────────────────────────────────────────────────────────────

@router.post("/api/product/prd/{prd_id}/comment")
async def post_comment(prd_id: int, content: str = Form(...)):
    if content.strip():
        add_prd_comment(prd_id, "user", "comment", content.strip())
    return RedirectResponse(url=f"/product/prd/{prd_id}", status_code=303)


# ── Status update ─────────────────────────────────────────────────────────────

@router.post("/api/product/prd/{prd_id}/status")
async def change_status(prd_id: int, status: str = Form(...)):
    update_prd_status(prd_id, status)
    return RedirectResponse(url=f"/product/prd/{prd_id}", status_code=303)


# ── Dev command (the alive part) ──────────────────────────────────────────────

@router.post("/api/product/prd/{prd_id}/command")
async def execute_command(prd_id: int, command: str = Form(...)):
    prd = get_prd(prd_id)
    if not prd:
        return JSONResponse({"error": "PRD not found"}, status_code=404)

    command = command.strip()
    if not command:
        return JSONResponse({"error": "empty command"}, status_code=400)

    # Build PRD context
    prd_text = _prd_as_text(prd)

    # Last 5 exchanges for context
    comments = get_prd_comments(prd_id)
    recent = comments[-5:] if len(comments) >= 5 else comments
    context_lines = [f"[{c['author'].upper()}] {c['content'][:300]}" for c in recent]
    context_text = "\n".join(context_lines) if context_lines else "No prior context."

    # --- Call 1: short JSON — response text + routing decision (no update_value) ---
    routing_prompt = f"""You are a product OS assistant. The user issued a command on this PRD.

--- PRD ---
{prd_text}

--- Recent context ---
{context_text}

--- Command ---
{command}

Reply with ONLY this JSON (no markdown, no extra text):
{{"response":"<your reply, max 300 chars>","update_field":"<one of: overview|problem|goals|non_goals|user_stories|requirements|success_metrics|open_questions|title — or null if no update needed>"}}

If the command asks to update/rewrite/add to a section, set update_field to that section name.
If it's a question or analysis, set update_field to null."""

    try:
        r1 = ask(routing_prompt, max_tokens=512)
        r1 = r1.strip()
        start = r1.find("{")
        end = r1.rfind("}")
        if start != -1 and end != -1:
            r1 = r1[start:end + 1]
        parsed = json.loads(r1)
    except Exception as exc:
        logger.warning("routing parse failed: %s", exc)
        parsed = {"response": "Sorry, I couldn't process that command. Please try again.", "update_field": None}

    field = parsed.get("update_field") if parsed.get("update_field") != "null" else None
    update_value = None

    # --- Call 2 (only if update needed): generate the full section content ---
    if field and field in PRD_SECTIONS + ["title"]:
        update_prompt = f"""You are a product OS assistant rewriting a PRD section.

PRD Title: {prd.get('title', '')}
Section to rewrite: {field}
Current content: {prd.get(field, '(empty)')}
User command: {command}

Write ONLY the new content for the "{field}" section — plain text, no JSON, no section header.
Be specific and concrete. Reflect the command exactly."""
        try:
            update_value = ask(update_prompt, max_tokens=1024).strip()
        except Exception as exc:
            logger.warning("update generation failed: %s", exc)
            update_value = None
            field = None

    # Save command + response to thread
    add_prd_comment(prd_id, "user", "command", command)
    add_prd_comment(prd_id, "claude", "response", parsed.get("response", ""))

    # Apply PRD update if we have content
    if field and update_value:
        update_prd_section(prd_id, field, update_value)
        add_prd_comment(prd_id, "claude", "update", f"Updated section: {field.replace('_', ' ').title()}")

    return JSONResponse({
        "response": parsed.get("response", ""),
        "updated": field if field and update_value else None,
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prd_as_text(prd: dict) -> str:
    lines = [f"Title: {prd.get('title', '')}",
             f"Status: {prd.get('status', 'draft')}"]
    labels = {
        "overview": "Overview", "problem": "Problem Statement",
        "goals": "Goals", "non_goals": "Non-Goals",
        "user_stories": "User Stories", "requirements": "Requirements",
        "success_metrics": "Success Metrics", "open_questions": "Open Questions",
    }
    for field, label in labels.items():
        val = prd.get(field, "")
        if val:
            lines.append(f"\n{label}:\n{val}")
    return "\n".join(lines)
