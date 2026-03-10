"""Vector retriever with graceful dependency fallback."""

from __future__ import annotations

import ast
import logging
from typing import Any, Dict, List, Tuple

import numpy as np
from sqlalchemy import func

from config.database import Document, get_db
from config.settings import settings

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - handled at runtime
    SentenceTransformer = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Semantic retriever based on sentence embeddings."""
    _model_cache: Dict[str, Any] = {}
    _vector_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.model = None
        if SentenceTransformer is None:
            logger.warning("sentence-transformers is unavailable, vector retrieval disabled")
            return
        try:
            self.model = self._model_cache.get(settings.EMBEDDING_MODEL)
            if self.model is None:
                self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
                self._model_cache[settings.EMBEDDING_MODEL] = self.model
        except Exception as exc:
            self.model = None
            logger.warning("Embedding model load failed, vector retrieval disabled: %s", exc)

    async def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if self.model is None:
            return []
        query_vector = self.model.encode([query])[0]
        return await self._search_similar(query_vector, top_k)

    def _get_signature(self) -> Dict[str, Any]:
        db = None
        try:
            db = next(get_db())
            count, updated_at = (
                db.query(func.count(Document.id), func.max(Document.updated_at))
                .filter(Document.game_id == self.game_id, Document.embedding.isnot(None))
                .one()
            )
            return {
                "count": int(count or 0),
                "updated_at": updated_at.isoformat() if updated_at else "",
            }
        except Exception:
            return {"count": 0, "updated_at": ""}
        finally:
            if db is not None:
                db.close()

    def _load_vector_cache(self) -> Tuple[np.ndarray | None, List[Dict[str, Any]]]:
        signature = self._get_signature()
        cached = self._vector_cache.get(self.game_id)
        if cached and cached.get("signature") == signature:
            return cached.get("matrix"), cached.get("meta", [])

        db = None
        try:
            db = next(get_db())
            docs = db.query(Document).filter(Document.game_id == self.game_id).all()
            vectors: List[np.ndarray] = []
            meta: List[Dict[str, Any]] = []
            for doc in docs:
                if not getattr(doc, "embedding", None):
                    continue
                try:
                    vec = np.array(ast.literal_eval(doc.embedding), dtype=float)
                    if vec.ndim != 1:
                        continue
                    vectors.append(vec)
                    meta.append(
                        {
                            "id": doc.id,
                            "content": doc.content,
                            "metadata": {"source": doc.source, "title": doc.title},
                        }
                    )
                except Exception:
                    continue

            matrix = np.vstack(vectors) if vectors else None
            self._vector_cache[self.game_id] = {
                "signature": signature,
                "matrix": matrix,
                "meta": meta,
            }
            return matrix, meta
        finally:
            if db is not None:
                db.close()

    async def _search_similar(self, query_vector: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        try:
            matrix, meta = self._load_vector_cache()
            if matrix is None or not meta:
                return []
            query_norm = np.linalg.norm(query_vector) + 1e-12
            matrix_norms = np.linalg.norm(matrix, axis=1) + 1e-12
            similarities = (matrix @ query_vector) / (matrix_norms * query_norm)
            top_indices = np.argsort(-similarities)[:top_k]

            scored = []
            for idx in top_indices:
                item = meta[int(idx)]
                scored.append(
                    {
                        "id": item["id"],
                        "content": item["content"],
                        "metadata": item["metadata"],
                        "score": float(similarities[int(idx)]),
                        "type": "vector",
                    }
                )
            return scored
        except Exception as exc:
            logger.warning("Vector retrieval failed: %s", exc)
            return []
