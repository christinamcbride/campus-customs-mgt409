"""Campus Customs API.

Run from the backend/ folder:

    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import logging
import sqlite3

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

import audit
import db
import routes_auth
import routes_catalogue
from agent import AgentUnavailable, agent_status, get_agent
from config import get_settings
from models import ChatMessage, ChatRequest, ChatResponse, ProductCard, ShopContext
from routes_auth import current_user_optional

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("campus_customs")

app = FastAPI(
    title="Campus Customs API",
    description="Catalogue, accounts and shopping assistant for Campus Customs.",
    version="0.3.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Products and images.
app.include_router(routes_catalogue.router)
# Registration, login, logout, current user.
app.include_router(routes_auth.router)


# --------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])

# Guests get a usable assistant but no stored history, since history is keyed
# to a user id. Signed-in shoppers get their conversation persisted.
HISTORY_LIMIT = 20
# Turns replayed into the model so it remembers the conversation. Kept small
# so a long history cannot crowd out the system prompt or inflate cost.
MEMORY_TURNS = 12

# Hard ceiling on the agent loop for a single message. Without this a model
# that keeps calling tools could loop until it times out or runs up a bill.
# Exceeding either limit stops the loop and is recorded in the audit trail.
CHAT_LIMITS = UsageLimits(request_limit=6, tool_calls_limit=10)


def _save_message(
    conn: sqlite3.Connection,
    user_id: int,
    role: str,
    content: str,
    products: list[ProductCard] | None = None,
) -> None:
    conn.execute(
        "INSERT INTO chat_messages (user_id, role, content, products_json) "
        "VALUES (?, ?, ?, ?)",
        (
            user_id,
            role,
            content,
            json.dumps([p.model_dump() for p in products]) if products else None,
        ),
    )
    conn.commit()


def _load_memory(conn: sqlite3.Connection, user_id: int) -> list[ModelMessage]:
    """Rebuild recent turns as model messages so the agent remembers them.

    Only the text of each turn is replayed. Stored tool calls and product
    payloads are not: the agent must re-run its tools against the live
    database rather than trusting figures captured in an earlier session,
    where a price or stock level may since have changed.
    """
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? "
        "ORDER BY id DESC LIMIT ?",
        (user_id, MEMORY_TURNS),
    ).fetchall()

    messages: list[ModelMessage] = []
    for row in reversed(rows):
        content = row["content"]
        if not content:
            continue
        if row["role"] == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


def _card_from_stored(item: dict) -> ProductCard | None:
    """Rebuild a ProductCard from a stored chat row.

    Rows seeded with the database predate the derived `category` field and
    carry extra keys, so the category is recomputed from `garment_type` and
    anything unrecognised is dropped rather than failing the whole message.
    """
    data = dict(item)
    if not data.get("category"):
        data["category"] = db.categorize(str(data.get("garment_type", "")))
    if not data.get("image_url") and data.get("image_file_path"):
        filename = str(data["image_file_path"]).split("/")[-1]
        data["image_url"] = f"/api/images/{filename}"
    try:
        return ProductCard(**data)
    except (ValueError, TypeError):
        log.warning("Dropping unreadable product card %r", data.get("product_id"))
        return None


@chat_router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    conn: sqlite3.Connection = Depends(db.get_connection),
    user: dict | None = Depends(current_user_optional),
) -> ChatResponse:
    """Send one message to the shopping assistant and get its reply.

    The reply carries any products the agent actually looked up, so the page can
    show exactly what the answer was based on.
    """
    message = payload.message.strip()
    if not message:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Message is empty.")

    try:
        agent = get_agent()
    except AgentUnavailable as exc:
        # A missing key is a configuration problem, not a server crash.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from None

    deps = ShopContext(conn=conn)
    memory: list[ModelMessage] = []

    if user:
        deps.user_id = user["id"]
        deps.user_first_name = user.get("first_name") or user["name"].split(" ")[0]
        deps.user_last_name = user.get("last_name")
        deps.user_full_name = user["name"]
        deps.user_email = user["email"]
        deps.member_since = (user.get("created_at") or "")[:10] or None
        # Signed-in shoppers get their conversation back; guests do not,
        # because nothing is stored for them.
        memory = _load_memory(conn, user["id"])

    # Resolve what they are looking at from our own data, not from the
    # browser's claims: only the id is taken from the request.
    if payload.page_context:
        deps.viewing_path = payload.page_context.path
        if payload.page_context.product_id:
            row = db.get_product(conn, payload.page_context.product_id)
            if row is not None:
                deps.viewing_product = ProductCard(
                    **{k: v for k, v in row.items() if k != "image_file_path"}
                )

    try:
        result = await agent.run(
            message,
            deps=deps,
            message_history=memory,
            usage_limits=CHAT_LIMITS,
        )
    except UsageLimitExceeded as exc:
        # The loop hit its configured ceiling. Recorded, then reported plainly.
        log.warning("Agent loop stopped at its limit: %s", exc)
        audit.record_run(
            stop_reason="limit_exceeded",
            user_id=deps.user_id,
            products_returned=len(deps.shown_products),
            detail=str(exc),
        )
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "That took more steps than I'm allowed for one question. Try "
            "asking about one product at a time.",
        ) from None
    except Exception as exc:
        # Never leak provider errors to the browser: they can echo the request
        # payload and name the upstream provider. Log the detail, return a
        # short message that tells the shopper whether retrying is worthwhile.
        log.exception("Agent run failed")
        detail = str(exc).lower()
        audit.record_run(
            stop_reason=(
                "content_filter" if "content_filter" in detail
                else "rate_limited" if ("rate" in detail and "limit" in detail)
                else "provider_error"
            ),
            user_id=deps.user_id,
            products_returned=len(deps.shown_products),
            detail=type(exc).__name__,
        )
        if "content_filter" in detail or "content management policy" in detail:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "I can't help with that request. Ask me about our products, "
                "sizes, prices or stock and I'll look it up.",
            ) from None
        if "rate" in detail and "limit" in detail:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "The shopping assistant is busy right now. Try again shortly.",
            ) from None
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "The shopping assistant could not answer just now. Please try again.",
        ) from None

    reply = result.output
    products = deps.shown_products

    usage = result.usage
    audit.record_run(
        stop_reason="completed",
        user_id=deps.user_id,
        tool_calls=getattr(usage, "tool_calls", None),
        requests=getattr(usage, "requests", None),
        products_returned=len(products),
    )

    if user:
        _save_message(conn, user["id"], "user", message)
        _save_message(conn, user["id"], "assistant", reply, products)

    return ChatResponse(reply=reply, products=products, matched_for=deps.last_query)


@chat_router.get("/history", response_model=list[ChatMessage])
def chat_history(
    conn: sqlite3.Connection = Depends(db.get_connection),
    user: dict | None = Depends(current_user_optional),
) -> list[ChatMessage]:
    """Recent conversation for the signed-in shopper. Empty list for guests."""
    if not user:
        return []
    rows = conn.execute(
        "SELECT id, role, content, products_json, created_at FROM chat_messages "
        "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user["id"], HISTORY_LIMIT),
    ).fetchall()

    messages: list[ChatMessage] = []
    for row in reversed(rows):
        products: list[ProductCard] = []
        if row["products_json"]:
            try:
                raw = json.loads(row["products_json"])
                products = [
                    card
                    for item in raw
                    if isinstance(item, dict)
                    and (card := _card_from_stored(item)) is not None
                ]
            except (ValueError, TypeError):
                # Stored rows predate the current shape; show the text anyway.
                log.warning("Skipping unreadable products_json on message %s", row["id"])
        messages.append(
            ChatMessage(
                id=int(row["id"]),
                role=row["role"],
                content=row["content"],
                products=products,
                created_at=row["created_at"],
            )
        )
    return messages


app.include_router(chat_router)


# --------------------------------------------------------------------------
# Meta
# --------------------------------------------------------------------------


@app.exception_handler(FileNotFoundError)
def missing_data_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
    """The database ships with the assignment and is not in git."""
    log.error("Data file missing: %s", exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, object]:
    s = get_settings()
    return {
        "status": "ok",
        "database_present": s.database_path.exists(),
        "products_dir_present": s.products_dir.is_dir(),
        "agent": agent_status(),
    }
