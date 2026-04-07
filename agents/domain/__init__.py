from __future__ import annotations

"""
Domain agent registry and invocation layer.

Each agent module exports: NAME, EMOJI, SYSTEM_PROMPT, TEMPERATURE
"""

from agents.domain import finance, product, strategy, research, contrarian, creative

AGENTS: dict[str, object] = {
    "finance":    finance,
    "product":    product,
    "strategy":   strategy,
    "research":   research,
    "contrarian": contrarian,
    "creative":   creative,
}


def invoke(agent_name: str, message: str, history: list[dict]) -> str:
    """
    Call the named domain agent with message + conversation history.
    Returns the agent's text response.
    """
    from utils.claude_client import ask

    agent = AGENTS.get(agent_name)
    if agent is None:
        agent = product  # default fallback

    # Build history context (last 10 turns)
    context_lines = []
    for turn in history[-10:]:
        role = turn.get("role", "user").upper()
        content = turn.get("content", "")[:600]  # truncate long turns
        context_lines.append(f"{role}: {content}")

    if context_lines:
        prompt = "\n".join(context_lines) + f"\nUSER: {message}"
    else:
        prompt = message

    return ask(
        prompt,
        system=agent.SYSTEM_PROMPT,
        max_tokens=1024,
    )


def agent_list_text() -> str:
    """Return a formatted list of all agents for display in Telegram."""
    lines = []
    for name, mod in AGENTS.items():
        lines.append(f"{mod.EMOJI} *{name.capitalize()}* — {_one_liner(name)}")
    return "\n".join(lines)


def _one_liner(name: str) -> str:
    descriptions = {
        "finance":    "financial analysis, risk, unit economics",
        "product":    "product strategy, prioritisation, roadmap",
        "strategy":   "competitive strategy, positioning, tradeoffs",
        "research":   "evidence synthesis, deep research, fact-checking",
        "contrarian": "challenge assumptions, stress-test plans",
        "creative":   "ideation, naming, divergent thinking",
    }
    return descriptions.get(name, "")
