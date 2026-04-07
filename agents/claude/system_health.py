from __future__ import annotations

"""
System Health Agent — launchd-aware

Checks all YOS launchd services are alive via `launchctl list`.
Restarts dead services with `launchctl kickstart`.
Sends a Telegram alert if anything needed attention.
"""

import os
import subprocess
from datetime import datetime

from utils.telegram import send_message
from utils.logger import get_logger

load_dotenv = __import__("dotenv").load_dotenv
load_dotenv()

logger = get_logger(__name__)

UID = os.getuid()

# launchd service name → human label
SERVICES = {
    "com.yos.bot":       "YOS Bot",
    "com.yos.scheduler": "YOS Scheduler",
    "com.yos.web":       "YOS Web",
}


def _launchd_pid(service: str) -> int | None:
    """Return the PID of a running launchd service, or None if not running."""
    try:
        out = subprocess.check_output(
            ["launchctl", "list", service],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for line in out.splitlines():
            line = line.strip().strip('"').rstrip(';').strip()
            if line.startswith('"PID"') or line.startswith('PID'):
                # Format: "PID" = 12345;
                pid_str = line.split('=')[-1].strip().rstrip(';').strip().strip('"')
                return int(pid_str)
    except (subprocess.CalledProcessError, ValueError):
        pass
    return None


def _kickstart(service: str) -> bool:
    """Restart a launchd service. Returns True on success."""
    try:
        subprocess.check_call(
            ["launchctl", "kickstart", "-k", f"gui/{UID}/{service}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run() -> dict:
    """Check all launchd services, restart dead ones. Returns status report."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    status = {}
    restarted = []
    healthy = []

    for service, label in SERVICES.items():
        pid = _launchd_pid(service)
        if pid:
            status[service] = f"✅ running (PID {pid})"
            healthy.append(label)
            logger.info(f"[health] {label}: OK (PID {pid})")
        else:
            logger.warning(f"[health] {label} is DOWN — restarting via launchd…")
            ok = _kickstart(service)
            if ok:
                new_pid = _launchd_pid(service)
                status[service] = f"🔄 restarted (PID {new_pid or '?'})"
                restarted.append(label)
                logger.info(f"[health] Restarted {label} (PID {new_pid})")
            else:
                status[service] = f"❌ failed to restart"
                logger.error(f"[health] Failed to restart {label}")

    if restarted:
        lines = [f"⚠️ YOS Health Alert — {now}\n"]
        for label in restarted:
            lines.append(f"🔄 Restarted: {label}")
        for label in healthy:
            lines.append(f"✅ OK: {label}")
        send_message("\n".join(lines))
        logger.info(f"[health] Restarted services: {restarted}")
    else:
        logger.info(f"[health] All services healthy.")

    return status


if __name__ == "__main__":
    report = run()
    for k, v in report.items():
        print(f"{k}: {v}")
