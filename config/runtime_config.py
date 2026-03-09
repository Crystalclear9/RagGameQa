"""运行时 Provider 配置管理。"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, Optional

from config.settings import Settings, settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
SUPPORTED_PROVIDERS = {"mock", "gemini", "claude"}

PROVIDER_MODEL_FIELD = {
    "mock": None,
    "gemini": "GEMINI_MODEL",
    "claude": "CLAUDE_MODEL",
}

PROVIDER_KEY_FIELD = {
    "mock": None,
    "gemini": "GEMINI_API_KEY",
    "claude": "CLAUDE_API_KEY",
}

PROVIDER_DEFAULT_MODEL = {
    "mock": "mock-llm-v1",
    "gemini": settings.GEMINI_MODEL,
    "claude": settings.CLAUDE_MODEL,
}


def _set_setting(name: str, value: str) -> None:
    setattr(settings, name, value)
    setattr(Settings, name, value)


def _mask_secret(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"


def _get_provider_secret(provider: str) -> str:
    field = PROVIDER_KEY_FIELD.get(provider)
    return getattr(settings, field, "") if field else ""


def _get_provider_model(provider: str) -> str:
    field = PROVIDER_MODEL_FIELD.get(provider)
    return getattr(settings, field, "") if field else PROVIDER_DEFAULT_MODEL["mock"]


def _normalize_provider(provider: str) -> str:
    normalized = (provider or "mock").strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise ValueError(f"不支持的 Provider: {provider}")
    return normalized


def get_provider_snapshot() -> Dict[str, object]:
    provider = _normalize_provider(getattr(settings, "AI_PROVIDER", "mock"))
    api_key = _get_provider_secret(provider)
    return {
        "provider": provider,
        "model": _get_provider_model(provider),
        "api_key_configured": bool(api_key),
        "api_key_masked": _mask_secret(api_key),
        "live_llm_enabled": provider != "mock" and bool(api_key),
        "available_providers": sorted(SUPPORTED_PROVIDERS),
    }


def _persist_env_updates(updates: Dict[str, str]) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    keys_left = set(updates.keys())
    new_lines = []

    for line in lines:
        stripped = line.strip()
        replaced = False
        for key, value in updates.items():
            if stripped.startswith(f"{key}="):
                new_lines.append(f"{key}={value}")
                keys_left.discard(key)
                replaced = True
                break
        if not replaced:
            new_lines.append(line)

    if keys_left:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        for key in keys_left:
            new_lines.append(f"{key}={updates[key]}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def update_provider_config(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    persist_to_env: bool = False,
) -> Dict[str, object]:
    provider = _normalize_provider(provider)
    updates: Dict[str, str] = {"AI_PROVIDER": provider}
    _set_setting("AI_PROVIDER", provider)

    model_field = PROVIDER_MODEL_FIELD.get(provider)
    if model_field and model:
        _set_setting(model_field, model)
        updates[model_field] = model

    key_field = PROVIDER_KEY_FIELD.get(provider)
    if key_field and api_key is not None:
        _set_setting(key_field, api_key)
        updates[key_field] = api_key

    if persist_to_env:
        _persist_env_updates(updates)

    snapshot = get_provider_snapshot()
    snapshot["persisted"] = persist_to_env
    return snapshot


@contextmanager
def temporary_provider_config(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Iterator[None]:
    provider = _normalize_provider(provider)
    original = {
        "AI_PROVIDER": getattr(settings, "AI_PROVIDER", "mock"),
        "GEMINI_API_KEY": getattr(settings, "GEMINI_API_KEY", ""),
        "GEMINI_MODEL": getattr(settings, "GEMINI_MODEL", PROVIDER_DEFAULT_MODEL["gemini"]),
        "CLAUDE_API_KEY": getattr(settings, "CLAUDE_API_KEY", ""),
        "CLAUDE_MODEL": getattr(settings, "CLAUDE_MODEL", PROVIDER_DEFAULT_MODEL["claude"]),
    }

    try:
        update_provider_config(provider, api_key=api_key, model=model, persist_to_env=False)
        yield
    finally:
        for key, value in original.items():
            _set_setting(key, value)
