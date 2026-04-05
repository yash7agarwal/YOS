from __future__ import annotations

"""
System Health Agent

Runs every 6 hours. Checks all YOS processes are alive and restarts them if dead.
Sends alert to Telegram if anything needs attention.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from utils.telegram import send_message
from utils.logger import get_logger

load_dotenv = __import__("dotenv").load_dotenv
load_dotenv()

logger = get_logger(__name__)

YOS_DIR = Path(__file__).parent.parent.parent
PID_DIR = YOS_DIR / "logs"

PROCESSES = {
    "bot": {
        "pid_file": "logs/bot.pid",
        "cmd": ["python3", "-m", "bot.main"],
        "log": "logs/daily/bot.log",
    },
    "scheduler": {
        "pid_file": "logs/scheduler.pid",
        "cmd": ["python3", "-m", "scheduler.main"],
        "log": "logs/daily/scheduler.log",
    },
    "web": {
        "pid_file": "logs/web.pid",
        "cmd": ["python3", "-m", "web.app"],
        "log": "logs/daily/web.log",
    },
}


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _read_pid(pid_file: str) -> int | None:
    path = YOS_DIR / pid_file
    if path.exists():
        try:
            return int(path.read_text().strip())
        except ValueError:
            return None
    return None


def _write_pid(pid_file: str, pid: int) -> None:
    (YOS_DIR / pid_file).write_text(str(pid))


def _start_process(name: str, config: dict) -> int:
    log_path = YOS_DIR / config["log"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as log_f:
        proc = subprocess.Popen(
            config["cmd"],
            cwd=str(YOS_DIR),
            stdout=log_f,
            stderr=log_f,
            start_new_session=True,
        )
    _write_pid(config["pid_file"], proc.pid)
    logger.info(f"[health] Started {name} (PID {proc.pid})")
    return proc.pid


def run() -> dict:
    """Check all processes, restart dead ones. Returns status report."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    status = {}
    restarted = []
    already_running = []

    for name, config in PROCESSES.items():
        pid = _read_pid(config["pid_file"])
        if pid and _is_running(pid):
            status[name] = f"✅ running (PID {pid})"
            already_running.append(name)
        else:
            logger.warning(f"[health] {name} is DOWN — restarting…")
            try:
                new_pid = _start_process(name, config)
                status[name] = f"🔄 restarted (PID {new_pid})"
                restarted.append(name)
            except Exception as e:
                status[name] = f"❌ failed to restart: {e}"
                logger.error(f"[health] Failed to restart {name}: {e}")

    if restarted:
        lines = [f"⚠️ *YOS Health Alert — {now}*\n"]
        for name in restarted:
            lines.append(f"🔄 Restarted: *{name}* — {status[name]}")
        for name in already_running:
            lines.append(f"✅ OK: {name}")
        send_message("\n".join(lines))
        logger.info(f"[health] Restarted: {restarted}")
    else:
        logger.info(f"[health] All processes healthy: {list(status.keys())}")

    return status


if __name__ == "__main__":
    report = run()
    for k, v in report.items():
        print(f"{k}: {v}")
