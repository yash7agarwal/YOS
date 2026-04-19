from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error

import anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "claude-sonnet-4-6"
FAST_MODEL = "claude-haiku-4-5-20251001"
INFERENCE_MODE = os.getenv("INFERENCE_MODE", "cloud")  # "cloud" | "local"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost:11434")

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Add it to your .env file."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def ask(
    prompt: str,
    max_tokens: int = 1024,
    model: str = DEFAULT_MODEL,
    system: str = "",
    retries: int = 3,
) -> str:
    """Call Claude and return the text response. Retries on transient errors."""
    messages = [{"role": "user", "content": prompt}]
    kwargs: dict = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        kwargs["system"] = system

    for attempt in range(retries):
        try:
            resp = _get_client().messages.create(**kwargs)
            return resp.content[0].text
        except anthropic.RateLimitError:
            time.sleep(2 ** attempt * 5)
        except anthropic.APIStatusError as e:
            if e.status_code >= 500 and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
            else:
                raise
    raise RuntimeError(f"Claude call failed after {retries} retries")


def ask_fast(prompt: str, max_tokens: int = 512) -> str:
    """Use the fast/cheap model for low-stakes tasks."""
    return ask(prompt, max_tokens=max_tokens, model=FAST_MODEL)


def ask_local(
    prompt: str,
    model: str = "gemma3:4b",
    max_tokens: int = 1024,
    system: str = "",
) -> str:
    """Call local Ollama instance. Falls back to ask() if Ollama is unavailable."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    payload = json.dumps({
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }).encode()
    try:
        req = urllib.request.Request(
            f"http://{OLLAMA_HOST}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data.get("response", "").strip()
    except (urllib.error.URLError, OSError):
        # Ollama not available — fall back to cloud
        return ask(prompt, max_tokens=max_tokens, system=system)


def ask_auto(prompt: str, max_tokens: int = 1024, system: str = "", model: str = "gemma3:4b") -> str:
    """Route to local or cloud based on INFERENCE_MODE env var."""
    if INFERENCE_MODE == "local":
        return ask_local(prompt, model=model, max_tokens=max_tokens, system=system)
    return ask(prompt, max_tokens=max_tokens, system=system)
