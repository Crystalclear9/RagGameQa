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
        
        # 3. 结果融合（RRF）
        combined_results = self._combine_results(vector_results, inverted_results)
        
        # 4. 重排序
        reranked_results = await self.reranker.rerank(query, combined_results)
        
        # 5. 返回top_k结果
        return reranked_results[:top_k]
    
    def _combine_results(self, vector_results: List[Dict], inverted_results: List[Dict]) -> List[Dict]:
        """融合向量检索和倒排索引结果（Reciprocal Rank Fusion, RRF）"""
        k = 60  # RRF平滑参数
        rank_scores: Dict[str, float] = {}
        id_to_doc: Dict[str, Dict[str, Any]] = {}

        # 为每个来源结果赋予排名分数
        for results in (vector_results, inverted_results):
            for rank, doc in enumerate(results, start=1):
                # 使用内容+标题作为key（无ID场景下的退化方案）
                doc_id = str(doc.get('id') or (doc.get('metadata', {}).get('title') or '')) + '|' + doc.get('content', '')[:32]
                id_to_doc[doc_id] = doc
                rank_scores[doc_id] = rank_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

        # 汇总为列表并按分数排序
        fused = []
        for doc_id, score in rank_scores.items():
            doc = id_to_doc[doc_id].copy()
            doc['final_score'] = float(score)
            fused.append(doc)

        fused.sort(key=lambda x: x['final_score'], reverse=True)
        return fused
