"""Knowledge base manager."""

from __future__ import annotations

import ast
import logging
from typing import Any, Dict, List

from config.database import Document, get_db
from core.knowledge_base.embedding_service import EmbeddingService
from core.knowledge_base.semantic_compression import SemanticCompression

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.embedding_service = EmbeddingService()
        self.semantic_compression = SemanticCompression()
        logger.info("KnowledgeBaseManager initialized for %s", game_id)

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        db = None
        try:
            db = next(get_db())
            for doc_data in documents:
                content = str(doc_data.get("content", ""))
                embedding = await self.embedding_service.encode_text(content)
                document = Document(
                    game_id=self.game_id,
                    content=content,
                    title=str(doc_data.get("title", "")),
                    category=str(doc_data.get("category", "")),
                    source=str(doc_data.get("source", "")),
                    doc_metadata=str(doc_data.get("metadata", {})),
                    embedding=str(embedding.tolist()),
                )
                db.add(document)
            db.commit()
            logger.info("Added %s documents to KB for %s", len(documents), self.game_id)
            return True
        except Exception as exc:
            logger.error("Add documents failed: %s", exc)
            if db is not None:
                db.rollback()
            return False
        finally:
            if db is not None:
                db.close()

    async def search_documents(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        db = None
        try:
            db = next(get_db())
            query_embedding = await self.embedding_service.encode_text(query)
            documents = db.query(Document).filter(Document.game_id == self.game_id).all()

            results = []
            for doc in documents:
                if not doc.embedding:
                    continue
                try:
                    doc_embedding = ast.literal_eval(doc.embedding)
                    similarity = self._calculate_similarity(query_embedding, doc_embedding)
                except Exception:
                    continue
                try:
                    metadata = ast.literal_eval(doc.doc_metadata) if doc.doc_metadata else {}
                except Exception:
                    metadata = {}
                results.append(
                    {
                        "id": doc.id,
                        "content": doc.content,
                        "title": doc.title,
                        "category": doc.category,
                        "source": doc.source,
                        "metadata": metadata,
                        "similarity": similarity,
                    }
                )

            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
        except Exception as exc:
            logger.error("Search documents failed: %s", exc)
            return []
        finally:
            if db is not None:
                db.close()

    async def update_document(self, doc_id: int, updates: Dict[str, Any]) -> bool:
        db = None
        try:
            db = next(get_db())
            document = (
                db.query(Document)
                .filter(Document.id == doc_id, Document.game_id == self.game_id)
                .first()
            )
            if not document:
                return False

            for key, value in updates.items():
                if hasattr(document, key):
                    setattr(document, key, value)

            if "content" in updates:
                embedding = await self.embedding_service.encode_text(str(updates["content"]))
                document.embedding = str(embedding.tolist())

            db.commit()
            logger.info("Document updated: %s", doc_id)
            return True
        except Exception as exc:
            logger.error("Update document failed: %s", exc)
            if db is not None:
                db.rollback()
            return False
        finally:
            if db is not None:
                db.close()

    async def delete_document(self, doc_id: int) -> bool:
        db = None
        try:
            db = next(get_db())
            document = (
                db.query(Document)
                .filter(Document.id == doc_id, Document.game_id == self.game_id)
                .first()
            )
            if not document:
                return False
            db.delete(document)
            db.commit()
            logger.info("Document deleted: %s", doc_id)
            return True
        except Exception as exc:
            logger.error("Delete document failed: %s", exc)
            if db is not None:
                db.rollback()
            return False
        finally:
            if db is not None:
                db.close()

    async def compress_knowledge_base(self) -> Dict[str, Any]:
        db = None
        try:
            db = next(get_db())
            documents = db.query(Document).filter(Document.game_id == self.game_id).all()
            compressed_docs = await self.semantic_compression.compress_documents(documents)

            for index, doc in enumerate(documents):
                if index >= len(compressed_docs):
                    break
                doc.content = compressed_docs[index]["content"]
                doc.doc_metadata = str(compressed_docs[index]["metadata"])

            db.commit()
            original_count = len(documents)
            compressed_count = len(compressed_docs)
            ratio = compressed_count / original_count if original_count else 0.0
            return {
                "original_count": original_count,
                "compressed_count": compressed_count,
                "compression_ratio": ratio,
            }
        except Exception as exc:
            logger.error("Compress KB failed: %s", exc)
            return {}
        finally:
            if db is not None:
                db.close()

    def _calculate_similarity(self, vec1, vec2) -> float:
        import numpy as np

        a = np.array(vec1)
        b = np.array(vec2)
        denominator = (np.linalg.norm(a) * np.linalg.norm(b)) or 0.0
        if denominator == 0:
            return 0.0
        return float(np.dot(a, b) / denominator)

    def get_stats(self) -> Dict[str, Any]:
        db = None
        try:
            db = next(get_db())
            total_docs = db.query(Document).filter(Document.game_id == self.game_id).count()
            categories = (
                db.query(Document.category).filter(Document.game_id == self.game_id).distinct().all()
            )
            return {
                "game_id": self.game_id,
                "total_documents": total_docs,
                "categories": [item[0] for item in categories if item[0]],
                "embedding_service": type(self.embedding_service).__name__,
                "compression_service": type(self.semantic_compression).__name__,
            }
        except Exception as exc:
            logger.error("Get KB stats failed: %s", exc)
            return {}
        finally:
            if db is not None:
                db.close()
