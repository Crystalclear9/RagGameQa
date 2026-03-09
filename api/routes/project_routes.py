from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.database import Feedback, QueryLog, SessionLocal, database_status
from config.runtime_config import get_provider_snapshot
from core.rag_engine import RAGEngine
from utils.security import redact_sensitive_text

logger = logging.getLogger(__name__)
router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_SHOWCASE_PATH = PROJECT_ROOT / "data" / "project_showcase.json"
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "sample_data.json"
LOCAL_PROVIDER_CONFIG_PATH = PROJECT_ROOT / "config" / "local_provider_config.py"


def _load_json_file(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_project_showcase() -> Dict[str, Any]:
    if not PROJECT_SHOWCASE_PATH.exists():
        raise FileNotFoundError(f"项目展示数据不存在: {PROJECT_SHOWCASE_PATH}")
    return _load_json_file(PROJECT_SHOWCASE_PATH)


def _build_knowledge_coverage() -> Dict[str, Any]:
    if not SAMPLE_DATA_PATH.exists():
        return {"games": [], "total_documents": 0}

    payload = _load_json_file(SAMPLE_DATA_PATH)
    games = payload.get("games", [])
    documents = payload.get("documents", [])
    counts = Counter(doc.get("game_id", "unknown") for doc in documents)
    coverage = []
    for game in games:
        coverage.append(
            {
                "game_id": game.get("game_id"),
                "game_name": game.get("game_name"),
                "version": game.get("version"),
                "document_count": counts.get(game.get("game_id"), 0),
                "platforms": game.get("platforms", []),
                "languages": game.get("languages", []),
            }
        )
    return {
        "games": coverage,
        "total_documents": len(documents),
    }


def _build_runtime_metrics() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        query_rows = db.query(QueryLog).all()
        feedback_rows = db.query(Feedback).all()
        queries_by_game = Counter(row.game_id or "unknown" for row in query_rows)
        feedback_by_game = Counter(row.game_id or "unknown" for row in feedback_rows)
        provider_snapshot = get_provider_snapshot()
        return {
            "database": database_status(),
            "ai_provider": provider_snapshot["provider"],
            "model": provider_snapshot["model"],
            "live_llm_enabled": provider_snapshot["live_llm_enabled"],
            "python_config_file": str(LOCAL_PROVIDER_CONFIG_PATH.relative_to(PROJECT_ROOT)),
            "python_config_exists": LOCAL_PROVIDER_CONFIG_PATH.exists(),
            "storage_mode": provider_snapshot["storage_mode"],
            "total_queries": len(query_rows),
            "total_feedback": len(feedback_rows),
            "queries_by_game": dict(queries_by_game),
            "feedback_by_game": dict(feedback_by_game),
            "average_confidence": round(
                sum(float(row.confidence or 0.0) for row in query_rows) / len(query_rows),
                3,
            ) if query_rows else 0.0,
            "average_processing_time": round(
                sum(float(row.processing_time or 0.0) for row in query_rows) / len(query_rows),
                3,
            ) if query_rows else 0.0,
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


@router.get("/overview")
async def get_project_overview():
    try:
        showcase = _load_project_showcase()
        return {
            **showcase,
            "knowledge_coverage": _build_knowledge_coverage(),
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


@router.post("/demo-batch", response_model=DemoBatchResponse)
async def run_demo_batch(req: DemoBatchRequest):
    try:
        results: List[DemoBatchResult] = []
        for item in req.items:
            rag = RAGEngine(item.game_id)
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
