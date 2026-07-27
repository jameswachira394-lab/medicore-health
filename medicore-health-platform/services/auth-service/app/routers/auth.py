from datetime import datetime, timedelta, timezone

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from shared_common.audit import write_audit_log
from shared_common.security import (
    create_token,
    decode_token,
    hash_password,
    make_current_user_dependency,
    verify_password,
)

from app.core.config import settings
from app.core.db import get_db
from app.models.user import RefreshToken, User
from app.schemas.auth import (
    LoginRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
get_current_user = make_current_user_dependency(settings.JWT_SECRET, settings.JWT_ALGORITHM)


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access = create_token(
        subject=user.id,
        role=user.role.value,
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        extra_claims={"email": user.email},
    )
    refresh = create_token(
        subject=user.id,
        role=user.role.value,
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )
    db.add(
        RefreshToken(
            user_id=user.id,
            token=refresh,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.flush()

    write_audit_log(
        actor_id=user.id,
        actor_role=user.role.value,
        action="REGISTER",
        resource_type="User",
        resource_id=user.id,
        source_ip=request.client.host if request.client else None,
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    ip = request.client.host if request.client else None

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        write_audit_log(
            actor_id=user.id, actor_role=user.role.value, action="LOGIN", resource_type="User",
            resource_id=user.id, source_ip=ip, outcome="LOCKED",
        )
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account temporarily locked")

    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.ACCOUNT_LOCKOUT_THRESHOLD:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
        write_audit_log(
            actor_id=user.id, actor_role=user.role.value, action="LOGIN", resource_type="User",
            resource_id=user.id, source_ip=ip, outcome="FAILED",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.mfa_enabled:
        if not payload.mfa_code or not pyotp.TOTP(user.mfa_secret).verify(payload.mfa_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing MFA code")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    user.failed_login_attempts = 0
    user.locked_until = None

    tokens = _issue_tokens(db, user)
    write_audit_log(
        actor_id=user.id, actor_role=user.role.value, action="LOGIN", resource_type="User",
        resource_id=user.id, source_ip=ip, outcome="SUCCESS",
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_row = db.query(RefreshToken).filter(RefreshToken.token == payload.refresh_token).first()
    if not token_row or token_row.revoked or token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    decoded = decode_token(payload.refresh_token, settings.JWT_SECRET, settings.JWT_ALGORITHM)
    if decoded.type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    user = db.query(User).filter(User.id == decoded.sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token_row.revoked = True
    return _issue_tokens(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_row = db.query(RefreshToken).filter(RefreshToken.token == payload.refresh_token).first()
    if token_row:
        token_row.revoked = True
    return None


@router.get("/me", response_model=UserOut)
def get_me(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    # Always return 202 regardless of whether the email exists, to avoid
    # leaking which emails are registered. A real implementation publishes
    # a "PasswordResetRequested" event consumed by the Notification Service.
    if user:
        reset_token = create_token(
            subject=user.id, role=user.role.value, secret=settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM, expires_delta=timedelta(minutes=30), token_type="password_reset",
        )
        # TODO: publish event to Notification Service / SNS with reset_token link
        _ = reset_token
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    decoded = decode_token(payload.token, settings.JWT_SECRET, settings.JWT_ALGORITHM)
    if decoded.type != "password_reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

    user = db.query(User).filter(User.id == decoded.sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = hash_password(payload.new_password)
    return {"message": "Password updated successfully"}


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def setup_mfa(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.sub).first()
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    otpauth_url = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="MediCore Health")
    return MfaSetupResponse(secret=secret, otpauth_url=otpauth_url)


@router.post("/mfa/verify", status_code=status.HTTP_200_OK)
def verify_mfa(payload: MfaVerifyRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.sub).first()
    if not user.mfa_secret or not pyotp.TOTP(user.mfa_secret).verify(payload.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    user.mfa_enabled = True
    return {"message": "MFA enabled"}
