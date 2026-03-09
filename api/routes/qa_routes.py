import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from accessibility.elderly_support.step_guide import StepGuide
from core.rag_engine import RAGEngine
from utils.security import redact_sensitive_text

logger = logging.getLogger(__name__)
router = APIRouter()


class QuestionRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    game_id: str = Field(..., description="游戏 ID")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="用户上下文")
    top_k: int = Field(default=5, ge=1, le=20, description="返回来源数量")
    include_sources: bool = Field(default=True, description="是否返回来源")
    include_assistive_guide: bool = Field(default=False, description="是否返回分步引导")


class SourceItem(BaseModel):
    source: str
    score: float


class QuestionResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceItem] = []
    metadata: Dict[str, Any]


class AssistiveGuideRequest(BaseModel):
    question: str = Field(..., description="任务或问题描述")
    game_id: str = Field(..., description="游戏 ID")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="用户上下文")
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
            raise HTTPException(status_code=400, detail="问题不能为空")
        if not request.game_id.strip():
            raise HTTPException(status_code=400, detail="game_id 不能为空")

        rag = RAGEngine(request.game_id)
        result = await rag.query(request.question, request.user_context or {})
        metadata = result.get("metadata", {})

        user_context = request.user_context or {}
        user_type = str(user_context.get("user_type", "normal"))
        if request.include_assistive_guide or user_type != "normal":
            guide = StepGuide(request.game_id)
            metadata["assistive_guide"] = await guide.generate_guide(
                request.question,
                user_context,
                str(user_context.get("difficulty_level", "beginner")),
            )

        sources: List[SourceItem] = []
        if request.include_sources:
            for item in result.get("sources", [])[: request.top_k]:
                sources.append(SourceItem(source=str(item), score=1.0))

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
        raise HTTPException(status_code=500, detail="问答处理失败")


@router.post("/assistive-guide", response_model=AssistiveGuideResponse)
async def generate_assistive_guide(request: AssistiveGuideRequest):
    try:
        guide = StepGuide(request.game_id)
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
        raise HTTPException(status_code=500, detail="分步引导生成失败")
