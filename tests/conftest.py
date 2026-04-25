"""Pytest bootstrap for YOS.

Ensures the project root is on sys.path so tests can import top-level
packages (`bot`, `store`, `utils`, ...) without an editable install, and
sets a benign TELEGRAM_CHAT_ID before any module reads it at import time.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# bot.dispatcher reads TELEGRAM_CHAT_ID at import time; give it a deterministic
# value so tests never depend on the developer's .env.
os.environ.setdefault("TELEGRAM_CHAT_ID", "0")
