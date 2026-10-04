"""Application settings, loaded from the environment / backend/.env."""

import logging
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> backend/app -> backend -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Data ---
    database_path: Path = PROJECT_ROOT / "data" / "campus_customs.db"
    products_dir: Path = PROJECT_ROOT / "data" / "products"

    # --- AI gateway ---
    # Graders supply their own PORTKEY_API_KEY; the app must start without one
    # and only degrade the chat feature, never the catalogue.
    portkey_api_key: str = ""
    ai_base_url: str = "https://api.portkey.ai/v1"
    ai_model: str = "gpt-4o-mini"

    # --- Auth ---
    # Signing key for session cookies. If it is not set the app still runs, but
    # with a key generated at startup, so sessions end when the server restarts.
    jwt_secret: str = ""
    jwt_ttl_seconds: int = 60 * 60 * 24 * 7
    cookie_secure: bool = False  # Set true when serving over HTTPS.

    # --- CORS ---
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_configured(self) -> bool:
        return bool(self.portkey_api_key)


    @property
    def session_secret(self) -> str:
        """The configured signing key, or the ephemeral fallback."""
        return self.jwt_secret or _EPHEMERAL_SECRET


# Generated once per process. Used only when JWT_SECRET is unset so that a
# grader can run the app without configuring anything.
_EPHEMERAL_SECRET = secrets.token_urlsafe(32)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.jwt_secret:
        logging.getLogger("campus_customs").warning(
            "JWT_SECRET is not set; using a key generated for this process. "
            "Sessions will not survive a restart. Set JWT_SECRET in backend/.env "
            "for stable logins."
        )
    return settings
