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
    StockSummary,
)

log = logging.getLogger("campus_customs.tools")

MAX_RESULTS = 8

# At or below this many units a size is worth flagging as nearly gone.
LOW_STOCK_THRESHOLD = 3

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


# A few catalogue rows hold a generated placeholder instead of a real
# description. Relaying that text to a shopper would be worse than saying
# nothing, so it is replaced and flagged.
STUB_MARKERS = ("vision blocked", "filename-based stub")


def _clean(row: dict) -> dict:
    data = {k: v for k, v in row.items() if k != "image_file_path"}
    description = str(data.get("description", ""))
    if any(marker in description.lower() for marker in STUB_MARKERS):
        data["description"] = (
            "No written description is on file for this item. Describe it only "
            "by its name, category and price."
        )
        data["description_available"] = False
    return data


def _card(row: dict) -> ProductCard:
    return ProductCard(**_clean(row))


def _sizes(conn, product_id: str) -> list[SizeStock]:
    """Per-size stock with the low-stock flag applied consistently."""
    return [
        SizeStock(
            size=s["size"],
            quantity=s["quantity"],
            in_stock=s["in_stock"],
            low_stock=0 < s["quantity"] <= LOW_STOCK_THRESHOLD,
        )
        for s in db.get_inventory(conn, product_id)
    ]


def _stock_statement(name: str, available: list[SizeStock], sold_out: list[SizeStock]) -> str:
    """One sentence naming what is in stock and what is not."""
    if not available:
        return f"{name} is sold out in every size right now."
    got = ", ".join(s.size for s in available)
    line = f"{name} is in stock in {got}."
    if sold_out:
        line += f" Sold out in {', '.join(s.size for s in sold_out)}."
    low = [s for s in available if s.low_stock]
    if low:
        line += " Only " + ", ".join(f"{s.quantity} left in {s.size}" for s in low) + "."
    return line


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
        if cards:
            # Label for the results shown on the page. Prefer the shopper's own
            # words; fall back to the filter when they only named a category.
            ctx.deps.last_query = query.strip() or category or color or "your search"

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
        sizes = _sizes(ctx.deps.conn, product_id)
        detail = ProductCardDetail(**_clean(row), sizes=sizes)
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

        sizes = _sizes(ctx.deps.conn, product_id)
        available = [s for s in sizes if s.in_stock]
        sold_out = [s for s in sizes if not s.in_stock]
        units = sum(s.quantity for s in sizes)
        ctx.deps.remember([_card(row)])
        return InventoryResult(
            product_id=row["product_id"],
            name=row["name"],
            price=row["price"],
            available_sizes=available,
            sold_out_sizes=sold_out,
            total_stock=units,
            units_in_stock=units,
            sizes_available_count=len(available),
            sizes_sold_out_count=len(sold_out),
            fully_sold_out=units == 0,
            available_size_labels=[s.size for s in available],
            sold_out_size_labels=[s.size for s in sold_out],
            low_stock_size_labels=[s.size for s in available if s.low_stock],
            stock_statement=_stock_statement(row["name"], available, sold_out),
        )

    @agent.tool
    def get_stock_summary(
        ctx: RunContext[ShopContext], product_id: str | None = None
    ) -> StockSummary | LookupFailure:
        """How many units are in stock, as counts from the inventory table.

        Use this when the shopper asks "how many do you have", "how much stock
        is left", or how much of the shop is in stock. Never estimate a
        quantity; this returns the real numbers.

        Args:
            product_id: A product id for one item's totals. Omit for a
                shop-wide summary across the whole catalogue.
        """
        conn = ctx.deps.conn

        if product_id:
            row = db.get_product(conn, product_id)
            if row is None:
                return LookupFailure(
                    reason=(
                        f"No product with id {product_id!r} exists, so there is "
                        "no stock to count. Search for it by name first."
                    ),
                    product_id=product_id,
                )
            sizes = _sizes(conn, product_id)
            available = [s for s in sizes if s.in_stock]
            sold_out = [s for s in sizes if not s.in_stock]
            ctx.deps.remember([_card(row)])
            return StockSummary(
                scope="product",
                product_id=row["product_id"],
                name=row["name"],
                price=row["price"],
                units_in_stock=sum(s.quantity for s in sizes),
                products_counted=1,
                sizes_available_count=len(available),
                sizes_sold_out_count=len(sold_out),
                available_size_labels=[s.size for s in available],
                sold_out_size_labels=[s.size for s in sold_out],
            )

        totals = conn.execute(
            "SELECT COUNT(DISTINCT c.product_id) AS products, "
            "       COALESCE(SUM(i.quantity), 0) AS units "
            "FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id"
        ).fetchone()
        with_stock = conn.execute(
            "SELECT COUNT(*) AS n FROM (SELECT product_id FROM inventory "
            "GROUP BY product_id HAVING SUM(quantity) > 0)"
        ).fetchone()
        with_gap = conn.execute(
            "SELECT COUNT(DISTINCT product_id) AS n FROM inventory WHERE quantity = 0"
        ).fetchone()
        return StockSummary(
            scope="shop",
            units_in_stock=int(totals["units"]),
            products_counted=int(totals["products"]),
            products_with_stock=int(with_stock["n"]),
            products_with_a_sold_out_size=int(with_gap["n"]),
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
