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


def invoke(
    agent_name: str,
    message: str,
    history: list[dict],
    project_context: str = "",
    max_tokens: int = 1024,
) -> str:
    """
    Call the named domain agent with message + conversation history.

    When project_context is non-empty, it's prepended to the system prompt so
    the agent answers with full awareness of the active workspace project
    (CLAUDE.md, recent commits, open questions). Used by the natural-language
    Telegram handler to give Claude-terminal-grade responses on mobile.
    """
    from utils.claude_client import ask

    agent = AGENTS.get(agent_name)
    if agent is None:
        agent = product  # default fallback

    system = agent.SYSTEM_PROMPT
    if project_context:
        system = (
            f"{project_context}\n\n"
            f"---\n\n"
            f"You are operating as the **{agent_name}** lens for the project above. "
            f"Use the project's CLAUDE.md instructions and recent context to inform every reply. "
            f"Your persona / lens:\n\n"
            f"{agent.SYSTEM_PROMPT}"
        )

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
        system=system,
        max_tokens=max_tokens,
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
