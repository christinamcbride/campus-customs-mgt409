"""SQLite access layer.

The database is the single source of truth for products, prices and stock.
Nothing in this module invents data: every value returned comes from a row.
"""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from config import get_settings

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# `catalogue.garment_type` is free text and inconsistent ("hoodie" vs
# "pullover hoodie", "T-shirt" vs "t-shirt"). We bucket it for filtering
# instead of editing the database, which ships read-only with the assignment.
CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Quarter-Zips", ("quarter-zip",)),
    ("Jackets", ("jacket",)),
    ("Hoodies", ("hood",)),
    ("Crewnecks", ("crewneck", "mockneck", "raglan")),
    ("Long Sleeve", ("long-sleeve", "performance")),
    ("T-Shirts", ("t-shirt", "tee")),
]
CATEGORIES = [name for name, _ in CATEGORY_RULES]


def categorize(garment_type: str) -> str:
    gt = (garment_type or "").lower()
    for name, needles in CATEGORY_RULES:
        if any(n in gt for n in needles):
            return name
    return "Other"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a connection to the catalogue database."""
    settings = get_settings()
    path = settings.database_path
    if not path.exists():
        raise FileNotFoundError(
            f"Database not found at {path}. The assignment data folder "
            "(data/campus_customs.db) is required and is not committed to git."
        )
    # FastAPI runs sync endpoints in a threadpool and may close a dependency on a
    # different thread than the one that opened it, so the same-thread check has
    # to be off. Each request still gets its own connection; none are shared.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def get_connection() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency wrapper around :func:`connect`."""
    with connect() as conn:
        yield conn


def _loads(raw: Any) -> list[str]:
    """Parse a JSON-array text column, tolerating malformed rows."""
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return [part.strip() for part in str(raw).split(",") if part.strip()]
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def row_to_product(row: sqlite3.Row) -> dict[str, Any]:
    keys = row.keys()
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": categorize(row["garment_type"]),
        "description": row["description"],
        "colors": _loads(row["colors"]),
        "search_tags": _loads(row["search_tags"]),
        "image_file_path": row["image_file_path"],
        "image_url": f"/api/images/{row['image_file_path'].split('/')[-1]}",
        "price": round(float(row["price"]), 2),
        "total_stock": int(row["total_stock"]) if "total_stock" in keys else None,
    }


_BASE_SELECT = """
    SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
    FROM catalogue c
    LEFT JOIN inventory i ON i.product_id = c.product_id
"""


def list_products(
    conn: sqlite3.Connection,
    *,
    search: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
    limit: int = 48,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Return (products, total_matching). Filtering happens in SQL where it can."""
    where: list[str] = []
    params: list[Any] = []

    if search:
        # Match the user's words against every text column, all terms required.
        for term in [t for t in search.split() if t][:6]:
            where.append(
                "(c.name LIKE ? OR c.description LIKE ? OR c.search_tags LIKE ?"
                " OR c.colors LIKE ? OR c.garment_type LIKE ?)"
            )
            params.extend([f"%{term}%"] * 5)
    if min_price is not None:
        where.append("c.price >= ?")
        params.append(min_price)
    if max_price is not None:
        where.append("c.price <= ?")
        params.append(max_price)

    sql = _BASE_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY c.product_id"
    if in_stock_only:
        sql += " HAVING total_stock > 0"

    rows = conn.execute(sql, params).fetchall()
    products = [row_to_product(r) for r in rows]

    # Category is derived in Python, so it is applied after the SQL pass.
    if category and category.lower() != "all":
        wanted = category.strip().lower()
        products = [p for p in products if p["category"].lower() == wanted]

    products.sort(key=lambda p: p["name"].lower())
    total = len(products)
    return products[offset : offset + limit], total


def get_product(conn: sqlite3.Connection, product_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        _BASE_SELECT + " WHERE c.product_id = ? GROUP BY c.product_id",
        (product_id,),
    ).fetchone()
    return row_to_product(row) if row else None


def get_inventory(conn: sqlite3.Connection, product_id: str) -> list[dict[str, Any]]:
    """Stock per size, ordered XS -> XXL, including sizes with zero quantity."""
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?",
        (product_id,),
    ).fetchall()
    by_size = {r["size"].upper(): int(r["quantity"]) for r in rows}
    ordered = [
        {"size": s, "quantity": by_size[s], "in_stock": by_size[s] > 0}
        for s in SIZE_ORDER
        if s in by_size
    ]
    # Any non-standard sizes still get reported rather than silently dropped.
    extras = sorted(k for k in by_size if k not in SIZE_ORDER)
    ordered.extend(
        {"size": s, "quantity": by_size[s], "in_stock": by_size[s] > 0} for s in extras
    )
    return ordered


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------
# Only non-sensitive columns are ever selected into a response. `password_hash`
# is read solely inside the login check and never returned by any endpoint.

USER_PUBLIC_COLUMNS = "id, name, email, first_name, last_name, created_at"


def get_user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    """Look up a user for login. Email comparison is case-insensitive."""
    return conn.execute(
        "SELECT id, name, email, first_name, last_name, created_at, password_hash "
        "FROM users WHERE email = ? COLLATE NOCASE",
        (email.strip(),),
    ).fetchone()


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return conn.execute(
        f"SELECT {USER_PUBLIC_COLUMNS} FROM users WHERE id = ?", (user_id,)
    ).fetchone()


def create_user(
    conn: sqlite3.Connection,
    *,
    first_name: str,
    last_name: str,
    email: str,
    password_hash: str,
) -> sqlite3.Row:
    """Insert a new account. Raises sqlite3.IntegrityError if the email exists."""
    full_name = f"{first_name} {last_name}".strip()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, first_name, last_name) "
        "VALUES (?, ?, ?, ?, ?)",
        (full_name, email, password_hash, first_name, last_name),
    )
    conn.commit()
    row = get_user_by_id(conn, int(cur.lastrowid))
    assert row is not None  # Just inserted.
    return row


def update_password_hash(conn: sqlite3.Connection, user_id: int, new_hash: str) -> None:
    """Upgrade a stored hash in place after a successful login."""
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()


def row_to_user(row: sqlite3.Row) -> dict[str, Any]:
    """Public view of an account. Never includes the password hash."""
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "created_at": row["created_at"],
    }
