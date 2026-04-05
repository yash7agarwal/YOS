from __future__ import annotations

import time
from datetime import datetime

import anthropic
from dotenv import load_dotenv

from agents.claude.tools import TOOL_DEFINITIONS, execute_tool
from store.database import save_agent_run
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

DEEP_MODEL = "claude-opus-4-6"
DEFAULT_MODEL = "claude-sonnet-4-6"


def run_agent(
    name: str,
    system_prompt: str,
    goal: str,
    tool_names: list[str] | None = None,
    max_turns: int = 15,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Run a Claude agent with a tool-use loop until it reaches end_turn.

    Claude autonomously decides which tools to call and in what order.
    Returns the final text response.
    """
    start = time.time()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Filter tools to only those requested
    tools = TOOL_DEFINITIONS
    if tool_names:
        tools = [t for t in TOOL_DEFINITIONS if t["name"] in tool_names]

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": goal}]

    logger.info(f"[{name}] Starting agent — model={model}, tools={[t['name'] for t in tools]}")

    final_text = ""
    turns_used = 0

    for turn in range(max_turns):
        turns_used = turn + 1
        response = client.messages.create(
            model=model,
            system=system_prompt,
            tools=tools,
            messages=messages,
            max_tokens=4096,
        )

        logger.info(f"[{name}] Turn {turn + 1}: stop_reason={response.stop_reason}")

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"[{name}] Calling tool: {block.name}({list(block.input.keys())})")
                    result = execute_tool(block.name, block.input)
                    logger.debug(f"[{name}] Tool result: {result[:200]}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            logger.warning(f"[{name}] Unexpected stop_reason: {response.stop_reason}")
            break

    else:
        final_text = f"[{name}] Reached max turns ({max_turns}) without completing."
        logger.warning(final_text)

    duration_ms = int((time.time() - start) * 1000)
    save_agent_run(today, name, goal, final_text[:5000], turns_used, "ok", duration_ms)
    logger.info(f"[{name}] Done — {turns_used} turns, {duration_ms}ms")

    return final_text
