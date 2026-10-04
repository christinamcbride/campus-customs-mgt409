"""Pydantic and PydanticAI structured types shared by the API and the agent.

The product-facing types here mirror what the database returns. Nothing in this
module invents defaults for price or stock: those fields are required, so a
malformed row fails loudly instead of rendering as "$0.00 — in stock".
"""

from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import Connection

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Catalogue types
# --------------------------------------------------------------------------


class SizeStock(BaseModel):
    """Stock for one size of one product."""

    size: str
    quantity: int
    in_stock: bool


class ProductCard(BaseModel):
    """A product as shown on the site and attached to a chat reply.

    This is the shape the frontend renders in the chat panel's product strip and
    on the catalogue grid, so the agent and the catalogue endpoints agree on one
    representation.
    """

    product_id: str
    name: str
    garment_type: str
    category: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_url: str
    price: float
    total_stock: int | None = None


class ProductCardDetail(ProductCard):
    """A product card plus its per-size inventory."""

    sizes: list[SizeStock]


# --------------------------------------------------------------------------
# Tool result types
# --------------------------------------------------------------------------
# Tools return these rather than raw rows, so the model always receives a
# predictable shape and an explicit "found nothing" signal instead of silence.


class ProductSearchResult(BaseModel):
    """What a catalogue search found. `matches` is empty when nothing matched."""

    query: str
    match_count: int
    matches: list[ProductCard]
    note: str | None = Field(
        default=None,
        description="Set when the search found nothing, explaining what was tried.",
    )


class InventoryResult(BaseModel):
    """Per-size stock for one product, split into available and sold out."""

    product_id: str
    name: str
    price: float
    available_sizes: list[SizeStock]
    sold_out_sizes: list[SizeStock]
    total_stock: int

    @property
    def fully_sold_out(self) -> bool:
        return self.total_stock == 0


class LookupFailure(BaseModel):
    """Returned when an identifier does not exist, so the model states it plainly."""

    reason: str
    product_id: str | None = None


# --------------------------------------------------------------------------
# Chat API types
# --------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatMessage(BaseModel):
    """One stored turn of a conversation."""

    id: int
    role: str
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


class ChatResponse(BaseModel):
    """The agent's reply plus any products the frontend should display."""

    reply: str
    products: list[ProductCard] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Agent dependencies
# --------------------------------------------------------------------------


@dataclass
class ShopContext:
    """Per-request dependencies handed to the agent and its tools.

    Carries the open database connection so tools query the same data the rest
    of the request sees, and the shopper's first name when they are signed in.

    `shown_products` is the side channel: tools append the products they
    retrieved, and the chat route returns them to the frontend so the page can
    display exactly what the agent actually looked at.
    """

    conn: Connection
    user_first_name: str | None = None
    user_id: int | None = None

    def __post_init__(self) -> None:
        self.shown_products: list[ProductCard] = []

    def remember(self, products: list[ProductCard]) -> None:
        """Record products a tool returned, keeping first-seen order."""
        seen = {p.product_id for p in self.shown_products}
        for p in products:
            if p.product_id not in seen:
                self.shown_products.append(p)
                seen.add(p.product_id)
