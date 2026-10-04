"""PydanticAI agent wiring for the Campus Customs shopping assistant.

The agent is built once and reused. Its instructions come from
``prompts/prompt.md`` so the voice and safety rules can be edited without
touching Python.

The model is reached through an OpenAI-compatible gateway, authenticated with
``PORTKEY_API_KEY``. Nothing here hard-codes a provider beyond that interface:
pointing ``AI_BASE_URL`` somewhere else is enough to switch backends.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import get_settings
from models import ShopContext
from tools import register_tools

log = logging.getLogger("campus_customs.agent")

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "prompt.md"


class AgentUnavailable(RuntimeError):
    """Raised when the agent cannot run, e.g. no API key is configured."""


def load_system_prompt() -> str:
    """Read the system prompt from disk.

    Read at agent construction rather than imported as a string so the prompt
    stays a plain Markdown file that can be edited and reviewed on its own.
    """
    if not PROMPT_PATH.exists():
        raise AgentUnavailable(f"System prompt not found at {PROMPT_PATH}")
    text = PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not text:
        raise AgentUnavailable(f"System prompt at {PROMPT_PATH} is empty")
    return text


@lru_cache
def get_agent() -> Agent[ShopContext, str]:
    """Build the agent once per process.

    Raises:
        AgentUnavailable: if no API key is configured, so the caller can return
            a clear message instead of a stack trace.
    """
    settings = get_settings()
    if not settings.portkey_api_key:
        raise AgentUnavailable(
            "The shopping assistant is not configured: PORTKEY_API_KEY is not "
            "set. Add it to backend/.env and restart the server."
        )

    model = OpenAIChatModel(
        settings.ai_model,
        provider=OpenAIProvider(
            api_key=settings.portkey_api_key,
            base_url=settings.ai_base_url,
        ),
    )

    agent = Agent(
        model,
        deps_type=ShopContext,
        output_type=str,
        instructions=load_system_prompt(),
        retries=2,
    )

    @agent.instructions
    def shopper_context(ctx) -> str:
        """Per-request facts appended to the static prompt."""
        if ctx.deps.user_first_name:
            return (
                f"The shopper is signed in and their first name is "
                f"{ctx.deps.user_first_name}. You know nothing else about them."
            )
        return (
            "The shopper is not signed in, so you do not know their name. Do "
            "not ask for it; just help them shop."
        )

    register_tools(agent)
    log.info(
        "Shopping assistant ready: model=%s base_url=%s",
        settings.ai_model,
        settings.ai_base_url,
    )
    return agent


def agent_status() -> dict[str, object]:
    """Describe the agent's configuration without exposing the API key."""
    settings = get_settings()
    return {
        "configured": bool(settings.portkey_api_key),
        "model": settings.ai_model,
        "base_url": settings.ai_base_url,
        "prompt_file": str(PROMPT_PATH.relative_to(PROMPT_PATH.parents[1])),
        "prompt_present": PROMPT_PATH.exists(),
    }
