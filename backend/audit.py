"""Append-only audit trail for agent-loop activity.

Every tool call and every end of an agent run is appended to
``output/audit_trail.json`` as one JSON object per line (JSON Lines). The file
is only ever opened in append mode: nothing in this project deletes, rewrites
or truncates it, so the record survives across runs and restarts.

JSON Lines rather than one big JSON array, because an array would have to be
re-read and rewritten on every entry — which is the opposite of append-only,
and loses the whole file if the process dies mid-write. Each line parses on its
own, and a reader can parse the file with one `json.loads` per line.

**Nothing sensitive is recorded.** Arguments and results are summarised, and a
redaction pass drops anything that looks like a password, key, token, hash, or
a customer's name or email. Users are identified only by their numeric id.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("campus_customs.audit")

AUDIT_PATH = Path(__file__).resolve().parents[1] / "output" / "audit_trail.json"

# Writes come from FastAPI's threadpool, so appends are serialised.
_LOCK = threading.Lock()

# How much of any single summarised value is kept.
MAX_VALUE_CHARS = 160

# Keys whose values are never written, at any depth.
REDACT_KEYS = {
    "password",
    "confirm_password",
    "password_hash",
    "token",
    "api_key",
    "portkey_api_key",
    "jwt_secret",
    "secret",
    "authorization",
    "cookie",
    "session",
    "email",
    "first_name",
    "last_name",
    "name",
}


def _clip(text: str) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= MAX_VALUE_CHARS else text[: MAX_VALUE_CHARS - 1] + "…"


def _summarise(value: Any, depth: int = 0) -> Any:
    """Shrink a value to something short, and drop anything sensitive."""
    if depth > 3:
        return "…"
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if str(k).lower() in REDACT_KEYS:
                out[str(k)] = "[redacted]"
            else:
                out[str(k)] = _summarise(v, depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        # Record how many, not every item.
        if len(value) > 3:
            return [_summarise(v, depth + 1) for v in value[:3]] + [
                f"…+{len(value) - 3} more"
            ]
        return [_summarise(v, depth + 1) for v in value]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _clip(value)


def _append(entry: dict[str, Any]) -> None:
    """Append one line. Never raises: auditing must not break a reply."""
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False, default=str)
        with _LOCK:
            # "a" only ever appends; the file is never truncated or rewritten.
            with AUDIT_PATH.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except Exception:
        log.exception("Could not write audit entry")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_tool_call(
    *,
    tool: str,
    arguments: dict[str, Any] | None = None,
    result: Any = None,
    user_id: int | None = None,
    error: str | None = None,
    duration_ms: int | None = None,
) -> None:
    """Record one tool invocation."""
    _append(
        {
            "time": _now(),
            "event": "tool_call",
            "tool": tool,
            "user_id": user_id,
            "arguments": _summarise(arguments or {}),
            "result": _summarise(result),
            "error": error,
            "duration_ms": duration_ms,
            "stop_reason": "error" if error else "ok",
        }
    )


def record_run(
    *,
    stop_reason: str,
    user_id: int | None = None,
    tool_calls: int | None = None,
    requests: int | None = None,
    products_returned: int | None = None,
    detail: str | None = None,
) -> None:
    """Record the end of an agent run and why the loop stopped."""
    _append(
        {
            "time": _now(),
            "event": "agent_run",
            "tool": None,
            "user_id": user_id,
            "tool_calls": tool_calls,
            "model_requests": requests,
            "products_returned": products_returned,
            "detail": _clip(detail) if detail else None,
            "stop_reason": stop_reason,
        }
    )


def summarise_result(value: Any) -> str:
    """A one-line description of what a tool returned, for the trail."""
    name = type(value).__name__
    for attr, label in (
        ("match_count", "matches"),
        ("units_in_stock", "units"),
        ("product_id", "product"),
    ):
        got = getattr(value, attr, None)
        if got is not None:
            return f"{name}({label}={got})"
    if isinstance(value, dict):
        return f"dict(keys={sorted(value)[:4]})"
    return name
