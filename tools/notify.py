"""
tools/notify.py — Notification execution tool

Thin wrapper over utils/telegram.py.
All outbound notifications go through here.
"""
from __future__ import annotations

from utils.telegram import send_message, send_markdown

__all__ = ["send_message", "send_markdown"]
