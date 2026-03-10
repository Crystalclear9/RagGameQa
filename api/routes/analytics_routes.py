# 分析路由
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config.database import Feedback, QueryLog, SessionLocal, ensure_game_record
from integrations.jira_client import JiraClient
from utils.security import redact_sensitive_text
from utils.text_utils import TextUtils

router = APIRouter()
logger = logging.getLogger(__name__)

LABEL_KEYWORDS = {
    "bug_report": ["bug", "异常", "报错", "崩溃", "卡住", "闪退", "无法"],
    "feature_request": ["建议", "希望", "新增", "增加", "优化", "feature"],
    "balance_feedback": ["平衡", "强度", "削弱", "增强", "太强", "太弱"],
    "gameplay_help": ["怎么", "如何", "攻略", "打法", "任务", "通关"],
}
LABEL_WEIGHTS = {
    "bug_report": 1.0,
    "balance_feedback": 0.85,
    "feature_request": 0.75,
    "gameplay_help": 0.5,
    "general_question": 0.4,
}


def _parse_iso_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _classify_feedback_text(text: str) -> tuple[str, float]:
    normalized = (text or "").lower()
    for label, keywords in LABEL_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in normalized)
        if hits:
            confidence = min(0.55 + hits * 0.15, 0.95)
            return label, round(confidence, 2)
    return "general_question", 0.55


def _infer_sentiment(feedback_type: Optional[str], rating: Optional[int], comment: str) -> str:
    if feedback_type in {"positive", "negative", "neutral"}:
        return feedback_type
    if rating is not None:
        if rating >= 4:
            return "positive"
        if rating <= 2:
            return "negative"
    negative_keywords = ["不好", "不行", "失败", "报错", "崩溃", "卡住", "闪退"]
    positive_keywords = ["不错", "很好", "喜欢", "清楚", "有帮助", "解决"]
    if any(keyword in (comment or "") for keyword in negative_keywords):
        return "negative"
    if any(keyword in (comment or "") for keyword in positive_keywords):
        return "positive"
    return "neutral"


def _in_range(created_at: Optional[datetime], start_time: Optional[datetime], end_time: Optional[datetime]) -> bool:
    if created_at is None:
        return False
    if start_time and created_at < start_time:
        return False
    if end_time and created_at > end_time:
        return False
    return True


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


class FeedbackCreateRequest(BaseModel):
    game_id: str = Field(..., description="游戏ID")
    user_id: Optional[str] = Field("anonymous", description="用户ID")
    query_log_id: Optional[int] = Field(None, description="关联查询日志ID")
    feedback_type: Optional[str] = Field(None, description="positive/negative/neutral")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")
    comment: str = Field("", description="文字反馈")


class FeedbackCreateResponse(BaseModel):
    id: int
    status: str
    feedback_type: str
    classification_label: str
    created_at: str


class HeatmapPoint(BaseModel):
    x: float
    y: float
    value: float


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


class TrendPoint(BaseModel):
    date: str
    count: int
    label: str


class QueryStatsResponse(BaseModel):
    total_queries: int
    avg_confidence: float
    avg_processing_time: float
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    top_questions: List[str] = []
    recent_days: List[TrendPoint] = []


class PriorityItem(BaseModel):
    title: str
    score: float
    label: str


class JiraStatusResponse(BaseModel):
    configured: bool
    base_url: str
    email_masked: str
    api_token_configured: bool
    project_key: str
    issue_type: str
    label_prefix: str


class JiraExportRequest(BaseModel):
    game_id: str = Field(..., description="游戏 ID")
    limit: int = Field(default=3, ge=1, le=10, description="最多导出的优先级项数量")
    dry_run: bool = Field(default=True, description="是否仅预览，不真正创建 Jira 工单")


class JiraExportIssue(BaseModel):
    summary: str
    label: str
    score: float
    created: bool
    jira_key: Optional[str] = None
    jira_url: Optional[str] = None


class JiraExportResponse(BaseModel):
    configured: bool
    dry_run: bool
    issue_count: int
    issues: List[JiraExportIssue]


def _build_priority_items(rows: List[Feedback]) -> List[PriorityItem]:
    summary: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "negative": 0, "keywords": []})

    for row in rows:
        label, _ = _classify_feedback_text(row.comment or "")
        summary[label]["count"] += 1
        if row.feedback_type == "negative":
            summary[label]["negative"] += 1
        summary[label]["keywords"].extend(TextUtils.extract_keywords(row.comment or "", top_k=3))

    items: List[PriorityItem] = []
    for label, stats in summary.items():
        count = stats["count"]
        negative_boost = 1 + min(stats["negative"] * 0.1, 0.5)
        score = round(count * LABEL_WEIGHTS.get(label, 0.4) * negative_boost, 2)
        keywords = Counter(stats["keywords"]).most_common(2)
        keyword_hint = " / ".join(word for word, _ in keywords) if keywords else label
        items.append(PriorityItem(title=keyword_hint, score=score, label=label))

    items.sort(key=lambda item: item.score, reverse=True)
    return items or [PriorityItem(title="暂无反馈", score=0.0, label="general_question")]


@router.post("/feedback", response_model=FeedbackCreateResponse)
async def create_feedback(req: FeedbackCreateRequest):
    """写入用户反馈，形成问答后的闭环数据。"""
    db = SessionLocal()
    try:
        ensure_game_record(db, req.game_id)
        label, _ = _classify_feedback_text(req.comment)
        feedback_type = _infer_sentiment(req.feedback_type, req.rating, req.comment)
        feedback = Feedback(
            game_id=req.game_id,
            user_id=req.user_id or "anonymous",
            query_log_id=req.query_log_id,
            feedback_type=feedback_type,
            rating=req.rating,
            comment=req.comment,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return FeedbackCreateResponse(
            id=int(feedback.id),
            status="stored",
            feedback_type=feedback_type,
            classification_label=label,
            created_at=feedback.created_at.isoformat(),
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"反馈写入失败: {exc}")
    finally:
        db.close()


@router.post("/feedback/analysis", response_model=FeedbackAnalysisResponse)
async def analyze_feedback(req: FeedbackAnalysisRequest):
    """反馈分析接口。"""
    db = SessionLocal()
    try:
        start_time = _parse_iso_time(req.start_time)
        end_time = _parse_iso_time(req.end_time)
        rows = [
            row
            for row in db.query(Feedback).filter(Feedback.game_id == req.game_id).all()
            if _in_range(row.created_at, start_time, end_time)
        ]

        total = len(rows)
        pos = sum(1 for row in rows if (row.feedback_type or "").lower() == "positive")
        neg = sum(1 for row in rows if (row.feedback_type or "").lower() == "negative")
        neu = total - pos - neg

        freq: Dict[str, int] = {}
        for row in rows:
            if row.comment:
                for keyword in TextUtils.extract_keywords(row.comment, top_k=8):
                    freq[keyword] = freq.get(keyword, 0) + 1
        top_keywords = [word for word, _ in sorted(freq.items(), key=lambda item: item[1], reverse=True)[:10]]

        return FeedbackAnalysisResponse(
            total=total,
            positive=pos,
            negative=neg,
            neutral=neu,
            top_keywords=top_keywords,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"反馈分析失败: {exc}")
    finally:
        db.close()


@router.get("/query-stats", response_model=QueryStatsResponse)
async def get_query_stats(game_id: str = Query(..., description="游戏ID"), days: int = Query(7, ge=1, le=30)):
    """统计查询日志与反馈数据，用于前端仪表盘。"""
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=days)
        query_rows = [
            row
            for row in db.query(QueryLog).filter(QueryLog.game_id == game_id).all()
            if row.created_at and row.created_at >= since
        ]
        feedback_rows = [
            row
            for row in db.query(Feedback).filter(Feedback.game_id == game_id).all()
            if row.created_at and row.created_at >= since
        ]

        total_queries = len(query_rows)
        avg_confidence = round(
            sum(float(row.confidence or 0.0) for row in query_rows) / total_queries,
            3,
        ) if total_queries else 0.0
        avg_processing_time = round(
            sum(float(row.processing_time or 0.0) for row in query_rows) / total_queries,
            3,
        ) if total_queries else 0.0

        top_questions = [
            question
            for question, _ in Counter((row.question or "").strip() for row in query_rows if row.question).most_common(5)
        ]

        daily_counter = Counter(row.created_at.strftime("%Y-%m-%d") for row in query_rows if row.created_at)
        recent_days = []
        for offset in range(days - 1, -1, -1):
            day = (datetime.utcnow() - timedelta(days=offset)).strftime("%Y-%m-%d")
            recent_days.append(TrendPoint(date=day, count=daily_counter.get(day, 0), label="query"))

        return QueryStatsResponse(
            total_queries=total_queries,
            avg_confidence=avg_confidence,
            avg_processing_time=avg_processing_time,
            total_feedback=len(feedback_rows),
            positive_feedback=sum(1 for row in feedback_rows if row.feedback_type == "positive"),
            negative_feedback=sum(1 for row in feedback_rows if row.feedback_type == "negative"),
            top_questions=top_questions,
            recent_days=recent_days,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询统计失败: {exc}")
    finally:
        db.close()


@router.get("/heatmap", response_model=List[HeatmapPoint])
async def generate_heatmap(game_id: str = Query(..., description="游戏ID")):
    """按工作日和小时生成查询热力图。"""
    db = SessionLocal()
    try:
        rows = db.query(QueryLog).filter(QueryLog.game_id == game_id).all()
        bucket = Counter()
        for row in rows:
            if not row.created_at:
                continue
            weekday = row.created_at.weekday()
            hour = row.created_at.hour
            bucket[(weekday, hour)] += 1
        if not bucket:
            return [HeatmapPoint(x=0, y=0, value=0.0)]
        return [
            HeatmapPoint(x=float(weekday), y=float(hour), value=float(count))
            for (weekday, hour), count in sorted(bucket.items(), key=lambda item: item[1], reverse=True)[:48]
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"热力图生成失败: {exc}")
    finally:
        db.close()


@router.post("/feedback/classify", response_model=FeedbackClassifyResponse)
async def classify_feedback(req: FeedbackClassifyRequest):
    """使用规则增强分类器对用户反馈做主题归类。"""
    try:
        results = []
        for item in req.items:
            label, confidence = _classify_feedback_text(item.comment)
            results.append(ClassifiedItem(id=item.id, label=label, confidence=confidence))
        return FeedbackClassifyResponse(model="rule-augmented-feedback-v1", results=results)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"反馈分类失败: {exc}")


@router.get("/trends", response_model=List[TrendPoint])
async def get_trends(game_id: str = Query(...), days: int = Query(7, ge=1, le=30)):
    """返回最近N天的查询与反馈趋势。"""
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=days)
        query_rows = [
            row
            for row in db.query(QueryLog).filter(QueryLog.game_id == game_id).all()
            if row.created_at and row.created_at >= since
        ]
        feedback_rows = [
            row
            for row in db.query(Feedback).filter(Feedback.game_id == game_id).all()
            if row.created_at and row.created_at >= since
        ]

        query_counter = Counter(row.created_at.strftime("%Y-%m-%d") for row in query_rows)
        feedback_counter = Counter(row.created_at.strftime("%Y-%m-%d") for row in feedback_rows)

        trend_points: List[TrendPoint] = []
        for offset in range(days - 1, -1, -1):
            day = (datetime.utcnow() - timedelta(days=offset)).strftime("%Y-%m-%d")
            trend_points.append(TrendPoint(date=day, count=query_counter.get(day, 0), label="query"))
            trend_points.append(TrendPoint(date=day, count=feedback_counter.get(day, 0), label="feedback"))

        return trend_points
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"趋势统计失败: {exc}")
    finally:
        db.close()


@router.get("/priority-report", response_model=List[PriorityItem])
async def get_priority_report(game_id: str = Query(...)):
    """根据反馈主题、情绪与频次生成优先级报告。"""
    db = SessionLocal()
    try:
        rows = db.query(Feedback).filter(Feedback.game_id == game_id).all()
        return _build_priority_items(rows)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"优先级报告生成失败: {exc}")
    finally:
        db.close()


@router.get("/jira/status", response_model=JiraStatusResponse)
async def get_jira_status():
    try:
        client = JiraClient()
        return JiraStatusResponse(**client.get_status())
    except Exception as exc:
        logger.error("Jira status failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Jira 状态读取失败")


@router.post("/jira/export", response_model=JiraExportResponse)
async def export_priority_report_to_jira(req: JiraExportRequest):
    db = SessionLocal()
    try:
        client = JiraClient()
        rows = db.query(Feedback).filter(Feedback.game_id == req.game_id).all()
        priority_items = _build_priority_items(rows)[: req.limit]

        comments_by_label: Dict[str, List[str]] = defaultdict(list)
        for row in rows:
            label, _ = _classify_feedback_text(row.comment or "")
            if row.comment and len(comments_by_label[label]) < 3:
                comments_by_label[label].append(row.comment.strip())

        issues: List[JiraExportIssue] = []
        for item in priority_items:
            summary = f"[{req.game_id}] {item.label} - {item.title}"
            description_lines = [
                f"游戏 ID：{req.game_id}",
                f"优先级标签：{item.label}",
                f"评分：{item.score}",
                "来自 RAG 游戏问答系统的反馈优先级导出。",
                "",
                "示例反馈：",
            ]
            description_lines.extend(
                f"- {comment}" for comment in comments_by_label.get(item.label, []) or ["暂无用户评论样本"]
            )
            description = "\n".join(description_lines)

            if req.dry_run or not client.is_configured():
                issues.append(
                    JiraExportIssue(
                        summary=summary,
                        label=item.label,
                        score=item.score,
                        created=False,
                    )
                )
                continue

            created = client.create_issue(
                summary=summary,
                description=description,
                labels=[client.label_prefix, f"{client.label_prefix}-{req.game_id}", f"{client.label_prefix}-{item.label}"],
            )
            issues.append(
                JiraExportIssue(
                    summary=summary,
                    label=item.label,
                    score=item.score,
                    created=True,
                    jira_key=created.get("key"),
                    jira_url=created.get("url"),
                )
            )

        return JiraExportResponse(
            configured=client.is_configured(),
            dry_run=req.dry_run,
            issue_count=len(issues),
            issues=issues,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Jira export failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Jira 导出失败")
    finally:
        db.close()
