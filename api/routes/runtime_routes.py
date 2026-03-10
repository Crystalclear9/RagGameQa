from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.runtime_config import (
    clear_saved_provider_secret,
    get_provider_snapshot,
    temporary_provider_config,
    update_provider_config,
    validate_provider_config,
)
from core.generator.llm_generator import LLMGenerator
from utils.security import redact_sensitive_text

logger = logging.getLogger(__name__)
router = APIRouter()


class ProviderConfigRequest(BaseModel):
    provider: str = Field(..., description="mock | gemini | claude | nim")
    api_key: Optional[str] = Field(default=None, description="新的 API Key，可留空表示沿用当前配置")
    model: Optional[str] = Field(default=None, description="模型名称，可自定义填写最新模型 ID")
    persist_to_env: bool = Field(default=False, description="兼容旧参数，等价于 storage_mode=env")
    storage_mode: Optional[str] = Field(default=None, description="session | secure_local | env")


class ProviderConfigResponse(BaseModel):
    provider: str
    model: str
    api_key_configured: bool
    api_key_masked: str
    live_llm_enabled: bool
    available_providers: list[str]
    storage_mode: str
    secure_storage_supported: bool
    provider_catalog: Dict[str, Dict[str, Any]]
    persisted: Optional[bool] = None


class ProviderTestRequest(BaseModel):
    provider: str = Field(..., description="mock | gemini | claude | nim")
    api_key: Optional[str] = Field(default=None, description="测试时使用的 API Key")
    model: Optional[str] = Field(default=None, description="测试时使用的模型")


class ProviderTestResponse(BaseModel):
    provider: str
    model: str
    success: bool
    preview: str


class ProviderClearRequest(BaseModel):
    provider: str = Field(..., description="要清除的 Provider")
    clear_env: bool = Field(default=False, description="是否一并清除 .env 中的调试配置")


@router.get("/provider-config", response_model=ProviderConfigResponse)
async def get_provider_config():
    try:
        return ProviderConfigResponse(**get_provider_snapshot())
    except Exception as exc:
        logger.error("Failed to read provider config: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="读取 Provider 配置失败")


@router.post("/provider-config", response_model=ProviderConfigResponse)
async def set_provider_config(req: ProviderConfigRequest):
    try:
        snapshot = update_provider_config(
            provider=req.provider,
            api_key=req.api_key,
            model=req.model,
            persist_to_env=req.persist_to_env,
            storage_mode=req.storage_mode,
        )
        return ProviderConfigResponse(**snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to update provider config: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="更新 Provider 配置失败")


@router.post("/provider-config/test", response_model=ProviderTestResponse)
async def test_provider_config(req: ProviderTestRequest):
    try:
        validate_provider_config(req.provider, req.api_key)
        with temporary_provider_config(req.provider, api_key=req.api_key, model=req.model):
            generator = LLMGenerator("wow")
            answer = await generator.generate(
                question="请用一句中文说明连接是否成功，并指出当前模型。",
                context_docs=[
                    {
                        "content": "这是连接测试上下文，仅用于验证模型可以被访问。",
                        "category": "system",
                        "metadata": {"source": "runtime-test"},
                    }
                ],
                user_context={"user_id": "runtime-config-test"},
            )
            preview = answer.strip().replace("\n", " ")[:160]
            success = not any(keyword in preview for keyword in ("失败", "异常", "不可用"))
            return ProviderTestResponse(
                provider=req.provider.lower(),
                model=req.model or get_provider_snapshot()["model"],
                success=success,
                preview=preview,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Provider test failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="测试 Provider 配置失败")


@router.post("/provider-config/clear", response_model=ProviderConfigResponse)
async def clear_provider_config(req: ProviderClearRequest):
    try:
        snapshot = clear_saved_provider_secret(req.provider, clear_env=req.clear_env)
        return ProviderConfigResponse(**snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to clear provider secret: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="清除已保存密钥失败")
