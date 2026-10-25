from typing import Any

import httpx
import jwt

from app.core.config import get_settings
from app.core.errors import AppError

_ALLOWED_ASYMMETRIC_ALGORITHMS = {"ES256", "RS256"}


async def verify_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")

        if settings.supabase_url:
            if algorithm not in _ALLOWED_ASYMMETRIC_ALGORITHMS:
                raise jwt.InvalidTokenError("Unsupported signing algorithm")
            jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
            signing_key = _get_signing_key(response.json(), header.get("kid"), algorithm)
            return jwt.decode(
                token,
                signing_key,
                algorithms=[algorithm],
                audience="authenticated",
            )

        if not settings.supabase_jwt_secret:
            raise AppError(500, "auth_not_configured", "Authentication is not configured.")
        if algorithm != "HS256":
            raise jwt.InvalidTokenError("Unsupported signing algorithm")
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except AppError:
        raise
    except (jwt.InvalidTokenError, httpx.HTTPError, ValueError, KeyError) as exc:
        raise AppError(401, "unauthorized", "The access token is invalid or expired.") from exc


def _get_signing_key(
    jwks: dict[str, Any], key_id: str | None, algorithm: str
) -> Any:
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == key_id:
            return jwt.PyJWK.from_dict(key_data, algorithm=algorithm).key
    raise jwt.InvalidTokenError("No matching signing key")
