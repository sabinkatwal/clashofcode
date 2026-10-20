import hashlib
import json
import os
import re
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.database import AsyncSessionLocal, get_db
from app.models import User

from app.schemas import (
    DeveloperLoginSchema,
    UserCreate,
    LoginSchema
)

from app.auth import (
    get_developer_email,
    hash_password,
    is_developer_user,
    normalize_developer_username,
    verify_password,
    create_access_token
)
from app.google_oauth import (
    OAUTH_STATE_MAX_AGE,
    build_google_authorization_url,
    create_oauth_values,
    exchange_code_for_tokens,
    google_is_configured,
    google_redirect_uri,
    validate_google_id_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://clashofcode-three.vercel.app").rstrip("/")


def _auth_response(user: User) -> dict:
    user_role = user.role or ("developer" if is_developer_user(user.username) else "user")
    return {
        "access_token": create_access_token({"sub": user.username, "role": user_role}),
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "role": user_role,
        },
    }


def _google_username(email: str, subject: str, existing: set[str]) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]", "_", email.split("@", 1)[0]).strip("_").lower() or "google_user"
    base = base[:40]
    candidate = base
    if candidate in existing:
        suffix = hashlib.sha256(subject.encode()).hexdigest()[:8]
        candidate = f"{base[:31]}_g_{suffix}"
    return candidate[:50]


def _oauth_error_redirect(message: str) -> RedirectResponse:
    return RedirectResponse(
        f"{FRONTEND_URL}/login?{urlencode({'error': message})}",
        status_code=303,
    )


@router.get("/google/login")
async def google_login():
    if not google_is_configured():
        raise HTTPException(status_code=503, detail="Google login is not configured")

    state, nonce = create_oauth_values()
    response = RedirectResponse(build_google_authorization_url(state, nonce), status_code=303)
    response.set_cookie(
        "google_oauth_state",
        json.dumps({"state": state, "nonce": nonce}),
        max_age=OAUTH_STATE_MAX_AGE,
        httponly=True,
        secure=google_redirect_uri().startswith("https://"),
        samesite="lax",
    )
    return response


@router.get("/google/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None):
    oauth_cookie = request.cookies.get("google_oauth_state")
    if not code or not state or not oauth_cookie:
        return _oauth_error_redirect("Google login was cancelled or expired.")

    try:
        stored = json.loads(oauth_cookie)
    except json.JSONDecodeError:
        return _oauth_error_redirect("Google login could not be verified.")

    stored_state = stored.get("state")
    stored_nonce = stored.get("nonce")
    if (
        not isinstance(stored_state, str)
        or not isinstance(stored_nonce, str)
        or not secrets.compare_digest(state, stored_state)
    ):
        return _oauth_error_redirect("Google login could not be verified.")

    try:
        tokens = await exchange_code_for_tokens(code)
        id_token = tokens.get("id_token")
        if not id_token:
            raise ValueError("Google did not return an ID token")
        claims = await validate_google_id_token(id_token, stored_nonce)
    except (httpx.HTTPError, ValueError, KeyError):
        return _oauth_error_redirect("Google login could not be completed.")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(func.lower(User.email) == claims["email"].lower())
        )
        user = result.scalar_one_or_none()
        if user is None:
            usernames = await db.execute(select(User.username))
            existing_usernames = {username for (username,) in usernames}
            user = User(
                username=_google_username(claims["email"], claims["sub"], existing_usernames),
                email=claims["email"].lower(),
                hashed_pw=hash_password(secrets.token_urlsafe(32)),
                role="user",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        auth_data = _auth_response(user)

    fragment = urlencode({
            'access_token': auth_data['access_token'],
            'token_type': auth_data['token_type'],
            'user': json.dumps(auth_data['user'], separators=(',', ':')),
        })
    response = RedirectResponse(f"{FRONTEND_URL}/auth/callback#{fragment}", status_code=303)
    response.delete_cookie("google_oauth_state")
    return response

# REGISTER
@router.post("/register")
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(User).where(
            or_(func.lower(User.username) == data.username.lower(), func.lower(User.email) == data.email.lower())
        )
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    user = User(
        username=data.username,
        email=data.email,
        hashed_pw=hash_password(data.password),
        role="developer" if is_developer_user(data.username) else "user",
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.username, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }


# LOGIN
@router.post("/login")
async def login(data: LoginSchema):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(
                or_(func.lower(User.username) == data.username.lower(), func.lower(User.email) == data.username.lower())
            )
        )

        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or email"
            )

        if not verify_password(
            data.password,
            user.hashed_pw
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid password"
            )

        user_role = user.role or ("developer" if is_developer_user(user.username) else "user")
        token = create_access_token(
            {"sub": user.username, "role": user_role}
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "email": user.email,
                "role": user_role,
            },
        }


@router.post("/developer-login")
async def developer_login(data: DeveloperLoginSchema):
    username = normalize_developer_username(data.username)
    if not is_developer_user(username):
        raise HTTPException(
            status_code=401,
            detail="Developer access denied.",
        )

    token = create_access_token({"sub": username, "role": "developer"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": username,
            "email": get_developer_email(username),
            "role": "developer",
        },
    }
