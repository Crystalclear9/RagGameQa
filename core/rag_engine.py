# RAG引擎主类
from typing import List, Dict, Any, Optional
import time
import logging
from core.retriever.hybrid_retriever import HybridRetriever
from core.generator.llm_generator import LLMGenerator
from core.knowledge_base.kb_manager import KnowledgeBaseManager
from config.database import SessionLocal, QueryLog

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG引擎主类，协调检索和生成模块"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.retriever = HybridRetriever(game_id)
        self.generator = LLMGenerator(game_id)
        self.knowledge_base = KnowledgeBaseManager(game_id)

    async def query(self, question: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理用户查询

        Args:
            question: 用户问题
            user_context: 用户上下文信息

        Returns:
            包含答案和相关信息的字典
        """
        t0 = time.time()
        # 1. 检索相关文档
        retrieved_docs = await self.retriever.retrieve(question)

        # 2. 生成答案
        answer = await self.generator.generate(
            question=question,
            context_docs=retrieved_docs,
            user_context=user_context,
        )

        processing_time = time.time() - t0

        # 3. 计算置信度与来源
        confidence = self._calculate_confidence(answer, retrieved_docs)
        sources = self._extract_sources(retrieved_docs)

        # 4. 记录查询日志
        await self._log_query(
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
            },
        }

    async def _log_query(
        self,
        question: str,
        answer: str,
        docs: List[Dict],
        confidence: float = 0.0,
        processing_time: float = 0.0,
        user_context: Optional[Dict] = None,
    ):
        """记录查询日志到数据库"""
        db = None
        try:
            db = SessionLocal()
            log = QueryLog(
                game_id=self.game_id,
                user_id=(user_context or {}).get("user_id", "anonymous"),
                question=question,
                answer=answer,
                confidence=confidence,
                processing_time=processing_time,
                retrieved_docs_count=len(docs),
                user_context=str(user_context or {}),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            if db is not None:
                db.rollback()
            logger.warning(f"记录查询日志失败: {e}")
        finally:
            if db is not None:
                db.close()

    def _calculate_confidence(self, answer: str, docs: List[Dict]) -> float:
        """根据检索分数与文档数量估算置信度（0-1）"""
        if not docs:
            return 0.5
        # 使用final_score或score的均值与最大值的加权
        scores: List[float] = []
        for d in docs:
            s = d.get("final_score") or d.get("score") or 0.0
            try:
                scores.append(float(s))
            except Exception:
                continue
        if not scores:
            return 0.5
        avg_s = sum(scores) / len(scores)
        max_s = max(scores)
        # 简单归一化到0-1区间（假设分数大致在[0,1]）
        conf = 0.6 * max(0.0, min(1.0, max_s)) + 0.4 * max(0.0, min(1.0, avg_s))
        return float(round(conf, 3))

    def _extract_sources(self, docs: List[Dict]) -> List[str]:
        """提取信息来源（title或source）"""
        sources: List[str] = []
        for d in docs:
            meta = d.get("metadata") or {}
            title = meta.get("title")
            source = meta.get("source")
            label = title or source
            if label:
                sources.append(str(label))
        # 去重保序
        seen = set()
        unique_sources = []
        for s in sources:
            if s not in seen:
                seen.add(s)
                unique_sources.append(s)
        return unique_sources[:10]
