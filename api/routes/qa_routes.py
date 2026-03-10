from __future__ import annotations

import importlib
import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from accessibility.elderly_support.step_guide import StepGuide
from config.settings import settings
from core.rag_engine import RAGEngine
from utils.security import redact_sensitive_text

logger = logging.getLogger(__name__)
router = APIRouter()
_ENGINE_CACHE: "OrderedDict[Tuple[str, str, str, str, bool], RAGEngine]" = OrderedDict()
_STEP_GUIDE_CACHE: Dict[str, StepGuide] = {}


def _current_model_name() -> str:
    provider = (settings.AI_PROVIDER or "mock").lower()
    if provider == "gemini":
        return settings.GEMINI_MODEL
    if provider == "claude":
        return settings.CLAUDE_MODEL
    if provider == "nim":
        return settings.NIM_MODEL
    return "mock-llm-v1"


def _get_rag_engine(game_id: str) -> RAGEngine:
    key = (
        game_id,
        str(settings.AI_PROVIDER or "mock").lower(),
        _current_model_name(),
        str(settings.RAG_DATA_MODE or "database"),
        bool(settings.ENABLE_BERT_RERANKER),
    )
    cached = _ENGINE_CACHE.get(key)
    if cached is not None:
        _ENGINE_CACHE.move_to_end(key)
        return cached

    engine = RAGEngine(game_id)
    _ENGINE_CACHE[key] = engine
    if len(_ENGINE_CACHE) > 8:
        _ENGINE_CACHE.popitem(last=False)
    return engine


def _get_step_guide(game_id: str) -> StepGuide:
    guide = _STEP_GUIDE_CACHE.get(game_id)
    if guide is None:
        guide = StepGuide(game_id)
        _STEP_GUIDE_CACHE[game_id] = guide
    return guide


def _optional_class(module_name: str, class_name: str):
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except Exception:
        return None


class QuestionRequest(BaseModel):
    question: str = Field(..., description="User question")
    game_id: str = Field(..., description="Game ID")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="User context")
    top_k: int = Field(default=5, ge=1, le=20, description="Top sources")
    include_sources: bool = Field(default=True, description="Return sources")
    include_assistive_guide: bool = Field(default=False, description="Return assistive guide")
    include_family_guide: bool = Field(default=False, description="Return family guide")
    enable_web_retrieval: bool = Field(default=True, description="Enable online retrieval fallback")


class SourceItem(BaseModel):
    source: str
    score: float


class QuestionResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceItem] = []
    metadata: Dict[str, Any]


class AssistiveGuideRequest(BaseModel):
    question: str = Field(..., description="Task or question")
    game_id: str = Field(..., description="Game ID")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context")
    difficulty_level: str = Field(default="beginner", description="beginner/intermediate/advanced")


class AssistiveGuideResponse(BaseModel):
    steps: List[Dict[str, Any]]
    difficulty_level: str
    metadata: Dict[str, Any]


@router.get("/ping")
async def ping():
    return {"status": "ok"}


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        if not request.game_id.strip():
            raise HTTPException(status_code=400, detail="game_id cannot be empty")

        rag = _get_rag_engine(request.game_id)
        result = await rag.query(
            request.question,
            request.user_context or {},
            top_k=request.top_k,
            enable_web_retrieval=request.enable_web_retrieval,
        )
        metadata = result.get("metadata", {})

        user_context = request.user_context or {}
        user_type = str(user_context.get("user_type", "normal"))

        if user_type == "elderly":
            patience_model_cls = _optional_class(
                "accessibility.elderly_support.patience_model",
                "PatienceModel",
            )
            if patience_model_cls is not None:
                patience_model = patience_model_cls(request.game_id)
                metadata["patience_analysis"] = await patience_model.check_patience(
                    request.question,
                    str(user_context.get("user_id", "anonymous")),
                )
            else:
                metadata["patience_analysis"] = {
                    "available": False,
                    "message": "Patience model dependency missing, skipped",
                }

        auto_guide_requested = bool(metadata.get("patience_analysis", {}).get("needs_guidance"))
        if request.include_assistive_guide or user_type != "normal" or auto_guide_requested:
            guide = _get_step_guide(request.game_id)
            metadata["assistive_guide"] = await guide.generate_guide(
                request.question,
                user_context,
                str(user_context.get("difficulty_level", "beginner")),
            )
            if auto_guide_requested and not request.include_assistive_guide:
                metadata["assistive_guide_reason"] = "patience_model"

        if request.include_family_guide or bool(user_context.get("family_mode")):
            family_cls = _optional_class(
                "accessibility.elderly_support.family_collaboration",
                "FamilyCollaboration",
            )
            if family_cls is not None:
                family = family_cls(request.game_id)
                metadata["family_guide"] = await family.generate_family_guide(
                    request.question,
                    result.get("answer", ""),
                    user_context,
                )
            else:
                metadata["family_guide"] = {
                    "available": False,
                    "message": "Family collaboration dependency missing, skipped",
                }

        sources: List[SourceItem] = []
        if request.include_sources:
            for item in result.get("retrieved_docs", [])[: request.top_k]:
                meta = item.get("metadata") or {}
                label = str(meta.get("title") or meta.get("source") or "source")
                raw_score = item.get("final_score", item.get("score", 0.0))
                try:
                    score = float(raw_score)
                except Exception:
                    score = 0.0
                sources.append(SourceItem(source=label, score=score))

        return QuestionResponse(
            answer=result.get("answer", ""),
            confidence=float(result.get("confidence", 0.0)),
            sources=sources,
            metadata=metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("QA request failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="QA processing failed")


@router.post("/assistive-guide", response_model=AssistiveGuideResponse)
async def generate_assistive_guide(request: AssistiveGuideRequest):
    try:
        guide = _get_step_guide(request.game_id)
        steps = await guide.generate_guide(
            request.question,
            request.user_context,
            request.difficulty_level,
        )
        return AssistiveGuideResponse(
            steps=steps,
            difficulty_level=request.difficulty_level,
            metadata={
                "game_id": request.game_id,
                "user_type": request.user_context.get("user_type", "normal"),
            },
        )
    except Exception as exc:
        logger.error("Assistive guide generation failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Assistive guide generation failed")
