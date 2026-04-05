"""
tools/eval.py — Evaluation execution tool

AOS compounding loop: score every meaningful output on 4 dimensions.
Saves scores to the evaluations table for trend analysis.
"""
from __future__ import annotations

import json
from datetime import datetime

from utils.claude_client import ask
from utils.logger import get_logger

logger = get_logger(__name__)


def score_output(
    agent: str,
    goal: str,
    output: str,
    context: str = "",
) -> dict:
    """
    Score an agent output on AOS 4 dimensions (1-5 each).
    Returns dict with correctness, efficiency, reusability, clarity, notes.
    Saves to evaluations table.
    """
    prompt = f"""You are evaluating an AI agent output for a personal operating system.

Agent: {agent}
Goal: {goal}
Context: {context}

Output to evaluate:
{output[:2000]}

Score this output on each dimension (integer 1-5):
- correctness: accurate, grounded, internally consistent?
- efficiency: minimal waste, reused existing knowledge?
- reusability: creates value beyond this single task?
- clarity: understandable, structured, actionable?

Respond ONLY with valid JSON:
{{"correctness": N, "efficiency": N, "reusability": N, "clarity": N, "notes": "one sentence"}}"""

    try:
        result = ask(prompt, max_tokens=256)
        scores = json.loads(result.strip())
    except Exception as exc:
        logger.warning("eval scoring failed agent=%s error=%s", agent, exc)
        scores = {"correctness": 3, "efficiency": 3, "reusability": 3, "clarity": 3, "notes": "auto-eval failed"}

    scores["agent"] = agent
    scores["goal"] = goal
    scores["evaluated_at"] = datetime.utcnow().isoformat()

    _save_evaluation(scores)
    return scores


def _save_evaluation(scores: dict) -> None:
    try:
        from store.database import save_evaluation
        save_evaluation(scores)
    except Exception as exc:
        logger.warning("save_evaluation failed: %s", exc)
