# 知识库管理模块
"""Graceful knowledge base package exports."""

from __future__ import annotations

KnowledgeBaseManager = None
EmbeddingService = None
SemanticCompression = None

try:
    from .kb_manager import KnowledgeBaseManager  # type: ignore[assignment]
except Exception:
    KnowledgeBaseManager = None  # type: ignore[assignment]

try:
    from .embedding_service import EmbeddingService  # type: ignore[assignment]
except Exception:
    EmbeddingService = None  # type: ignore[assignment]

try:
    from .semantic_compression import SemanticCompression  # type: ignore[assignment]
except Exception:
    SemanticCompression = None  # type: ignore[assignment]

__all__ = ["KnowledgeBaseManager", "EmbeddingService", "SemanticCompression"]
