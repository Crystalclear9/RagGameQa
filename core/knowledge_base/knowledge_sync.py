"""Online knowledge sync utilities."""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from config.database import Document, SessionLocal, create_tables, ensure_game_record
from config.settings import settings
from core.retriever.web_retriever import WebRetriever

try:
    from data.crawler.spider_cluster import SpiderCluster
except Exception:  # pragma: no cover - optional at runtime
    SpiderCluster = None  # type: ignore[assignment]

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional at runtime
    SentenceTransformer = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

GAME_NAMES = {
    "wow": "World of Warcraft",
    "lol": "League of Legends",
    "genshin": "Genshin Impact",
    "minecraft": "Minecraft",
    "valorant": "Valorant",
    "apex": "Apex Legends",
}

DEFAULT_SYNC_QUERIES = {
    "wow": ["warrior abilities", "dungeon finder", "talent tree", "gear progression"],
    "lol": ["jungle pathing", "summoner spells", "item build", "new player guide"],
    "genshin": ["elemental reactions", "artifact guide", "character build", "exploration tips"],
    "minecraft": ["crafting table", "survival mode", "nether portal", "enchanting"],
    "valorant": ["agent abilities", "buy round", "map positioning", "new player guide"],
    "apex": ["legend abilities", "drop locations", "weapon guide", "ranked tips"],
}


def get_default_sync_queries(game_id: str) -> List[str]:
    return list(DEFAULT_SYNC_QUERIES.get(game_id, ["新手指南", "基础玩法", "装备系统", "常见问题"]))


class KnowledgeSyncService:
    """Fetch online game knowledge and write it into the local database."""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.retriever = WebRetriever(game_id)
        self.embedding_model = self._load_embedding_model()

    def _load_embedding_model(self):
        if SentenceTransformer is None:
            return None
        try:
            return SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as exc:
            logger.warning("Embedding model unavailable for knowledge sync: %s", exc)
            return None

    async def sync(
        self,
        queries: Optional[List[str]] = None,
        max_results_per_query: int = 2,
        include_crawler: Optional[bool] = None,
        crawler_max_pages: Optional[int] = None,
    ) -> Dict[str, Any]:
        create_tables()
        sync_queries = [item.strip() for item in (queries or get_default_sync_queries(self.game_id)) if item and item.strip()]
        normalized_docs: List[Dict[str, Any]] = []
        now = datetime.utcnow().isoformat()

        for query in sync_queries:
            results = await self.retriever.retrieve(query, top_k=max_results_per_query)
            for item in results:
                normalized = self._normalize_doc(item, query, now)
                if normalized:
                    normalized_docs.append(normalized)

        use_crawler = settings.KNOWLEDGE_SYNC_INCLUDE_CRAWLER if include_crawler is None else bool(include_crawler)
        crawler_docs = await self._fetch_crawler_docs(
            max_pages=crawler_max_pages or max(1, int(settings.KNOWLEDGE_SYNC_CRAWLER_MAX_PAGES or 3)),
        ) if use_crawler else []
        normalized_docs.extend(crawler_docs)

        unique_docs = self._dedupe_docs(normalized_docs)
        store_result = self._store_docs(unique_docs)
        return {
            "game_id": self.game_id,
            "game_name": GAME_NAMES.get(self.game_id, self.game_id.upper()),
            "queries": sync_queries,
            "fetched_docs": len(unique_docs),
            "crawler_docs": len(crawler_docs),
            **store_result,
        }

    def _normalize_doc(self, item: Dict[str, Any], query: str, synced_at: str) -> Optional[Dict[str, Any]]:
        metadata = item.get("metadata") or {}
        content = str(item.get("content") or "").strip()
        title = str(metadata.get("title") or query).strip()
        source = str(metadata.get("source") or "").strip()
        if not content or not source:
            return None

        return {
            "title": title[:200],
            "content": content[:2000],
            "category": "web_sync",
            "source": source[:200],
            "doc_metadata": {
                "retrieval_type": item.get("type", "web"),
                "score": round(float(item.get("score", 0.0)), 4),
                "sync_query": query,
                "synced_at": synced_at,
            },
        }

    async def _fetch_crawler_docs(self, max_pages: int) -> List[Dict[str, Any]]:
        if SpiderCluster is None:
            return []
        try:
            cluster = SpiderCluster(self.game_id)
            items = await cluster.crawl_all_sources(max_pages=max_pages)
        except Exception as exc:
            logger.warning("Crawler sync skipped: %s", exc)
            return []

        normalized: List[Dict[str, Any]] = []
        now = datetime.utcnow().isoformat()
        for item in items:
            title = self._stringify_meta(item.get("title")) or self._stringify_meta(item.get("type")) or "Crawler Result"
            content = (
                self._stringify_meta(item.get("content"))
                or self._stringify_meta(item.get("description"))
                or self._stringify_meta(item.get("title"))
            )
            if not content:
                continue
            source_name = self._stringify_meta(item.get("source")) or "crawler"
            source_url = self._stringify_meta(item.get("url"))
            normalized.append(
                {
                    "title": title[:200],
                    "content": content[:2000],
                    "category": "crawler_sync",
                    "source": (source_url or source_name)[:200],
                    "doc_metadata": {
                        "retrieval_type": "crawler",
                        "crawler_source": source_name,
                        "synced_at": now,
                    },
                }
            )
        return normalized

    def _stringify_meta(self, value: Any) -> str:
        if value is None:
            return ""
        try:
            if hasattr(value, "get"):
                content = value.get("content")
                if content:
                    return str(content).strip()
            return str(value).strip()
        except Exception:
            return ""

    def _dedupe_docs(self, docs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: List[Dict[str, Any]] = []
        seen = set()
        for item in docs:
            key = f"{item.get('title')}|{item.get('source')}|{str(item.get('content'))[:120]}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _store_docs(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            ensure_game_record(db, self.game_id, GAME_NAMES.get(self.game_id))
            embeddings = self._encode_embeddings([item["content"] for item in docs])
            stored = 0
            skipped = 0

            for index, item in enumerate(docs):
                exists = (
                    db.query(Document)
                    .filter(
                        Document.game_id == self.game_id,
                        Document.title == item["title"],
                        Document.source == item["source"],
                        Document.content == item["content"],
                    )
                    .first()
                )
                if exists:
                    skipped += 1
                    continue

                embedding = embeddings[index] if index < len(embeddings) else None
                db.add(
                    Document(
                        game_id=self.game_id,
                        title=item["title"],
                        content=item["content"],
                        category=item["category"],
                        source=item["source"],
                        doc_metadata=json.dumps(item["doc_metadata"], ensure_ascii=False),
                        embedding=json.dumps(embedding, ensure_ascii=False) if embedding is not None else None,
                    )
                )
                stored += 1

            db.commit()
            return {
                "stored_new_docs": stored,
                "skipped_existing_docs": skipped,
                "last_sync_at": datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            db.rollback()
            logger.error("Knowledge sync failed: %s", exc)
            raise
        finally:
            db.close()

    def _encode_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        if self.embedding_model is None or not texts:
            return [None for _ in texts]
        try:
            vectors = self.embedding_model.encode(texts)
            return [vector.tolist() for vector in vectors]
        except Exception as exc:
            logger.warning("Embedding encode skipped during knowledge sync: %s", exc)
            return [None for _ in texts]


def build_sync_status(game_id: Optional[str] = None) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        query = db.query(Document).filter(Document.category.in_(["web_sync", "crawler_sync"]))
        if game_id:
            query = query.filter(Document.game_id == game_id)
        docs = query.order_by(Document.created_at.desc()).all()

        by_game = Counter((doc.game_id or "unknown") for doc in docs)
        recent_sources = []
        seen_sources = set()
        for doc in docs:
            source = str(doc.source or "").strip()
            if not source or source in seen_sources:
                continue
            seen_sources.add(source)
            recent_sources.append(source)
            if len(recent_sources) >= 5:
                break

        return {
            "enabled": settings.ENABLE_WEB_RETRIEVAL,
            "total_synced_docs": len(docs),
            "last_sync_at": docs[0].created_at.isoformat() if docs and docs[0].created_at else None,
            "games": [
                {"game_id": key, "synced_docs": value}
                for key, value in sorted(by_game.items(), key=lambda item: item[1], reverse=True)
            ],
            "recent_sources": recent_sources,
            "default_queries": get_default_sync_queries(game_id) if game_id else None,
        }
    finally:
        db.close()
