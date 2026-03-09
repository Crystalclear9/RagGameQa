# 核心RAG框架模块
"""轻量导出核心入口，避免在导入阶段拉起重量依赖。"""

from .rag_engine import RAGEngine

__all__ = ["RAGEngine"]
