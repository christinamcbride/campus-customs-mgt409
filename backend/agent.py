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
        """Who is chatting. Rebuilt per request, never baked into the prompt."""
        deps = ctx.deps
        if not deps.is_signed_in:
            return (
                "The shopper is NOT signed in. You do not know their name or "
                "email, and no chat history is kept for them. Do not ask them "
                "to log in unless they raise it; just help them shop."
            )
        lines = [
            "The shopper is signed in. Their account details:",
            f"- Name: {deps.user_full_name}",
            f"- First name: {deps.user_first_name}",
            f"- Email: {deps.user_email}",
        ]
        if deps.member_since:
            lines.append(f"- Customer since: {deps.member_since}")
        lines.append(
            "Greet them by first name when it fits naturally. You know nothing "
            "else about them: do not guess their size, budget, affiliation or "
            "past purchases. Never repeat their email back unless they ask for "
            "it, and never discuss passwords or account security."
        )
        return "\n".join(lines)

    @agent.instructions
    def page_context(ctx) -> str:
        """What the shopper is looking at, so 'this' resolves to a product."""
        product = ctx.deps.viewing_product
        if product is None:
            if ctx.deps.viewing_path and ctx.deps.viewing_path != "/":
                return (
                    f"The shopper is on the page {ctx.deps.viewing_path}. They "
                    "are not viewing a specific product, so if they say "
                    '"this" or "it" without naming an item, ask which product '
                    "they mean."
                )
            return (
                "The shopper is browsing the site but not viewing a specific "
                'product. If they say "this" or "it" without naming an item, '
                "ask which product they mean rather than guessing."
            )
        colors = ", ".join(product.colors) if product.colors else "not recorded"
        return (
            "The shopper is currently viewing this product page:\n"
            f"- product_id: {product.product_id}\n"
            f"- Name: {product.name}\n"
            f"- Price: ${product.price:.2f}\n"
            f"- Colours on file: {colors}\n"
            'Treat "this", "it", "this one" and similar as referring to this '
            "product. Use its product_id when calling a tool about it. Still "
            "call the tools for sizes, stock or anything you need to confirm "
            "— do not answer from these few fields alone."
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
