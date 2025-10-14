# 倒排索引
from typing import List, Dict, Any, Set
from collections import defaultdict
import jieba
import re

class InvertedIndex:
    """倒排索引检索器，基于关键词匹配"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.index = defaultdict(set)  # 词 -> 文档ID集合
        self.documents = {}  # 文档ID -> 文档内容
        self._build_index()
    
    async def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        倒排索引检索方法
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索到的文档列表
        """
        # 1. 分词
        query_terms = self._tokenize(query)
        
        # 2. 查找包含查询词的文档
        candidate_docs = self._find_candidate_docs(query_terms)
        
        # 3. 计算BM25分数
        scored_docs = self._calculate_bm25_scores(query_terms, candidate_docs)
        
        # 4. 排序并返回top_k结果
        sorted_docs = sorted(scored_docs, key=lambda x: x['score'], reverse=True)
        
        return sorted_docs[:top_k]
    
    def _tokenize(self, text: str) -> List[str]:
        """文本分词"""
        # 使用jieba进行中文分词
        words = jieba.lcut(text)
        # 过滤停用词和标点符号
        filtered_words = [word for word in words if len(word) > 1 and word.isalnum()]
        return filtered_words
    
    def _find_candidate_docs(self, terms: List[str]) -> Set[str]:
        """查找包含查询词的候选文档"""
        if not terms:
            return set()
        
        # 取所有词的文档集合的交集
        candidate_docs = self.index[terms[0]]
        for term in terms[1:]:
            candidate_docs = candidate_docs.intersection(self.index[term])
        
        return candidate_docs
    
    def _calculate_bm25_scores(self, query_terms: List[str], candidate_docs: Set[str]) -> List[Dict[str, Any]]:
        """计算BM25分数"""
        pass
    
    def _build_index(self):
        """构建倒排索引"""
        pass
