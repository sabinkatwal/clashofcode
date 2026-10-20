import os
import secrets
import time
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt


GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
OAUTH_STATE_MAX_AGE = 600


def google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


def google_client_secret() -> str:
    return os.getenv("GOOGLE_CLIENT_SECRET", "").strip()


def google_redirect_uri() -> str:
    return os.getenv("GOOGLE_REDIRECT_URI", "").strip()


def google_is_configured() -> bool:
    return all((google_client_id(), google_client_secret(), google_redirect_uri()))


def create_oauth_values() -> tuple[str, str]:
    return secrets.token_urlsafe(32), secrets.token_urlsafe(32)


def build_google_authorization_url(state: str, nonce: str) -> str:
    params = {
        'client_id': google_client_id(),
        'redirect_uri': google_redirect_uri(),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'nonce': nonce,
        'prompt': 'select_account',
    }
    return f"{GOOGLE_AUTHORIZATION_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": google_client_id(),
                "client_secret": google_client_secret(),
                "redirect_uri": google_redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
    response.raise_for_status()
    return response.json()


_jwks_cache: dict | None = None
_jwks_cache_expires_at = 0.0


async def _google_jwks() -> dict:
    global _jwks_cache, _jwks_cache_expires_at
    if _jwks_cache and time.monotonic() < _jwks_cache_expires_at:
        return _jwks_cache

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(GOOGLE_JWKS_URL)
    response.raise_for_status()
    cache_control = response.headers.get("cache-control", "")
    max_age = next(
        (int(part.split("=", 1)[1]) for part in cache_control.split(",")
         if part.strip().startswith("max-age=")),
        3600,
    )
    _jwks_cache = response.json()
    _jwks_cache_expires_at = time.monotonic() + max_age
    return _jwks_cache


async def validate_google_id_token(id_token: str, expected_nonce: str) -> dict:
    try:
        header = jwt.get_unverified_header(id_token)
        claims = jwt.get_unverified_claims(id_token)
    except JWTError as exc:
        raise ValueError("Google returned an invalid ID token") from exc

    if header.get("alg") != "RS256" or not header.get("kid"):
        raise ValueError("Google returned an unsupported ID token")
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise ValueError("Google ID token has an invalid issuer")

    key = next(
        (key for key in (await _google_jwks()).get("keys", [])
         if key.get("kid") == header["kid"]),
        None,
    )
    if key is None:
        raise ValueError("Google signing key is unavailable")

    try:
        verified_claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=google_client_id(),
            issuer=claims["iss"],
        )
    except JWTError as exc:
        raise ValueError("Google ID token validation failed") from exc

    if verified_claims.get("nonce") != expected_nonce:
        raise ValueError("Google ID token nonce validation failed")
    if not verified_claims.get("email_verified"):
        raise ValueError("Google account email is not verified")
    if not verified_claims.get("sub") or not verified_claims.get("email"):
        raise ValueError("Google ID token is missing required claims")
    return verified_claims
