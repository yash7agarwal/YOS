"""
tools/ai.py — AI execution tool

Thin wrapper over utils/claude_client.py.
All Claude API calls in the system go through here.
"""
from __future__ import annotations

from utils.claude_client import ask, ask_deep, DEFAULT_MODEL, DEEP_MODEL

__all__ = ["ask", "ask_deep", "DEFAULT_MODEL", "DEEP_MODEL"]
