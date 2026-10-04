"""Password hashing and signed session tokens.

Passwords are never stored or logged in plaintext and are never recoverable from
what is stored. Only a salted PBKDF2-HMAC-SHA256 digest is written to the
database; verifying a login recomputes the digest and compares it in constant
time. There is no code path anywhere in this project that can turn a stored value
back into the original password.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time

log = logging.getLogger("campus_customs.security")

ALGORITHM = "pbkdf2_sha256"

# The seeded accounts were hashed with 120,000 iterations and store only
# `algorithm$salt$digest`, with no iteration count. New accounts record the
# count explicitly as `algorithm$iterations$salt$digest` so the cost can be
# raised later without locking anyone out.
LEGACY_ITERATIONS = 120_000
ITERATIONS = 240_000
SALT_BYTES = 16

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 200  # Bound the work an attacker can force us to do.


def hash_password(password: str) -> str:
    """Return a self-describing PBKDF2 hash. The input is never retained."""
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS
    ).hex()
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest}"


def _parse(stored: str) -> tuple[str, int, str, str] | None:
    parts = stored.split("$")
    if len(parts) == 3:
        algo, salt, digest = parts
        return algo, LEGACY_ITERATIONS, salt, digest
    if len(parts) == 4:
        algo, iterations, salt, digest = parts
        try:
            return algo, int(iterations), salt, digest
        except ValueError:
            return None
    return None


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check of a candidate password against a stored hash."""
    parsed = _parse(stored)
    if parsed is None:
        log.warning("Malformed password hash encountered; refusing login.")
        return False

    algo, iterations, salt, digest = parsed
    if algo != ALGORITHM or iterations < 1:
        log.warning("Unsupported password hash algorithm %r.", algo)
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return hmac.compare_digest(candidate, digest)


def needs_rehash(stored: str) -> bool:
    """True when a hash uses weaker parameters than we now issue."""
    parsed = _parse(stored)
    if parsed is None:
        return False
    _, iterations, _, _ = parsed
    return iterations < ITERATIONS


# A hash of a throwaway value, used to spend the same CPU time on a login for an
# unknown email as for a real one. Without this, response timing reveals which
# addresses have accounts.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def waste_time_like_a_real_verify() -> None:
    verify_password("not-the-password", _DUMMY_HASH)


# --------------------------------------------------------------------------
# Session tokens
# --------------------------------------------------------------------------
# A token is `base64url(payload_json).base64url(hmac_sha256)`. The signature is
# over the exact payload bytes, so the user id and expiry cannot be edited by the
# client. Tokens carry no secret beyond the user id.


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_session_token(user_id: int, secret: str, ttl_seconds: int) -> str:
    payload = json.dumps(
        {"sub": user_id, "exp": int(time.time()) + ttl_seconds},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    body = _b64e(payload)
    sig = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64e(sig)}"


def read_session_token(token: str, secret: str) -> int | None:
    """Return the user id if the token is authentic and unexpired, else None."""
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return None

    expected = hmac.new(
        secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256
    ).digest()
    try:
        if not hmac.compare_digest(_b64d(sig), expected):
            return None
        payload = json.loads(_b64d(body))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    if int(payload.get("exp", 0)) < time.time():
        return None
    sub = payload.get("sub")
    return int(sub) if isinstance(sub, int) else None
