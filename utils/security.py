from __future__ import annotations

import re
from typing import Any, Dict, Iterable

SENSITIVE_FIELD_NAMES = {
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "password",
    "secret",
    "secret_key",
    "cookie",
    "set_cookie",
}

PII_FIELD_NAMES = {
    "phone",
    "telephone",
    "mobile",
    "email",
    "contact",
    "qq",
    "wechat",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(x-goog-api-key\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)([^\s,;]+)"),
    re.compile(r"(?i)(token\s*[:=]\s*)([^\s,;]+)"),
]

PHONE_PATTERN = re.compile(r"(?<!\d)(1\d{10})(?!\d)")
EMAIL_PATTERN = re.compile(r"([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def mask_secret(secret: str) -> str:
    value = str(secret or "").strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def redact_sensitive_text(text: Any, extra_secrets: Iterable[str] | None = None) -> str:
    value = str(text or "")
    if not value:
        return ""

    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)

    redacted = PHONE_PATTERN.sub(lambda match: f"{match.group(1)[:3]}****{match.group(1)[-4:]}", redacted)
    redacted = EMAIL_PATTERN.sub(lambda match: f"{match.group(1)}***{match.group(2)}", redacted)

    for secret in extra_secrets or []:
        token = str(secret or "").strip()
        if token:
            redacted = redacted.replace(token, "[REDACTED]")

    return redacted


def sanitize_user_context(user_context: Dict[str, Any] | None) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {}
    for key, value in (user_context or {}).items():
        lowered = key.lower()
        if lowered in SENSITIVE_FIELD_NAMES:
            sanitized[key] = "[REDACTED]"
            continue
        if lowered in PII_FIELD_NAMES:
            sanitized[key] = mask_secret(str(value))
            continue
        if isinstance(value, dict):
            sanitized[key] = sanitize_user_context(value)
            continue
        if isinstance(value, list):
            sanitized[key] = [
                sanitize_user_context(item) if isinstance(item, dict) else redact_sensitive_text(item)
                for item in value
            ]
            continue
        sanitized[key] = redact_sensitive_text(value)
    return sanitized

