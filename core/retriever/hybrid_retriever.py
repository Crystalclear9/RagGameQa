# 混合检索器
from typing import List, Dict, Any
from core.retriever.vector_retriever import VectorRetriever
from core.retriever.inverted_index import InvertedIndex
from core.retriever.reranker import Reranker

class HybridRetriever:
    """混合检索器，结合向量和倒排索引"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.vector_retriever = VectorRetriever(game_id)
        self.inverted_index = InvertedIndex(game_id)
        self.reranker = Reranker(game_id)
    
    async def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        混合检索方法
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索到的文档列表
        """
        # 1. 向量检索
        vector_results = await self.vector_retriever.retrieve(query, top_k * 2)
        
        # 2. 倒排索引检索
        inverted_results = await self.inverted_index.retrieve(query, top_k * 2)
        
        # 3. 结果融合
        combined_results = self._combine_results(vector_results, inverted_results)
        
        # 4. 重排序
        reranked_results = await self.reranker.rerank(query, combined_results)
        
        # 5. 返回top_k结果
        return reranked_results[:top_k]
    
    def _combine_results(self, vector_results: List[Dict], inverted_results: List[Dict]) -> List[Dict]:
        """融合向量检索和倒排索引结果"""
        # 使用Reciprocal Rank Fusion (RRF)算法
        pass
