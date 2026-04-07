from __future__ import annotations

"""
Domain agent commands: /agent, /ask, /reset
"""

from telegram import Update
from telegram.ext import ContextTypes

from agents.domain import AGENTS, invoke, agent_list_text
from store.database import get_agent_state, set_agent, append_agent_message, clear_agent_conversation
from utils.logger import get_logger

logger = get_logger(__name__)


async def cmd_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/agent [name] — show active agent or switch to a new one."""
    args = context.args or []

    if not args:
        # Show current agent + list
        state = get_agent_state()
        current = state["agent_name"]
        mod = AGENTS.get(current)
        emoji = mod.EMOJI if mod else "🤖"
        history_len = len(state["conversation"])

        text = (
            f"{emoji} *Active agent: {current.capitalize()}*\n"
            f"_{history_len} message{'s' if history_len != 1 else ''} in conversation_\n\n"
            f"*Available agents:*\n{agent_list_text()}\n\n"
            f"Switch with `/agent <name>` · Clear history with `/reset`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
        return

    name = args[0].lower().strip()
    if name not in AGENTS:
        names = ", ".join(f"`{n}`" for n in AGENTS)
        await update.message.reply_text(
            f"Unknown agent `{name}`.\nAvailable: {names}",
            parse_mode="Markdown",
        )
        return

    set_agent(name)
    mod = AGENTS[name]
    await update.message.reply_text(
        f"Switched to {mod.EMOJI} *{name.capitalize()} Agent*\n"
        f"_Conversation history cleared. Ready for your first message._\n\n"
        f"Use `/ask <your message>` to query this agent.",
        parse_mode="Markdown",
    )
    logger.info(f"[domain] Switched to agent: {name}")


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ask <message> — query the active domain agent."""
    message = " ".join(context.args) if context.args else ""

    if not message:
        state = get_agent_state()
        current = state["agent_name"]
        mod = AGENTS.get(current)
        emoji = mod.EMOJI if mod else "🤖"
        await update.message.reply_text(
            f"Usage: `/ask <your question or request>`\n\n"
            f"Current agent: {emoji} *{current.capitalize()}*",
            parse_mode="Markdown",
        )
        return

    state = get_agent_state()
    agent_name = state["agent_name"]
    history = state["conversation"]
    mod = AGENTS.get(agent_name)
    emoji = mod.EMOJI if mod else "🤖"

    # Send typing indicator
    await update.message.chat.send_action("typing")

    try:
        response = invoke(agent_name, message, history)
    except Exception as e:
        logger.error(f"[domain] invoke failed: {e}")
        await update.message.reply_text("Agent encountered an error. Please try again.")
        return

    # Persist exchange
    append_agent_message("user", message)
    append_agent_message("assistant", response)

    # Chunk if needed (Telegram 4096 char limit)
    header = f"{emoji} *{agent_name.capitalize()}*\n\n"
    full = header + response
    if len(full) <= 4000:
        await update.message.reply_text(full, parse_mode="Markdown")
    else:
        # Send header + chunked response
        await update.message.reply_text(header, parse_mode="Markdown")
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i + 4000])


async def cmd_reset_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reset — clear conversation history for the active agent."""
    state = get_agent_state()
    agent_name = state["agent_name"]
    history_len = len(state["conversation"])

    clear_agent_conversation()

    mod = AGENTS.get(agent_name)
    emoji = mod.EMOJI if mod else "🤖"
    await update.message.reply_text(
        f"{emoji} *{agent_name.capitalize()} Agent* — conversation cleared\n"
        f"_{history_len} message{'s' if history_len != 1 else ''} removed._",
        parse_mode="Markdown",
    )
    logger.info(f"[domain] Cleared conversation for agent: {agent_name}")
