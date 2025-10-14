# 问答路由
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str
    game_id: str
    user_context: Optional[Dict[str, Any]] = None

class QuestionResponse(BaseModel):
    answer: str
    confidence: float
    sources: list
    metadata: Dict[str, Any]

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """问答接口"""
    try:
        # 这里应该调用RAG引擎
        return QuestionResponse(
            answer="这是一个示例答案",
            confidence=0.9,
            sources=["source1", "source2"],
            metadata={"processing_time": 0.5}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
