"""Background scheduler for recurring online knowledge sync."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.knowledge_base.knowledge_sync import KnowledgeSyncService
from utils.security import redact_sensitive_text

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEDULER_STATE_PATH = PROJECT_ROOT / "data" / "knowledge_sync_scheduler.json"


def _utc_now() -> datetime:
    return datetime.utcnow()


class KnowledgeSyncScheduler:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._state: Dict[str, Any] = self._load_state()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "enabled": bool(settings.KNOWLEDGE_SYNC_SCHEDULER_ENABLED),
            "interval_minutes": max(5, int(settings.KNOWLEDGE_SYNC_INTERVAL_MINUTES or 60)),
            "game_ids": [
                game_id.strip()
                for game_id in str(settings.KNOWLEDGE_SYNC_GAMES or "wow,lol,genshin").split(",")
                if game_id.strip()
            ],
            "max_results_per_query": max(1, min(int(settings.KNOWLEDGE_SYNC_MAX_RESULTS_PER_QUERY or 2), 5)),
            "last_run_at": None,
            "next_run_at": None,
            "last_result": None,
            "last_error": None,
        }

    def _load_state(self) -> Dict[str, Any]:
        state = self._default_state()
        if not SCHEDULER_STATE_PATH.exists():
            return state
        try:
            payload = json.loads(SCHEDULER_STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                state.update(payload)
        except Exception as exc:
            logger.warning("Failed to load sync scheduler state: %s", redact_sensitive_text(exc))
        return state

    def _save_state(self) -> None:
        SCHEDULER_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCHEDULER_STATE_PATH.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_status(self) -> Dict[str, Any]:
        return {
            **self._state,
            "running": bool(self._task and not self._task.done()),
        }

    async def restore(self) -> Dict[str, Any]:
        self._state = self._load_state()
        if self._state.get("enabled"):
            await self.start()
        return self.get_status()

    async def configure(
        self,
        enabled: bool,
        interval_minutes: Optional[int] = None,
        game_ids: Optional[List[str]] = None,
        max_results_per_query: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._state["enabled"] = bool(enabled)
        if interval_minutes is not None:
            self._state["interval_minutes"] = max(5, int(interval_minutes))
        if game_ids is not None:
            cleaned = [item.strip() for item in game_ids if str(item).strip()]
            self._state["game_ids"] = cleaned or self._default_state()["game_ids"]
        if max_results_per_query is not None:
            self._state["max_results_per_query"] = max(1, min(int(max_results_per_query), 5))

        if self._state["enabled"]:
            await self.start()
        else:
            await self.stop()
            self._state["next_run_at"] = None

        self._save_state()
        return self.get_status()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event = asyncio.Event()
        self._state["enabled"] = True
        self._task = asyncio.create_task(self._run_loop(), name="knowledge-sync-scheduler")
        self._save_state()

    async def stop(self) -> None:
        if self._task is None:
            return
        if self._stop_event is not None:
            self._stop_event.set()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            self._stop_event = None

    async def run_once(self, game_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        target_games = [item.strip() for item in (game_ids or self._state.get("game_ids") or []) if item.strip()]
        results = []
        started_at = _utc_now()

        for game_id in target_games:
            service = KnowledgeSyncService(game_id)
            result = await service.sync(
                max_results_per_query=int(self._state.get("max_results_per_query", 2)),
                include_crawler=bool(settings.KNOWLEDGE_SYNC_INCLUDE_CRAWLER),
                crawler_max_pages=max(1, int(settings.KNOWLEDGE_SYNC_CRAWLER_MAX_PAGES or 3)),
            )
            results.append(result)

        finished_at = _utc_now()
        self._state["last_run_at"] = finished_at.isoformat()
        self._state["last_error"] = None
        self._state["last_result"] = {
            "games": len(target_games),
            "total_stored_new_docs": sum(int(item.get("stored_new_docs", 0)) for item in results),
            "total_skipped_existing_docs": sum(int(item.get("skipped_existing_docs", 0)) for item in results),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "results": results,
        }
        self._state["next_run_at"] = (
            finished_at + timedelta(minutes=int(self._state.get("interval_minutes", 60)))
        ).isoformat() if self._state.get("enabled") else None
        self._save_state()
        return self._state["last_result"]

    async def _run_loop(self) -> None:
        while self._stop_event is not None and not self._stop_event.is_set():
            try:
                await self.run_once()
            except Exception as exc:
                self._state["last_error"] = redact_sensitive_text(exc)
                self._state["last_run_at"] = _utc_now().isoformat()
                self._state["next_run_at"] = (
                    _utc_now() + timedelta(minutes=int(self._state.get("interval_minutes", 60)))
                ).isoformat()
                self._save_state()
                logger.error("Scheduled knowledge sync failed: %s", redact_sensitive_text(exc), exc_info=True)

            wait_seconds = max(60, int(self._state.get("interval_minutes", 60)) * 60)
            if self._stop_event is None:
                break
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=wait_seconds)
            except asyncio.TimeoutError:
                continue


knowledge_sync_scheduler = KnowledgeSyncScheduler()
