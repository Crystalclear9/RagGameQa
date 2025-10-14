# 知识库管理模块
"""
知识库管理模块

提供知识库的增删改查、嵌入向量管理和语义压缩功能。
支持动态知识库更新和优化。
"""

from .kb_manager import KnowledgeBaseManager
from .embedding_service import EmbeddingService
from .semantic_compression import SemanticCompression

__all__ = [
    "KnowledgeBaseManager",
    "EmbeddingService",
    "SemanticCompression"
]