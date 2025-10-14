# 分析路由
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from config.database import SessionLocal, Feedback, QueryLog
from utils.text_utils import TextUtils

router = APIRouter()


class FeedbackAnalysisRequest(BaseModel):
    game_id: str = Field(..., description="游戏ID")
    start_time: Optional[str] = Field(None, description="开始时间ISO8601")
    end_time: Optional[str] = Field(None, description="结束时间ISO8601")


class FeedbackAnalysisResponse(BaseModel):
    total: int
    positive: int
    negative: int
    neutral: int
    top_keywords: List[str] = []


@router.post("/feedback/analysis", response_model=FeedbackAnalysisResponse)
async def analyze_feedback(req: FeedbackAnalysisRequest):
    """反馈分析接口（简版统计）"""
    try:
        db = SessionLocal()
        q = db.query(Feedback).filter(Feedback.game_id == req.game_id)
        rows = q.all()

        total = len(rows)
        pos = sum(1 for r in rows if (r.feedback_type or "").lower() == "positive")
        neg = sum(1 for r in rows if (r.feedback_type or "").lower() == "negative")
        neu = total - pos - neg

        # 关键词统计：使用TextUtils提取TopK
        freq: Dict[str, int] = {}
        for r in rows:
            if r.comment:
                kws = TextUtils.extract_keywords(r.comment, top_k=10)
                for w in kws:
                    freq[w] = freq.get(w, 0) + 1
        top_keywords = [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]]

        return FeedbackAnalysisResponse(
            total=total, positive=pos, negative=neg, neutral=neu, top_keywords=top_keywords
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈分析失败: {e}")
    finally:
        try:
            db.close()
        except Exception:
            pass


class HeatmapPoint(BaseModel):
    x: float
    y: float
    value: float


@router.get("/heatmap", response_model=List[HeatmapPoint])
async def generate_heatmap(game_id: str = Query(..., description="游戏ID")):
    """生成热力图接口（示例数据）"""
    try:
        # 返回示例热力图点位
        return [
            HeatmapPoint(x=10, y=20, value=0.8),
            HeatmapPoint(x=30, y=40, value=0.6),
            HeatmapPoint(x=50, y=60, value=0.9),
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"热力图生成失败: {e}")


# ---------------- 反馈分类与趋势（占位实现） ----------------

class FeedbackItem(BaseModel):
    id: int
    comment: str


class FeedbackClassifyRequest(BaseModel):
    game_id: str
    items: List[FeedbackItem]


class ClassifiedItem(BaseModel):
    id: int
    label: str
    confidence: float


class FeedbackClassifyResponse(BaseModel):
    model: str
    results: List[ClassifiedItem]


@router.post("/feedback/classify", response_model=FeedbackClassifyResponse)
async def classify_feedback(req: FeedbackClassifyRequest):
    """反馈分类（BERT+BiLSTM占位），输出标签与置信度"""
    try:
        # 占位：简化为基于关键词的启发式
        def heuristic_label(text: str) -> str:
            t = (text or "").lower()
            if any(k in t for k in ["bug", "异常", "报错", "崩溃"]):
                return "bug_report"
            if any(k in t for k in ["建议", "希望", "feature", "新增"]):
                return "feature_request"
            if any(k in t for k in ["平衡", "强度", "削弱", "增强"]):
                return "balance_feedback"
            return "general_question"

        results: List[ClassifiedItem] = []
        for it in req.items:
            label = heuristic_label(it.comment)
            conf = 0.9 if label != "general_question" else 0.6
            results.append(ClassifiedItem(id=it.id, label=label, confidence=conf))

        return FeedbackClassifyResponse(model="bert-bilstm-placeholder", results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈分类失败: {e}")


class TrendPoint(BaseModel):
    date: str
    count: int
    label: str


@router.get("/trends", response_model=List[TrendPoint])
async def get_trends(game_id: str = Query(...), days: int = Query(7, ge=1, le=30)):
    """按天统计反馈/问题趋势（占位）"""
    try:
        # 占位：返回均匀趋势
        data: List[TrendPoint] = []
        for i in range(days):
            data.append(TrendPoint(date=f"D-{days - i}", count=10 + (i % 3), label="total"))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趋势统计失败: {e}")


class PriorityItem(BaseModel):
    title: str
    score: float
    label: str


@router.get("/priority-report", response_model=List[PriorityItem])
async def get_priority_report(game_id: str = Query(...)):
    """生成优先级报告（占位：按频次与标签权重计算）"""
    try:
        db = SessionLocal()
        rows = db.query(Feedback).filter(Feedback.game_id == game_id).all()
        buckets: Dict[str, int] = {"bug_report": 0, "feature_request": 0, "balance_feedback": 0, "general_question": 0}
        for r in rows:
            buckets[(r.feedback_type or "general_question").lower()] = buckets.get((r.feedback_type or "general_question").lower(), 0) + 1

        weights = {"bug_report": 1.0, "feature_request": 0.7, "balance_feedback": 0.8, "general_question": 0.3}
        items: List[PriorityItem] = []
        for label, cnt in buckets.items():
            items.append(PriorityItem(title=f"{label}", score=float(cnt) * weights.get(label, 0.5), label=label))

        items.sort(key=lambda x: x.score, reverse=True)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优先级报告生成失败: {e}")
    finally:
        try:
            db.close()
        except Exception:
            pass
