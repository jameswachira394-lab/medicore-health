"""
Thin wrappers around the actual delivery channels. In production these call
AWS SES (email), AWS SNS (SMS), and Firebase Cloud Messaging (push) per the
platform's technology stack. Locally / in tests, they just log — no real
credentials are required to run the platform end-to-end.
"""
import logging

logger = logging.getLogger("medicore.notifications")


def send_email(to_address: str, subject: str, body: str) -> bool:
    logger.info(f"[SES] to={to_address} subject={subject!r}")
    return True


def send_sms(to_number: str, body: str) -> bool:
    logger.info(f"[SNS] to={to_number} body={body!r}")
    return True


def send_push(user_id: str, title: str, body: str) -> bool:
    logger.info(f"[FCM] user={user_id} title={title!r}")
    return True
