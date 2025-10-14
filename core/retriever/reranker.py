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
        """计算查询和文档的相关性分数"""
        # 使用BERT计算语义相似度
        inputs = self.tokenizer(
            query, 
            document, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # 使用CLS token的表示计算相似度
            query_repr = outputs.last_hidden_state[:, 0, :]
            doc_repr = outputs.last_hidden_state[:, 1, :]
            
            # 计算余弦相似度
            similarity = torch.cosine_similarity(query_repr, doc_repr, dim=1)
            return similarity.item()
