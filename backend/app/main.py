"""Campus Customs API."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import catalogue

log = logging.getLogger("campus_customs")

app = FastAPI(
    title="Campus Customs API",
    description="Catalogue, accounts and shopping assistant for Campus Customs.",
    version="0.1.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalogue.router)


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
        "ai_configured": s.ai_configured,
    }
