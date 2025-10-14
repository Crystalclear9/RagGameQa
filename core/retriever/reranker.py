# 重排序模型
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModel

class Reranker:
    """重排序模型，优化检索结果的相关性排序"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.model_name = "bert-base-chinese"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
    
    async def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重排序方法
        
        Args:
            query: 查询文本
            documents: 待排序的文档列表
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return documents
        
        # 1. 计算查询-文档相关性分数
        relevance_scores = []
        for doc in documents:
            score = await self._calculate_relevance(query, doc['content'])
            relevance_scores.append(score)
        
        # 2. 结合原始分数和相关性分数
        for i, doc in enumerate(documents):
            original_score = doc.get('score', 0)
            relevance_score = relevance_scores[i]
            # 加权融合
            doc['final_score'] = 0.7 * original_score + 0.3 * relevance_score
        
        # 3. 按最终分数排序
        reranked_docs = sorted(documents, key=lambda x: x['final_score'], reverse=True)
        
        return reranked_docs
    
    async def _calculate_relevance(self, query: str, document: str) -> float:
        """计算查询和文档的相关性分数（双塔CLS余弦）"""
        try:
            # 分别编码查询与文档，取CLS
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
                return similarity.item()
        except Exception:
            return self._fallback_similarity(query, document)
    
    def _fallback_similarity(self, query: str, document: str) -> float:
        """备用相似度计算方法"""
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        
        if not query_words or not doc_words:
            return 0.0
        
        intersection = len(query_words.intersection(doc_words))
        union = len(query_words.union(doc_words))
        
        return intersection / union if union > 0 else 0.0
