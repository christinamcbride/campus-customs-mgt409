"""Registration, login, logout and the current-session lookup.

The session is carried in an HttpOnly cookie so that page scripts cannot read
it, which keeps a cross-site scripting bug from turning into account theft.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

import db
import security
from config import Settings, get_settings
from schemas import LoginRequest, RegisterRequest, User

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "cc_session"


def _set_session_cookie(response: Response, user_id: int, settings: Settings) -> None:
    token = security.create_session_token(
        user_id, settings.session_secret, settings.jwt_ttl_seconds
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.jwt_ttl_seconds,
        httponly=True,       # Not readable from JavaScript.
        samesite="lax",      # Not sent on cross-site POSTs.
        secure=settings.cookie_secure,
        path="/",
    )


def current_user_optional(
    request: Request,
    conn: sqlite3.Connection = Depends(db.get_connection),
    settings: Settings = Depends(get_settings),
) -> dict | None:
    """The signed-in user, or None. Use where anonymous access is allowed."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    user_id = security.read_session_token(token, settings.session_secret)
    if user_id is None:
        return None
    row = db.get_user_by_id(conn, user_id)
    return db.row_to_user(row) if row else None


def current_user(user: dict | None = Depends(current_user_optional)) -> dict:
    """The signed-in user, or 401. Use where an account is required."""
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "You need to be logged in to do that.",
            headers={"WWW-Authenticate": "cookie"},
        )
    return user


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(db.get_connection),
    settings: Settings = Depends(get_settings),
) -> User:
    email = payload.email.strip().lower()

    if db.get_user_by_email(conn, email) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An account with that email already exists. Try logging in instead.",
        )

    try:
        row = db.create_user(
            conn,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=email,
            password_hash=security.hash_password(payload.password),
        )
    except sqlite3.IntegrityError:
        # The UNIQUE index is the real guard; the check above is just a nicer
        # message. This catches a registration that raced us.
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An account with that email already exists. Try logging in instead.",
        ) from None

    user = db.row_to_user(row)
    _set_session_cookie(response, user["id"], settings)
    return User(**user)


@router.post("/login", response_model=User)
def login(
    payload: LoginRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(db.get_connection),
    settings: Settings = Depends(get_settings),
) -> User:
    row = db.get_user_by_email(conn, payload.email)

    if row is None:
        # Spend comparable time so the response does not reveal whether the
        # address has an account.
        security.waste_time_like_a_real_verify()
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Incorrect email or password."
        )

    stored = row["password_hash"]
    if not security.verify_password(payload.password, stored):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Incorrect email or password."
        )

    user = db.row_to_user(row)

    # The seeded accounts use a lower iteration count. Now that we have the
    # plaintext in memory for this request, upgrade the stored hash.
    if security.needs_rehash(stored):
        db.update_password_hash(
            conn, user["id"], security.hash_password(payload.password)
        )

    _set_session_cookie(response, user["id"], settings)
    return User(**user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    # Build the response we actually return, then clear the cookie on it.
    # Clearing it on an injected Response and returning a different object
    # silently drops the Set-Cookie header.
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@router.get("/me", response_model=User)
def me(user: dict = Depends(current_user)) -> User:
    return User(**user)
