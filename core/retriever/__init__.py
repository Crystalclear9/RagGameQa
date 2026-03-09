# 检索模块
"""仅保留轻量导出，避免导入阶段触发向量依赖。"""

from .simple_memory_retriever import SimpleMemoryRetriever

__all__ = ["SimpleMemoryRetriever"]
