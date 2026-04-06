from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, Optional

from config.secure_storage import (
    SecureStorageError,
    clear_secure_payload,
    load_secure_payload,
    save_secure_payload,
    secure_storage_supported,
)
from config.settings import Settings, settings
from utils.security import mask_secret, redact_sensitive_text

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
SUPPORTED_PROVIDERS = {"mock", "gemini", "claude", "nim", "deepseek"}
SUPPORTED_STORAGE_MODES = {"session", "secure_local", "env"}

PROVIDER_MODEL_FIELD = {
    "mock": None,
    "gemini": "GEMINI_MODEL",
    "claude": "CLAUDE_MODEL",
    "nim": "NIM_MODEL",
    "deepseek": "DEEPSEEK_MODEL",
}

PROVIDER_KEY_FIELD = {
    "mock": None,
    "gemini": "GEMINI_API_KEY",
    "claude": "CLAUDE_API_KEY",
    "nim": "NIM_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

PROVIDER_DEFAULT_MODEL = {
    "mock": "mock-llm-v1",
    "gemini": settings.GEMINI_MODEL,
    "claude": settings.CLAUDE_MODEL,
    "nim": settings.NIM_MODEL,
    "deepseek": settings.DEEPSEEK_MODEL,
}

PROVIDER_CATALOG = {
    "mock": {
        "recommended": "mock-llm-v1",
        "latest_verified_at": "2026-03-09",
        "source_url": "",
        "models": [
            {"id": "mock-llm-v1", "label": "本地演示模式", "stage": "stable"},
        ],
    },
    "gemini": {
        "recommended": "gemini-2.5-flash",
        "latest_verified_at": "2026-03-09",
        "source_url": "https://ai.google.dev/gemini-api/docs/models",
        "models": [
            {"id": "gemini-3.1-pro-preview", "label": "最新预览 Pro", "stage": "preview"},
            {"id": "gemini-3-flash-preview", "label": "最新预览 Flash", "stage": "preview"},
            {"id": "gemini-3.1-flash-lite-preview", "label": "最新预览 Flash-Lite", "stage": "preview"},
            {"id": "gemini-2.5-flash", "label": "稳定推荐", "stage": "stable"},
            {"id": "gemini-2.5-pro", "label": "高质量稳定版", "stage": "stable"},
            {"id": "gemini-flash-latest", "label": "自动跟随最新 Flash", "stage": "alias"},
        ],
    },
    "claude": {
        "recommended": "claude-sonnet-4-6",
        "latest_verified_at": "2026-03-09",
        "source_url": "https://docs.anthropic.com/en/docs/about-claude/models/overview",
        "models": [
            {"id": "claude-sonnet-4-6", "label": "最新平衡模型", "stage": "latest"},
            {"id": "claude-opus-4-6", "label": "高能力旗舰模型", "stage": "latest"},
            {"id": "claude-haiku-4-5", "label": "低延迟轻量模型", "stage": "latest"},
        ],
    },
    "nim": {
        "recommended": settings.NIM_MODEL or "meta/llama-3.1-70b-instruct",
        "latest_verified_at": "2026-03-10",
        "source_url": "https://build.nvidia.com/explore/discover",
        "models": [
            {"id": settings.NIM_MODEL or "meta/llama-3.1-70b-instruct", "label": "当前本地默认模型", "stage": "config"},
            {"id": "自定义填写", "label": "按你的 NIM 部署模型填写", "stage": "custom"},
        ],
    },
    "deepseek": {
        "recommended": settings.DEEPSEEK_MODEL or "deepseek-chat",
        "latest_verified_at": "2026-04-06",
        "source_url": "https://platform.deepseek.com",
        "models": [
            {"id": settings.DEEPSEEK_MODEL or "deepseek-chat", "label": "当前配置模型", "stage": "config"},
            {"id": "deepseek-chat", "label": "DeepSeek-V3", "stage": "stable"},
            {"id": "deepseek-reasoner", "label": "DeepSeek-R1", "stage": "stable"},
        ],
    },
}


def _set_setting(name: str, value: str) -> None:
    setattr(settings, name, value)
    setattr(Settings, name, value)


def _normalize_provider(provider: str) -> str:
    normalized = (provider or "mock").strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise ValueError(f"不支持的 Provider: {provider}")
    return normalized


def _normalize_storage_mode(storage_mode: Optional[str], persist_to_env: bool = False) -> str:
    normalized = (storage_mode or "").strip().lower()
    if not normalized:
        normalized = "env" if persist_to_env else "session"
    if normalized not in SUPPORTED_STORAGE_MODES:
        raise ValueError(f"不支持的保存方式: {storage_mode}")
    if normalized == "secure_local" and not secure_storage_supported():
        raise ValueError("当前系统不支持本机安全存储，请改用仅会话或 .env 调试模式")
    return normalized


def _normalize_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if any(char in cleaned for char in ("\r", "\n", "\0")):
        raise ValueError("配置内容不能包含换行或空字符")
    return cleaned


def _get_provider_secret(provider: str) -> str:
    field = PROVIDER_KEY_FIELD.get(provider)
    return getattr(settings, field, "") if field else ""


def _get_provider_model(provider: str) -> str:
    field = PROVIDER_MODEL_FIELD.get(provider)
    return getattr(settings, field, "") if field else PROVIDER_DEFAULT_MODEL["mock"]


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
        for key in sorted(keys_left):
            new_lines.append(f"{key}={updates[key]}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _build_secure_payload(provider: str, api_key: Optional[str], model: Optional[str]) -> Dict[str, str]:
    provider = _normalize_provider(provider)
    payload = {
        "provider": provider,
        "model": model or _get_provider_model(provider) or PROVIDER_DEFAULT_MODEL[provider],
        "storage_mode": "secure_local",
    }
    if provider != "mock" and api_key:
        payload["api_key"] = api_key
    return payload


def validate_provider_config(provider: str, api_key: Optional[str] = None) -> None:
    provider = _normalize_provider(provider)
    if provider == "mock":
        return

    configured_key = api_key or _get_provider_secret(provider)
    if not configured_key:
        raise ValueError(f"{provider} 需要先提供 API Key")


def get_provider_snapshot() -> Dict[str, object]:
    provider = _normalize_provider(getattr(settings, "AI_PROVIDER", "mock"))
    api_key = _get_provider_secret(provider)
    storage_mode = getattr(settings, "RUNTIME_STORAGE_MODE", "session")
    return {
        "provider": provider,
        "model": _get_provider_model(provider),
        "api_key_configured": bool(api_key),
        "api_key_masked": mask_secret(api_key),
        "live_llm_enabled": provider != "mock" and bool(api_key),
        "available_providers": sorted(SUPPORTED_PROVIDERS),
        "storage_mode": storage_mode,
        "secure_storage_supported": secure_storage_supported(),
        "provider_catalog": PROVIDER_CATALOG,
    }


def update_provider_config(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    persist_to_env: bool = False,
    storage_mode: Optional[str] = None,
) -> Dict[str, object]:
    provider = _normalize_provider(provider)
    normalized_key = _normalize_value(api_key)
    normalized_model = _normalize_value(model) or _get_provider_model(provider) or PROVIDER_CATALOG[provider]["recommended"]
    normalized_storage_mode = _normalize_storage_mode(storage_mode, persist_to_env=persist_to_env)

    if provider != "mock" and normalized_key is None and not _get_provider_secret(provider):
        raise ValueError(f"{provider} 需要先提供 API Key")

    updates: Dict[str, str] = {
        "AI_PROVIDER": provider,
        "RUNTIME_STORAGE_MODE": normalized_storage_mode,
    }
    _set_setting("AI_PROVIDER", provider)
    _set_setting("RUNTIME_STORAGE_MODE", normalized_storage_mode)

    model_field = PROVIDER_MODEL_FIELD.get(provider)
    if model_field:
        _set_setting(model_field, normalized_model)
        updates[model_field] = normalized_model

    key_field = PROVIDER_KEY_FIELD.get(provider)
    if key_field and normalized_key is not None:
        _set_setting(key_field, normalized_key)
        updates[key_field] = normalized_key

    if normalized_storage_mode == "env":
        _persist_env_updates(updates)
    elif normalized_storage_mode == "secure_local":
        try:
            save_secure_payload(
                _build_secure_payload(
                    provider=provider,
                    api_key=_get_provider_secret(provider),
                    model=_get_provider_model(provider),
                )
            )
        except SecureStorageError as exc:
            raise ValueError("本机安全存储写入失败，请稍后重试") from exc

    snapshot = get_provider_snapshot()
    snapshot["persisted"] = normalized_storage_mode != "session"
    snapshot["storage_mode"] = normalized_storage_mode
    return snapshot


def load_persisted_runtime_config() -> bool:
    try:
        payload = load_secure_payload()
    except SecureStorageError as exc:
        logger.warning("Failed to load secure runtime config: %s", redact_sensitive_text(exc))
        return False

    if not payload:
        return False

    try:
        provider = _normalize_provider(str(payload.get("provider", "mock")))
        model = _normalize_value(str(payload.get("model", ""))) or PROVIDER_CATALOG[provider]["recommended"]
        api_key = _normalize_value(str(payload.get("api_key", "")))

        _set_setting("AI_PROVIDER", provider)
        _set_setting("RUNTIME_STORAGE_MODE", "secure_local")

        model_field = PROVIDER_MODEL_FIELD.get(provider)
        if model_field:
            _set_setting(model_field, model)

        key_field = PROVIDER_KEY_FIELD.get(provider)
        if key_field and api_key:
            _set_setting(key_field, api_key)
        return True
    except Exception as exc:
        logger.warning("Persisted runtime config is invalid: %s", redact_sensitive_text(exc))
        return False


def clear_saved_provider_secret(provider: str, clear_env: bool = False) -> Dict[str, object]:
    provider = _normalize_provider(provider)
    key_field = PROVIDER_KEY_FIELD.get(provider)

    if key_field:
        _set_setting(key_field, "")

    if getattr(settings, "AI_PROVIDER", "mock") == provider:
        _set_setting("AI_PROVIDER", "mock")
        _set_setting("RUNTIME_STORAGE_MODE", "session")

    try:
        clear_secure_payload()
    except SecureStorageError as exc:
        logger.warning("Failed to clear secure payload: %s", redact_sensitive_text(exc))

    if clear_env and key_field:
        _persist_env_updates(
            {
                key_field: "",
                "AI_PROVIDER": "mock",
                "RUNTIME_STORAGE_MODE": "session",
            }
        )

    snapshot = get_provider_snapshot()
    snapshot["persisted"] = False
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
        "RUNTIME_STORAGE_MODE": getattr(settings, "RUNTIME_STORAGE_MODE", "session"),
        "GEMINI_API_KEY": getattr(settings, "GEMINI_API_KEY", ""),
        "GEMINI_MODEL": getattr(settings, "GEMINI_MODEL", PROVIDER_DEFAULT_MODEL["gemini"]),
        "CLAUDE_API_KEY": getattr(settings, "CLAUDE_API_KEY", ""),
        "CLAUDE_MODEL": getattr(settings, "CLAUDE_MODEL", PROVIDER_DEFAULT_MODEL["claude"]),
    }

    try:
        update_provider_config(
            provider,
            api_key=api_key,
            model=model,
            persist_to_env=False,
            storage_mode="session",
        )
        yield
    finally:
        for key, value in original.items():
            _set_setting(key, value)
