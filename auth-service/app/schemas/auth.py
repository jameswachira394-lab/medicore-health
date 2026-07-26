from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.PATIENT


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    mfa_enabled: bool

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class MfaVerifyRequest(BaseModel):
    code: str
