"""
API Key authentication and authorization.

Implements FastAPI HTTPBearer authentication scheme to protect endpoints.
API keys are validated using constant-time comparison to prevent timing attacks.
"""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings


# HTTPBearer security scheme for extracting API key from Authorization header
bearer_scheme = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Verify API key from Authorization header using Bearer token scheme.

    Uses constant-time comparison (secrets.compare_digest) to prevent
    timing attacks that could reveal valid key prefixes.

    Args:
        credentials: Bearer token from Authorization header
        settings: Application settings with configured API key

    Returns:
        The verified API key string

    Raises:
        HTTPException 401 if credentials missing or invalid
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
        )

    if not secrets.compare_digest(credentials.credentials, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return credentials.credentials
