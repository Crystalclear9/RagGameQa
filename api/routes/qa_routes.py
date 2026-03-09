# 问答路由
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from accessibility.elderly_support.step_guide import StepGuide
from core.rag_engine import RAGEngine

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    game_id: str = Field(..., description="游戏ID")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="用户上下文信息")
    top_k: int = Field(default=5, ge=1, le=20, description="检索文档数量")
    include_sources: bool = Field(default=True, description="是否返回来源信息")
    include_assistive_guide: bool = Field(default=False, description="是否返回无障碍分步引导")

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
    game_id: str = Field(..., description="游戏ID")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="用户上下文")
    difficulty_level: str = Field(default="beginner", description="beginner/intermediate/advanced")


class AssistiveGuideResponse(BaseModel):
    steps: List[Dict[str, Any]]
    difficulty_level: str
    metadata: Dict[str, Any]

@router.get("/ping")
async def ping():
    """健康检查"""
    return {"status": "ok"}

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """问答接口"""
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
            for s in result.get("sources", [])[: request.top_k]:
                sources.append(SourceItem(source=str(s), score=1.0))

        return QuestionResponse(
            answer=result.get("answer", ""),
            confidence=float(result.get("confidence", 0.0)),
            sources=sources,
            metadata=metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"问答处理失败: {str(e)}"
        print(f"错误详情: {error_detail}")
        print(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/assistive-guide", response_model=AssistiveGuideResponse)
async def generate_assistive_guide(request: AssistiveGuideRequest):
    """生成老年友好的分步引导。"""
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分步引导生成失败: {e}")
