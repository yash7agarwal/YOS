# Workflow: System Health Monitoring

## Objective
Every 6 hours, verify that critical processes (bot, scheduler, web) are running. Auto-restart dead processes and alert via Telegram if a restart occurs.

## Inputs
- PID files: `logs/bot.pid`, `logs/scheduler.pid`
- Process existence check via `os.kill(pid, 0)`

## Outputs
- Restarted processes (if dead)
- Telegram alert: "⚠️ YOS: bot process was dead and restarted"
- Log entry in `logs/daily/`

## Tools Used
- `agents/claude/system_health.py`
- `utils/telegram.py:send_message()`
- `subprocess.Popen()` for process restart

## Steps

1. **Read PID files**
   - `logs/bot.pid` → bot PID
   - `logs/scheduler.pid` → scheduler PID

2. **Check each PID**
   - `os.kill(pid, 0)` — raises `ProcessLookupError` if dead
   - If dead: log, restart via `subprocess.Popen(...)`, send Telegram alert

3. **Log health check**
   - Append to `logs/daily/<date>.log`: "Health check: bot=OK, scheduler=OK"

## Restart Commands

| Process | Command |
|---|---|
| Bot | `python3 -m bot.main` |
| Scheduler | `python3 -m scheduler.main` |

## Edge Cases
- If PID file missing: process was never started; start it cold
- If restart fails: send alert "YOS: FAILED to restart bot — manual intervention needed"
- Never restart more than 3 times per hour (prevent restart loop)

## Quality Bar
- All critical processes verified within 10 minutes of a failure
- No silent failures — every restart produces a Telegram alert

## Trigger
- APScheduler: every 6 hours in `scheduler/main.py`
- Manual: `python3 -m agents.claude.system_health`
