"""Catalogue browsing endpoints. All data comes from the SQLite database."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, Path as PathParam
from fastapi.responses import FileResponse

import db
from config import get_settings
from schemas import CategoryList, ProductDetail, ProductPage

router = APIRouter(prefix="/api", tags=["catalogue"])


@router.get("/products", response_model=ProductPage)
def list_products(
    conn: sqlite3.Connection = Depends(db.get_connection),
    search: str | None = Query(None, max_length=200),
    category: str | None = Query(None, max_length=50),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    in_stock_only: bool = Query(False),
    limit: int = Query(48, ge=1, le=120),
    offset: int = Query(0, ge=0),
) -> ProductPage:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(422, "min_price cannot be greater than max_price")

    items, total = db.list_products(
        conn,
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        limit=limit,
        offset=offset,
    )
    return ProductPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(
    product_id: str = PathParam(..., max_length=200),
    conn: sqlite3.Connection = Depends(db.get_connection),
) -> ProductDetail:
    product = db.get_product(conn, product_id)
    if product is None:
        raise HTTPException(404, f"No product with id '{product_id}'")
    product["sizes"] = db.get_inventory(conn, product_id)
    return ProductDetail(**product)


@router.get("/categories", response_model=CategoryList)
def list_categories(
    conn: sqlite3.Connection = Depends(db.get_connection),
) -> CategoryList:
    """Categories actually present in the catalogue, plus the real price range."""
    rows = conn.execute("SELECT garment_type, price FROM catalogue").fetchall()
    present = {db.categorize(r["garment_type"]) for r in rows}
    ordered = [c for c in db.CATEGORIES if c in present]
    if "Other" in present:
        ordered.append("Other")
    prices = [float(r["price"]) for r in rows] or [0.0]
    return CategoryList(
        categories=ordered, price_min=min(prices), price_max=max(prices)
    )


@router.get("/images/{filename}")
def get_image(filename: str = PathParam(..., max_length=200)) -> FileResponse:
    """Serve a product image by bare filename.

    The filename is resolved inside the products directory and rejected if it
    escapes it, so a crafted path cannot read arbitrary files.
    """
    products_dir = get_settings().products_dir.resolve()
    candidate = (products_dir / filename).resolve()
    if candidate.parent != products_dir or not candidate.is_file():
        raise HTTPException(404, "Image not found")
    return FileResponse(candidate, media_type="image/jpeg")
