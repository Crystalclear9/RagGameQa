# 运行时配置路由
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.runtime_config import get_provider_snapshot, temporary_provider_config, update_provider_config
from core.generator.llm_generator import LLMGenerator

router = APIRouter()


class ProviderConfigRequest(BaseModel):
    provider: str = Field(..., description="mock | gemini | claude")
    api_key: Optional[str] = Field(default=None, description="新的 API Key；留空表示不改")
    model: Optional[str] = Field(default=None, description="模型名")
    persist_to_env: bool = Field(default=False, description="是否写回 .env")


class ProviderConfigResponse(BaseModel):
    provider: str
    model: str
    api_key_configured: bool
    api_key_masked: str
    live_llm_enabled: bool
    available_providers: list[str]
    persisted: Optional[bool] = None


class ProviderTestRequest(BaseModel):
    provider: str = Field(..., description="mock | gemini | claude")
    api_key: Optional[str] = Field(default=None, description="测试时使用的 API Key")
    model: Optional[str] = Field(default=None, description="测试时使用的模型")


class ProviderTestResponse(BaseModel):
    provider: str
    model: str
    success: bool
    preview: str


@router.get("/provider-config", response_model=ProviderConfigResponse)
async def get_provider_config():
    """返回当前运行时 Provider 配置（密钥已脱敏）。"""
    try:
        return ProviderConfigResponse(**get_provider_snapshot())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取 Provider 配置失败: {exc}")


@router.post("/provider-config", response_model=ProviderConfigResponse)
async def set_provider_config(req: ProviderConfigRequest):
    """更新当前运行时 Provider 配置，可选写回 .env。"""
    try:
        api_key = req.api_key if req.api_key not in {"", None} else None
        snapshot = update_provider_config(
            provider=req.provider,
            api_key=api_key,
            model=req.model,
            persist_to_env=req.persist_to_env,
        )
        return ProviderConfigResponse(**snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"更新 Provider 配置失败: {exc}")


@router.post("/provider-config/test", response_model=ProviderTestResponse)
async def test_provider_config(req: ProviderTestRequest):
    """测试用户在图形界面中输入的 Provider 配置是否可用。"""
    try:
        api_key = req.api_key if req.api_key not in {"", None} else None
        with temporary_provider_config(req.provider, api_key=api_key, model=req.model):
            generator = LLMGenerator("wow")
            answer = await generator.generate(
                question="请用一句中文说明连接是否成功，并指出当前模型。",
                context_docs=[
                    {
                        "content": "这是连接测试上下文，只用于验证模型是否可访问。",
                        "category": "system",
                        "metadata": {"source": "runtime-test"},
                    }
                ],
                user_context={"user_id": "runtime-config-test"},
            )
            preview = answer.strip().replace("\n", " ")[:160]
            success = "失败" not in preview and "异常" not in preview
            return ProviderTestResponse(
                provider=req.provider.lower(),
                model=req.model or get_provider_snapshot()["model"],
                success=success,
                preview=preview,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"测试 Provider 配置失败: {exc}")
