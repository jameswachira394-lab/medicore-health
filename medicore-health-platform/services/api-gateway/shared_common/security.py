"""
Shared security primitives: password hashing, JWT encode/decode, and a
FastAPI dependency for extracting + validating the current user from a
Bearer token. Used by every service to enforce authentication; role checks
are layered on top via `require_roles`.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class TokenPayload(BaseModel):
    sub: str  # user id
    role: str
    email: Optional[str] = None
    type: str = "access"  # access | refresh
    exp: Optional[int] = None


def create_token(
    subject: str,
    role: str,
    secret: str,
    algorithm: str,
    expires_delta: timedelta,
    token_type: str = "access",
    extra_claims: Optional[dict] = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, secret: str, algorithm: str) -> TokenPayload:
    try:
        data = jwt.decode(token, secret, algorithms=[algorithm])
        return TokenPayload(**data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def make_current_user_dependency(secret: str, algorithm: str):
    """
    Returns a FastAPI dependency `get_current_user` configured with this
    service's JWT secret/algorithm, so every microservice can validate
    tokens issued by the Authentication Service without importing it directly.
    """

    def _get_current_user(
        creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    ) -> TokenPayload:
        if creds is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        payload = decode_token(creds.credentials, secret, algorithm)
        if payload.type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")
        return payload

    return _get_current_user


def make_require_roles(current_user_dependency):
    """
    Dependency-factory-factory: bind to a service's `get_current_user`
    dependency once, then produce `require_roles("doctor", "nurse")` style
    dependencies for individual routes.
    """

    def require_roles(*allowed_roles: str):
        def _check(current_user: TokenPayload = Depends(current_user_dependency)) -> TokenPayload:
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{current_user.role}' is not permitted to perform this action",
                )
            return current_user

        return _check

    return require_roles
