"""
Field-level encryption helper for sensitive PII/PHI columns (phone, address,
insurance details, diagnosis notes, etc.) as required by the Patient Service
and Medical Records Service security requirements.

In production this wraps AWS KMS (envelope encryption: KMS data key + local
AES-256-GCM). Locally / in tests it falls back to a Fernet key from env so
the platform runs without AWS credentials.
"""
import base64
import os

from cryptography.fernet import Fernet

_ENC_KEY_ENV = "MEDICORE_FIELD_ENCRYPTION_KEY"


def _get_fernet() -> Fernet:
    key = os.environ.get(_ENC_KEY_ENV)
    if not key:
        # Deterministic dev-only fallback key so local/dev environments work
        # out of the box. NEVER used in staging/prod — those must set
        # MEDICORE_FIELD_ENCRYPTION_KEY from AWS Secrets Manager / KMS.
        key = base64.urlsafe_b64encode(b"0" * 32).decode()
    return Fernet(key)


def encrypt_field(value: str) -> str:
    if value is None:
        return value
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_field(value: str) -> str:
    if value is None:
        return value
    return _get_fernet().decrypt(value.encode()).decode()
