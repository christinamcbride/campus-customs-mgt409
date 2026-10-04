"""Tools the shopping assistant can call.

Every tool reads the live SQLite database and returns a typed result. None of
them can invent a product: if a lookup finds nothing, the tool says so
explicitly so the model has a concrete "not found" to report rather than a
silence it might fill in.
"""

from __future__ import annotations

import logging

from pydantic_ai import RunContext

import db
from models import (
    InventoryResult,
    LookupFailure,
    ProductCard,
    ProductCardDetail,
    ProductSearchResult,
    ShopContext,
    SizeStock,
)

log = logging.getLogger("campus_customs.tools")

MAX_RESULTS = 8

# Catalogue colour names are inconsistent, so a shopper's word has to match a
# family of spellings. Keys are what people type; values are substrings to match.
COLOR_SYNONYMS: dict[str, tuple[str, ...]] = {
    "navy": ("navy",),
    "blue": ("blue", "navy"),
    "grey": ("gray", "grey"),
    "gray": ("gray", "grey"),
    "charcoal": ("charcoal",),
    "white": ("white",),
    "black": ("black",),
    "red": ("red", "crimson"),
    "green": ("green",),
    "yellow": ("yellow", "gold"),
    "gold": ("gold", "yellow"),
    "pink": ("pink",),
    "purple": ("purple",),
    "orange": ("orange",),
}


def _card(row: dict) -> ProductCard:
    return ProductCard(**{k: v for k, v in row.items() if k != "image_file_path"})


def register_tools(agent) -> None:
    """Attach every shop tool to the agent."""

    @agent.tool
    def search_products(
        ctx: RunContext[ShopContext],
        query: str,
        category: str | None = None,
        color: str | None = None,
        max_price: float | None = None,
        min_price: float | None = None,
        in_stock_only: bool = False,
    ) -> ProductSearchResult:
        """Search the Campus Customs catalogue.

        Use this for any question about what the shop sells. Call it before
        naming a product, a price, or a colour.

        Args:
            query: What the shopper is looking for, in their own words, e.g.
                "navy hoodie", "bulldog t-shirt", "Morse college". Pass an empty
                string to browse by the filters alone.
            category: One of Quarter-Zips, Jackets, Hoodies, Crewnecks,
                Long Sleeve, T-Shirts. Omit unless the shopper named a type.
            color: A colour the shopper asked for. Matching handles the
                catalogue's inconsistent spellings.
            max_price: Only products at or below this price.
            min_price: Only products at or above this price.
            in_stock_only: True to exclude products with no stock in any size.

        Returns:
            Matching products, or an empty list with a note when nothing matched.
        """
        rows, _ = db.list_products(
            ctx.deps.conn,
            search=query or None,
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            limit=120,
            offset=0,
        )

        if color:
            wanted = COLOR_SYNONYMS.get(color.strip().lower(), (color.strip().lower(),))
            rows = [
                r for r in rows
                if any(w in c.lower() for c in r["colors"] for w in wanted)
            ]

        cards = [_card(r) for r in rows[:MAX_RESULTS]]
        ctx.deps.remember(cards)

        if not cards:
            tried = [f"query={query!r}"]
            if category:
                tried.append(f"category={category}")
            if color:
                tried.append(f"color={color}")
            if min_price is not None or max_price is not None:
                tried.append(f"price={min_price}-{max_price}")
            if in_stock_only:
                tried.append("in stock only")
            return ProductSearchResult(
                query=query,
                match_count=0,
                matches=[],
                note=(
                    "No products in the catalogue matched "
                    + ", ".join(tried)
                    + ". Campus Customs does not currently carry this. Tell the "
                    "shopper plainly rather than suggesting something unverified."
                ),
            )

        return ProductSearchResult(
            query=query, match_count=len(rows), matches=cards
        )

    @agent.tool
    def get_product_details(
        ctx: RunContext[ShopContext], product_id: str
    ) -> ProductCardDetail | LookupFailure:
        """Full details for one product, including stock for every size.

        Args:
            product_id: The product's id, e.g. "morse-1-4-zip". Get this from a
                prior search rather than guessing it.
        """
        row = db.get_product(ctx.deps.conn, product_id)
        if row is None:
            return LookupFailure(
                reason=(
                    f"No product with id {product_id!r} exists in the catalogue. "
                    "Do not describe this product; search for it by name instead."
                ),
                product_id=product_id,
            )
        sizes = [SizeStock(**s) for s in db.get_inventory(ctx.deps.conn, product_id)]
        detail = ProductCardDetail(
            **{k: v for k, v in row.items() if k != "image_file_path"}, sizes=sizes
        )
        ctx.deps.remember([ProductCard(**detail.model_dump(exclude={"sizes"}))])
        return detail

    @agent.tool
    def check_size_availability(
        ctx: RunContext[ShopContext], product_id: str
    ) -> InventoryResult | LookupFailure:
        """Which sizes of a product are in stock and which are sold out.

        Use this for any question about sizes or availability. Report both the
        available and the sold-out sizes; do not answer with a bare yes or no.

        Args:
            product_id: The product's id, e.g. "morse-1-4-zip".
        """
        row = db.get_product(ctx.deps.conn, product_id)
        if row is None:
            return LookupFailure(
                reason=(
                    f"No product with id {product_id!r} exists, so there is no "
                    "stock to report. Search for the product by name first."
                ),
                product_id=product_id,
            )

        sizes = [SizeStock(**s) for s in db.get_inventory(ctx.deps.conn, product_id)]
        ctx.deps.remember([_card(row)])
        return InventoryResult(
            product_id=row["product_id"],
            name=row["name"],
            price=row["price"],
            available_sizes=[s for s in sizes if s.in_stock],
            sold_out_sizes=[s for s in sizes if not s.in_stock],
            total_stock=sum(s.quantity for s in sizes),
        )

    @agent.tool
    def list_categories(ctx: RunContext[ShopContext]) -> dict[str, object]:
        """The product categories the shop carries, and the real price range.

        Use this when a shopper asks what kinds of things the shop sells, or
        before claiming the shop does or does not carry a category.
        """
        rows = ctx.deps.conn.execute(
            "SELECT garment_type, price FROM catalogue"
        ).fetchall()
        present = {db.categorize(r["garment_type"]) for r in rows}
        prices = [float(r["price"]) for r in rows] or [0.0]
        return {
            "categories": [c for c in db.CATEGORIES if c in present],
            "price_min": min(prices),
            "price_max": max(prices),
            "product_count": len(rows),
        }
