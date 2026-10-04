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


# --------------------------------------------------------------------------
# Accounts
# --------------------------------------------------------------------------

from pydantic import EmailStr, field_validator  # noqa: E402

from .security import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH  # noqa: E402


class User(BaseModel):
    """Public account details. Deliberately has no password field of any kind."""

    id: int
    name: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    created_at: str


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    confirm_password: str = Field(max_length=MAX_PASSWORD_LENGTH)

    @field_validator("first_name", "last_name")
    @classmethod
    def _trim(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("cannot be blank")
        return trimmed

    @field_validator("confirm_password")
    @classmethod
    def _match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("passwords do not match")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)
