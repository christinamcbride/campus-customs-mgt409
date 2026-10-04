"""Entry point for the Campus Customs API.

The implementation lives in ``backend/app`` so that routers, database access and
the agent can grow in separate modules. This module re-exports the application
so it can be served from the path named in the assignment:

    uvicorn backend.main:app --reload --port 8787
"""

from .app.main import app

__all__ = ["app"]
