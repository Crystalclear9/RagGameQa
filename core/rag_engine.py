# RAG引擎主类
from typing import List, Dict, Any, Optional
from core.retriever.hybrid_retriever import HybridRetriever
from core.generator.llm_generator import LLMGenerator
from core.knowledge_base.kb_manager import KnowledgeBaseManager

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
        # 1. 检索相关文档
        retrieved_docs = await self.retriever.retrieve(question)
        
        # 2. 生成答案
        answer = await self.generator.generate(
            question=question,
            context_docs=retrieved_docs,
            user_context=user_context
        )
        
        # 3. 记录查询日志
        await self._log_query(question, answer, retrieved_docs)
        
        return {
            "answer": answer,
            "retrieved_docs": retrieved_docs,
            "confidence": self._calculate_confidence(answer, retrieved_docs),
            "sources": self._extract_sources(retrieved_docs)
        }
    
    async def _log_query(self, question: str, answer: str, docs: List[Dict]):
        """记录查询日志"""
        pass
    
    def _calculate_confidence(self, answer: str, docs: List[Dict]) -> float:
        """计算答案置信度"""
        pass
    
    def _extract_sources(self, docs: List[Dict]) -> List[str]:
        """提取信息来源"""
        pass
