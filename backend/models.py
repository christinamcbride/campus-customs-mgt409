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
    """Stock for one size of one product.

    `in_stock` and `low_stock` are stated rather than left for the model to
    infer from `quantity`, so a reply cannot describe a size as available by
    misreading a zero.
    """

    size: str
    quantity: int
    in_stock: bool
    low_stock: bool = False


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
    description_available: bool = Field(
        default=True,
        description=(
            "False when the catalogue row holds a placeholder instead of a real "
            "description. Do not quote the description text when this is False."
        ),
    )


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
    """Per-size stock for one product, split into available and sold out.

    The split is done here rather than handed over as one flat list, so the
    model cannot report availability without also seeing what is gone.
    """

    product_id: str
    name: str
    price: float
    available_sizes: list[SizeStock]
    sold_out_sizes: list[SizeStock]
    total_stock: int
    units_in_stock: int
    sizes_available_count: int
    sizes_sold_out_count: int
    fully_sold_out: bool
    # Plain size letters, pre-joined, so a reply cannot drop one while
    # reformatting a list of objects.
    available_size_labels: list[str]
    sold_out_size_labels: list[str]
    low_stock_size_labels: list[str]
    stock_statement: str = Field(
        description=(
            "A ready-to-use sentence stating availability and what is sold "
            "out. Reuse or lightly rephrase it; do not contradict it."
        )
    )


class StockSummary(BaseModel):
    """How much stock exists, for one product or across the whole shop.

    Answers "how many do you have?" with counts straight from the inventory
    table, so the model never has to estimate a quantity.
    """

    scope: str = Field(description='Either "product" or "shop".')
    product_id: str | None = None
    name: str | None = None
    price: float | None = None
    units_in_stock: int = Field(description="Total units summed across sizes.")
    products_counted: int = Field(
        default=1, description="How many products this summary covers."
    )
    products_with_stock: int | None = None
    products_with_a_sold_out_size: int | None = None
    sizes_available_count: int | None = None
    sizes_sold_out_count: int | None = None
    available_size_labels: list[str] = Field(default_factory=list)
    sold_out_size_labels: list[str] = Field(default_factory=list)


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
    """The agent's reply plus the products the page should display.

    This is the contract between the agent and the frontend. `products` holds
    the cards the agent actually retrieved while answering — not what it
    mentioned in prose — so the page cannot show an item the agent never looked
    up, and cannot omit one it relied on.
    """

    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    matched_for: str | None = Field(
        default=None,
        description=(
            "The search phrase that produced these products, for labelling the "
            "results on the page. Null when the reply involved no search."
        ),
    )


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
        self.last_query: str | None = None

    def remember(self, products: list[ProductCard]) -> None:
        """Record products a tool returned, keeping first-seen order."""
        seen = {p.product_id for p in self.shown_products}
        for p in products:
            if p.product_id not in seen:
                self.shown_products.append(p)
                seen.add(p.product_id)
