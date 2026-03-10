from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.database import QueryLog, SessionLocal, ensure_game_record
from config.settings import settings
from core.retriever.web_retriever import WebRetriever
from utils.security import redact_sensitive_text, sanitize_user_context

logger = logging.getLogger(__name__)


class RAGEngine:
    """Main RAG pipeline orchestrator."""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.mode = "memory"
        self.retriever = None
        self.generator = None
        self.knowledge_base = None
        self.web_retriever = WebRetriever(game_id) if settings.ENABLE_WEB_RETRIEVAL else None

        preferred_mode = (settings.RAG_DATA_MODE or "database").strip().lower()
        if preferred_mode not in {"database", "memory", "auto"}:
            preferred_mode = "database"

        if preferred_mode == "memory":
            self._init_memory_mode()
            return

        if self._init_database_mode():
            return

        logger.warning("Database mode init failed for %s, fallback to memory mode", game_id)
        self._init_memory_mode()

    def _init_database_mode(self) -> bool:
        try:
            from core.generator.llm_generator import LLMGenerator
            from core.retriever.hybrid_retriever import HybridRetriever

            self.retriever = HybridRetriever(self.game_id)
            self.generator = LLMGenerator(self.game_id)
            self.knowledge_base = None
            try:
                from core.knowledge_base.kb_manager import KnowledgeBaseManager

                self.knowledge_base = KnowledgeBaseManager(self.game_id)
            except Exception as kb_exc:
                logger.warning("Knowledge base manager disabled: %s", redact_sensitive_text(kb_exc))
            self.mode = "database"
            logger.info("RAG engine initialized in database mode for %s", self.game_id)
            return True
        except Exception as exc:
            logger.warning("Database mode init error: %s", redact_sensitive_text(exc))
            self.retriever = None
            self.generator = None
            self.knowledge_base = None
            return False

    def _init_memory_mode(self) -> None:
        from core.generator.memory_llm_generator import MemoryLLMGenerator
        from core.retriever.simple_memory_retriever import SimpleMemoryRetriever

        self.retriever = SimpleMemoryRetriever(self.game_id)
        self.generator = MemoryLLMGenerator(self.game_id)
        self.knowledge_base = None
        self.mode = "memory"
        logger.info("RAG engine initialized in memory mode for %s", self.game_id)

    async def query(
        self,
        question: str,
        user_context: Optional[Dict] = None,
        top_k: Optional[int] = None,
        enable_web_retrieval: Optional[bool] = None,
    ) -> Dict[str, Any]:
        t0 = time.time()
        top_k = int(top_k or settings.TOP_K_RESULTS)
        top_k = max(1, min(top_k, 20))
        use_web = settings.ENABLE_WEB_RETRIEVAL if enable_web_retrieval is None else bool(enable_web_retrieval)

        retrieved_docs = await self.retriever.retrieve(question, top_k=top_k)
        web_docs: List[Dict[str, Any]] = []

        if self._should_augment_with_web(retrieved_docs, use_web):
            web_docs = await self.web_retriever.retrieve(
                question,
                top_k=max(1, settings.WEB_RETRIEVAL_MAX_RESULTS),
            )
            if web_docs:
                retrieved_docs = self._merge_retrieved_docs(retrieved_docs, web_docs, limit=top_k + len(web_docs))
                await self._persist_web_docs(web_docs)

        answer = await self.generator.generate(
            question=question,
            context_docs=retrieved_docs,
            user_context=user_context,
        )

        processing_time = time.time() - t0
        confidence = self._calculate_confidence(answer, retrieved_docs)
        sources = self._extract_sources(retrieved_docs)

        query_log_id = await self._log_query(
            question=question,
            answer=answer,
            docs=retrieved_docs,
            confidence=confidence,
            processing_time=processing_time,
            user_context=user_context or {},
        )

        return {
            "answer": answer,
            "retrieved_docs": retrieved_docs,
            "confidence": confidence,
            "sources": sources,
            "metadata": {
                "processing_time": round(processing_time, 3),
                "retrieved": len(retrieved_docs),
                "query_log_id": query_log_id,
                "ai_provider": getattr(self.generator, "ai_provider", "memory"),
                "retrieval_mode": self.mode,
                "web_augmented": bool(web_docs),
                "web_docs": len(web_docs),
            },
        }

    def _should_augment_with_web(self, docs: List[Dict[str, Any]], use_web: bool) -> bool:
        if not use_web or self.web_retriever is None:
            return False
        if len(docs) < settings.WEB_RETRIEVAL_TRIGGER_DOC_COUNT:
            return True

        top_score = 0.0
        for doc in docs:
            score = doc.get("final_score", doc.get("score", 0.0))
            try:
                top_score = max(top_score, float(score))
            except Exception:
                continue
        return top_score <= 0.55

    def _merge_retrieved_docs(self, local_docs: List[Dict[str, Any]], web_docs: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        merged = []
        seen_keys = set()

        for item in [*local_docs, *web_docs]:
            metadata = item.get("metadata") or {}
            source = str(metadata.get("source") or "")
            title = str(metadata.get("title") or "")
            content = str(item.get("content") or "")
            key = f"{source}|{title}|{content[:80]}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            merged.append(item)
            if len(merged) >= limit:
                break
        return merged

    async def _persist_web_docs(self, web_docs: List[Dict[str, Any]]) -> None:
        if self.mode != "database" or self.knowledge_base is None or not web_docs:
            return
        try:
            docs_to_store = []
            now = datetime.utcnow().isoformat()
            for doc in web_docs:
                metadata = doc.get("metadata") or {}
                docs_to_store.append(
                    {
                        "title": metadata.get("title", "Web Result"),
                        "content": doc.get("content", ""),
                        "category": "web_retrieval",
                        "source": metadata.get("source", ""),
                        "metadata": {
                            "retrieval_type": "web",
                            "fetched_at": now,
                        },
                    }
                )
            await self.knowledge_base.add_documents(docs_to_store)
        except Exception as exc:
            logger.warning("Persist web docs failed: %s", redact_sensitive_text(exc))

    async def _log_query(
        self,
        question: str,
        answer: str,
        docs: List[Dict],
        confidence: float = 0.0,
        processing_time: float = 0.0,
        user_context: Optional[Dict] = None,
    ) -> Optional[int]:
        db = None
        try:
            db = SessionLocal()
            ensure_game_record(db, self.game_id)
            safe_question = redact_sensitive_text(question)
            safe_answer = redact_sensitive_text(answer)
            safe_user_context = sanitize_user_context(user_context or {})
            log = QueryLog(
                game_id=self.game_id,
                user_id=safe_user_context.get("user_id", "anonymous"),
                question=safe_question,
                answer=safe_answer,
                confidence=confidence,
                processing_time=processing_time,
                retrieved_docs_count=len(docs),
                user_context=str(safe_user_context),
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return int(log.id)
        except Exception as exc:
            if db is not None:
                db.rollback()
            logger.warning("Failed to write query log: %s", redact_sensitive_text(exc))
            return None
        finally:
            if db is not None:
                db.close()

    def _calculate_confidence(self, answer: str, docs: List[Dict]) -> float:
        if not docs:
            return 0.45
        scores: List[float] = []
        for doc in docs:
            score = doc.get("final_score", doc.get("score", 0.0))
            try:
                value = float(score)
                if value > 1.0:
                    value = 1.0
                if value < 0.0:
                    value = 0.0
                scores.append(value)
            except Exception:
                continue
        if not scores:
            return 0.5
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        conf = 0.6 * max_score + 0.4 * avg_score
        return float(round(conf, 3))

    def _extract_sources(self, docs: List[Dict]) -> List[str]:
        sources: List[str] = []
        for doc in docs:
            metadata = doc.get("metadata") or {}
            title = metadata.get("title")
            source = metadata.get("source")
            label = title or source
            if label:
                sources.append(str(label))

        seen = set()
        unique_sources = []
        for source in sources:
            if source in seen:
                continue
            seen.add(source)
            unique_sources.append(source)
        return unique_sources[:10]
