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

    deps = ShopContext(
        conn=conn,
        user_first_name=(user or {}).get("first_name") or None,
        user_id=(user or {}).get("id"),
    )

    try:
        result = await agent.run(message, deps=deps)
    except Exception:
        # Never leak provider errors, which can contain the request payload.
        log.exception("Agent run failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "The shopping assistant could not answer just now. Please try again.",
        ) from None

    reply = result.output
    products = deps.shown_products

    if user:
        _save_message(conn, user["id"], "user", message)
        _save_message(conn, user["id"], "assistant", reply, products)

    return ChatResponse(reply=reply, products=products)


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
