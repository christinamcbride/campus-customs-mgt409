"""Response/request models. These validate what leaves and enters the API."""

from pydantic import BaseModel, Field


class SizeStock(BaseModel):
    size: str
    quantity: int
    in_stock: bool


class Product(BaseModel):
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


class ProductDetail(Product):
    sizes: list[SizeStock]


class ProductPage(BaseModel):
    items: list[Product]
    total: int
    limit: int
    offset: int


class CategoryList(BaseModel):
    categories: list[str]
    price_min: float
    price_max: float
