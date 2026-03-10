from __future__ import annotations

import json
import logging
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func

from config.database import Document, Feedback, Game, QueryLog, SessionLocal, database_status
from config.runtime_config import get_provider_snapshot
from config.settings import settings
from core.knowledge_base.knowledge_sync import (
    KnowledgeSyncService,
    build_sync_status,
    get_default_sync_queries,
)
from core.knowledge_base.sync_scheduler import knowledge_sync_scheduler
from core.rag_engine import RAGEngine
from integrations.jira_client import JiraClient
from utils.security import redact_sensitive_text

logger = logging.getLogger(__name__)
router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_SHOWCASE_PATH = PROJECT_ROOT / "data" / "project_showcase.json"
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "sample_data.json"
LOCAL_PROVIDER_CONFIG_PATH = PROJECT_ROOT / "config" / "local_provider_config.py"
_SHOWCASE_CACHE: Dict[str, Any] = {"mtime": None, "payload": None}
_DEMO_ENGINE_CACHE: "OrderedDict[str, RAGEngine]" = OrderedDict()


def _load_json_file(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_project_showcase() -> Dict[str, Any]:
    if not PROJECT_SHOWCASE_PATH.exists():
        raise FileNotFoundError(f"项目展示数据不存在: {PROJECT_SHOWCASE_PATH}")
    mtime = PROJECT_SHOWCASE_PATH.stat().st_mtime
    if _SHOWCASE_CACHE["mtime"] == mtime and _SHOWCASE_CACHE["payload"] is not None:
        return _SHOWCASE_CACHE["payload"]
    payload = _load_json_file(PROJECT_SHOWCASE_PATH)
    _SHOWCASE_CACHE["mtime"] = mtime
    _SHOWCASE_CACHE["payload"] = payload
    return payload


def _parse_json_text(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value


def _get_demo_engine(game_id: str) -> RAGEngine:
    engine = _DEMO_ENGINE_CACHE.get(game_id)
    if engine is not None:
        _DEMO_ENGINE_CACHE.move_to_end(game_id)
        return engine

    engine = RAGEngine(game_id)
    _DEMO_ENGINE_CACHE[game_id] = engine
    if len(_DEMO_ENGINE_CACHE) > 6:
        _DEMO_ENGINE_CACHE.popitem(last=False)
    return engine
    if value is None or value == "":
        return []
    try:
        return json.loads(str(value))
    except Exception:
        return value


def _build_knowledge_coverage() -> Dict[str, Any]:
    payload = _load_json_file(SAMPLE_DATA_PATH) if SAMPLE_DATA_PATH.exists() else {"games": [], "documents": []}
    sample_games = {game.get("game_id"): game for game in payload.get("games", []) if game.get("game_id")}
    sample_counts = Counter(doc.get("game_id", "unknown") for doc in payload.get("documents", []))

    db = SessionLocal()
    try:
        game_rows = db.query(Game).all()
        doc_counts = Counter(
            (
                getattr(row, "game_id", None)
                or (row[0] if isinstance(row, tuple) and row else None)
                or "unknown"
            )
            for row in db.query(Document.game_id).all()
        )
        has_db_data = bool(game_rows) or bool(doc_counts)
        if not has_db_data:
            raise ValueError("database coverage empty")

        games_by_id = {row.game_id: row for row in game_rows if row.game_id}
        game_ids = sorted(set(sample_games) | set(games_by_id) | set(doc_counts))
        coverage = []
        for game_id in game_ids:
            row = games_by_id.get(game_id)
            sample = sample_games.get(game_id, {})
            coverage.append(
                {
                    "game_id": game_id,
                    "game_name": getattr(row, "game_name", None) or sample.get("game_name") or game_id,
                    "version": getattr(row, "version", None) or sample.get("version") or "current",
                    "document_count": doc_counts.get(game_id, 0),
                    "platforms": _parse_json_text(getattr(row, "platforms", None)) or sample.get("platforms", []),
                    "languages": _parse_json_text(getattr(row, "languages", None)) or sample.get("languages", []),
                }
            )

        return {
            "games": coverage,
            "total_documents": sum(doc_counts.values()),
            "source": "database",
        }
    except Exception:
        coverage = []
        for game in payload.get("games", []):
            coverage.append(
                {
                    "game_id": game.get("game_id"),
                    "game_name": game.get("game_name"),
                    "version": game.get("version"),
                    "document_count": sample_counts.get(game.get("game_id"), 0),
                    "platforms": game.get("platforms", []),
                    "languages": game.get("languages", []),
                }
            )
        return {
            "games": coverage,
            "total_documents": len(payload.get("documents", [])),
            "source": "sample_data",
        }
    finally:
        db.close()


def _build_runtime_metrics() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        total_queries, avg_confidence, avg_processing_time = (
            db.query(
                func.count(QueryLog.id),
                func.avg(QueryLog.confidence),
                func.avg(QueryLog.processing_time),
            )
            .one()
        )
        total_feedback = int(db.query(func.count(Feedback.id)).scalar() or 0)
        queries_by_game = {
            str(game_id or "unknown"): int(count or 0)
            for game_id, count in db.query(QueryLog.game_id, func.count(QueryLog.id)).group_by(QueryLog.game_id).all()
        }
        feedback_by_game = {
            str(game_id or "unknown"): int(count or 0)
            for game_id, count in db.query(Feedback.game_id, func.count(Feedback.id)).group_by(Feedback.game_id).all()
        }
        provider_snapshot = get_provider_snapshot()
        scheduler_status = knowledge_sync_scheduler.get_status()
        return {
            "database": database_status(),
            "ai_provider": provider_snapshot["provider"],
            "model": provider_snapshot["model"],
            "live_llm_enabled": provider_snapshot["live_llm_enabled"],
            "rag_data_mode": settings.RAG_DATA_MODE,
            "web_retrieval_enabled": settings.ENABLE_WEB_RETRIEVAL,
            "web_retrieval_trigger_doc_count": settings.WEB_RETRIEVAL_TRIGGER_DOC_COUNT,
            "web_retrieval_max_results": settings.WEB_RETRIEVAL_MAX_RESULTS,
            "knowledge_sync_scheduler_enabled": scheduler_status.get("enabled", False),
            "knowledge_sync_interval_minutes": scheduler_status.get("interval_minutes", settings.KNOWLEDGE_SYNC_INTERVAL_MINUTES),
            "jira_configured": JiraClient().is_configured(),
            "python_config_file": str(LOCAL_PROVIDER_CONFIG_PATH.relative_to(PROJECT_ROOT)),
            "python_config_exists": LOCAL_PROVIDER_CONFIG_PATH.exists(),
            "storage_mode": provider_snapshot["storage_mode"],
            "total_queries": int(total_queries or 0),
            "total_feedback": total_feedback,
            "queries_by_game": dict(queries_by_game),
            "feedback_by_game": dict(feedback_by_game),
            "average_confidence": round(float(avg_confidence or 0.0), 3),
            "average_processing_time": round(float(avg_processing_time or 0.0), 3),
        }
    finally:
        db.close()


class DemoBatchItem(BaseModel):
    game_id: str = Field(..., description="游戏 ID")
    question: str = Field(..., description="要演示的问题")
    user_context: Optional[Dict[str, Any]] = Field(default=None)


class DemoBatchRequest(BaseModel):
    items: List[DemoBatchItem] = Field(..., min_length=1, max_length=10)


class DemoBatchResult(BaseModel):
    game_id: str
    question: str
    answer: str
    confidence: float
    sources: List[str]
    processing_time: float


class DemoBatchResponse(BaseModel):
    results: List[DemoBatchResult]


class KnowledgeSyncRequest(BaseModel):
    game_id: str = Field(..., description="游戏 ID")
    queries: Optional[List[str]] = Field(default=None, description="自定义联网查询词")
    max_results_per_query: int = Field(default=2, ge=1, le=5, description="每个查询拉取的结果数")
    include_crawler: bool = Field(default=False, description="是否同时尝试爬虫源")
    crawler_max_pages: int = Field(default=3, ge=1, le=20, description="爬虫最大页数")


class KnowledgeSyncSchedulerRequest(BaseModel):
    enabled: bool = Field(..., description="是否启用自动同步")
    interval_minutes: int = Field(default=60, ge=5, le=1440, description="同步间隔，单位分钟")
    game_ids: List[str] = Field(default_factory=lambda: ["wow", "lol", "genshin"], description="要同步的游戏 ID")
    max_results_per_query: int = Field(default=2, ge=1, le=5, description="每个查询同步的文档数")


class KnowledgeSyncSchedulerRunRequest(BaseModel):
    game_ids: Optional[List[str]] = Field(default=None, description="临时指定执行的游戏 ID 列表")


@router.get("/overview")
async def get_project_overview():
    try:
        showcase = _load_project_showcase()
        return {
            **showcase,
            "knowledge_coverage": _build_knowledge_coverage(),
            "knowledge_sync": build_sync_status(),
            "knowledge_sync_scheduler": knowledge_sync_scheduler.get_status(),
            "jira": JiraClient().get_status(),
            "runtime_metrics": _build_runtime_metrics(),
        }
    except Exception as exc:
        logger.error("Failed to load project overview: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="项目概览加载失败")


@router.get("/module-audit")
async def get_module_audit():
    try:
        showcase = _load_project_showcase()
        audit_items = showcase.get("module_audit", [])
        summary = {
            "implemented": sum(1 for item in audit_items if item.get("status") == "implemented"),
            "partial": sum(1 for item in audit_items if item.get("status") == "partial"),
            "missing": sum(1 for item in audit_items if item.get("status") == "missing"),
            "total": len(audit_items),
        }
        return {
            "summary": summary,
            "items": audit_items,
        }
    except Exception as exc:
        logger.error("Failed to load module audit: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="模块核查加载失败")


@router.get("/knowledge-sync/status")
async def get_knowledge_sync_status(game_id: Optional[str] = None):
    try:
        status = build_sync_status(game_id)
        status["scheduler"] = knowledge_sync_scheduler.get_status()
        if game_id:
            status["game_id"] = game_id
            status["default_queries"] = get_default_sync_queries(game_id)
        return status
    except Exception as exc:
        logger.error("Knowledge sync status failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="联网知识同步状态读取失败")


@router.post("/knowledge-sync")
async def run_knowledge_sync(req: KnowledgeSyncRequest):
    try:
        service = KnowledgeSyncService(req.game_id)
        return await service.sync(
            req.queries,
            req.max_results_per_query,
            include_crawler=req.include_crawler,
            crawler_max_pages=req.crawler_max_pages,
        )
    except Exception as exc:
        logger.error("Knowledge sync failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="联网知识同步失败")


@router.get("/knowledge-sync/scheduler")
async def get_knowledge_sync_scheduler():
    try:
        return knowledge_sync_scheduler.get_status()
    except Exception as exc:
        logger.error("Knowledge sync scheduler status failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="自动同步状态读取失败")


@router.post("/knowledge-sync/scheduler")
async def configure_knowledge_sync_scheduler(req: KnowledgeSyncSchedulerRequest):
    try:
        return await knowledge_sync_scheduler.configure(
            enabled=req.enabled,
            interval_minutes=req.interval_minutes,
            game_ids=req.game_ids,
            max_results_per_query=req.max_results_per_query,
        )
    except Exception as exc:
        logger.error("Knowledge sync scheduler update failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="自动同步配置失败")


@router.post("/knowledge-sync/scheduler/run")
async def run_knowledge_sync_scheduler_once(req: KnowledgeSyncSchedulerRunRequest):
    try:
        return await knowledge_sync_scheduler.run_once(game_ids=req.game_ids)
    except Exception as exc:
        logger.error("Knowledge sync scheduler manual run failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="自动同步手动执行失败")


@router.post("/demo-batch", response_model=DemoBatchResponse)
async def run_demo_batch(req: DemoBatchRequest):
    try:
        results: List[DemoBatchResult] = []
        for item in req.items:
            rag = _get_demo_engine(item.game_id)
            response = await rag.query(item.question, item.user_context or {"user_id": "demo-batch"})
            results.append(
                DemoBatchResult(
                    game_id=item.game_id,
                    question=item.question,
                    answer=response.get("answer", ""),
                    confidence=float(response.get("confidence", 0.0)),
                    sources=response.get("sources", []),
                    processing_time=float(response.get("metadata", {}).get("processing_time", 0.0)),
                )
            )
        return DemoBatchResponse(results=results)
    except Exception as exc:
        logger.error("Batch demo failed: %s", redact_sensitive_text(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="批量演示失败")
