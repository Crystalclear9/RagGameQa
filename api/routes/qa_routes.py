# 问答路由
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from core.rag_engine import RAGEngine

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    game_id: str = Field(..., description="游戏ID")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="用户上下文信息")
    top_k: int = Field(default=5, ge=1, le=20, description="检索文档数量")
    include_sources: bool = Field(default=True, description="是否返回来源信息")

class SourceItem(BaseModel):
    source: str
    score: float

class QuestionResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceItem] = []
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

        sources: List[SourceItem] = []
        if request.include_sources:
            for s in result.get("sources", [])[: request.top_k]:
                sources.append(SourceItem(source=str(s), score=1.0))

        return QuestionResponse(
            answer=result.get("answer", ""),
            confidence=float(result.get("confidence", 0.0)),
            sources=sources,
            metadata=result.get("metadata", {}),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
