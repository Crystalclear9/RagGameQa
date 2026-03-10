"""Reranker with optional BERT support."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from config.settings import settings

try:
    import torch
    from transformers import AutoModel, AutoTokenizer
except Exception:  # pragma: no cover - handled at runtime
    torch = None  # type: ignore[assignment]
    AutoModel = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class Reranker:
    """Improve retrieval order by semantic relevance."""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.model_name = "bert-base-chinese"
        self.available = False
        self.tokenizer = None
        self.model = None

        if not settings.ENABLE_BERT_RERANKER:
            logger.info("BERT reranker disabled by config (ENABLE_BERT_RERANKER=False)")
            return

        if AutoTokenizer is None or AutoModel is None or torch is None:
            logger.warning("transformers/torch unavailable, reranker disabled")
            return

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.available = True
        except Exception as exc:
            logger.warning("Reranker model load failed, disabled: %s", exc)
            self.available = False

    async def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not documents:
            return documents
        if not self.available:
            for doc in documents:
                doc["final_score"] = float(doc.get("final_score") or doc.get("score") or 0.0)
            return sorted(documents, key=lambda x: x.get("final_score", 0.0), reverse=True)

        relevance_scores = []
        for doc in documents:
            score = await self._calculate_relevance(query, str(doc.get("content", "")))
            relevance_scores.append(score)

        for i, doc in enumerate(documents):
            base_score = float(doc.get("final_score") or doc.get("score") or 0.0)
            doc["final_score"] = 0.7 * base_score + 0.3 * relevance_scores[i]

        return sorted(documents, key=lambda x: x["final_score"], reverse=True)

    async def _calculate_relevance(self, query: str, document: str) -> float:
        if not self.available or self.tokenizer is None or self.model is None or torch is None:
            return self._fallback_similarity(query, document)
        try:
            q_inputs = self.tokenizer(
                query,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=True,
            )
            d_inputs = self.tokenizer(
                document,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            with torch.no_grad():
                q_out = self.model(**q_inputs).last_hidden_state[:, 0, :]
                d_out = self.model(**d_inputs).last_hidden_state[:, 0, :]
                similarity = torch.cosine_similarity(q_out, d_out, dim=1)
                return float(similarity.item())
        except Exception:
            return self._fallback_similarity(query, document)

    def _fallback_similarity(self, query: str, document: str) -> float:
        query_words = set(str(query or "").lower().split())
        doc_words = set(str(document or "").lower().split())
        if not query_words or not doc_words:
            return 0.0
        overlap = len(query_words.intersection(doc_words))
        union = len(query_words.union(doc_words))
        return overlap / union if union > 0 else 0.0
