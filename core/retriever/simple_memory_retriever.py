# 简化版内存检索器
import json
import os
from typing import List, Dict, Any
import logging
import jieba

logger = logging.getLogger(__name__)

class SimpleMemoryRetriever:
    """简化版内存检索器，不使用向量模型"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.documents = []
        self._load_documents()
    
    def _load_documents(self):
        """从JSON文件加载文档"""
        try:
            data_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sample_data.json')
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 过滤当前游戏的文档
                game_docs = [doc for doc in data.get('documents', []) if doc.get('game_id') == self.game_id]
                self.documents = game_docs
                
                logger.info(f"加载了 {len(self.documents)} 个文档 for {self.game_id}")
            else:
                logger.warning(f"数据文件不存在: {data_file}")
        except Exception as e:
            logger.error(f"加载文档失败: {e}")
            # 如果加载失败，使用默认文档
            self.documents = [
                {
                    "game_id": self.game_id,
                    "title": "默认文档",
                    "content": "这是一个默认文档，用于测试问答功能。",
                    "category": "测试",
                    "source": "系统"
                }
            ]
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """简单的关键词匹配检索"""
        if not self.documents:
            return []
        
        try:
            query_lower = query.lower()
            query_tokens = self._tokenize(query_lower)
            results = []
            
            for doc in self.documents:
                content = doc.get('content', '').lower()
                title = doc.get('title', '').lower()
                category = doc.get('category', '').lower()
                doc_text = f"{title} {content} {category}"
                
                score = 0.0
                if query_lower and query_lower in doc_text:
                    score += 3.0

                overlap = 0
                for token in query_tokens:
                    if token in title:
                        overlap += 2
                    elif token in content or token in category:
                        overlap += 1

                score += float(overlap)
                
                if score > 0:
                    results.append({
                        'content': doc.get('content', ''),
                        'title': doc.get('title', ''),
                        'category': doc.get('category', ''),
                        'source': doc.get('source', ''),
                        'score': float(score),
                        'metadata': {
                            'title': doc.get('title', ''),
                            'source': doc.get('source', ''),
                        }
                    })
            
            # 按分数排序
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

    def _tokenize(self, text: str) -> List[str]:
        tokens = []
        for token in jieba.cut(text):
            token = token.strip()
            if len(token) >= 2:
                tokens.append(token)
        if not tokens and text:
            tokens.append(text)
        return list(dict.fromkeys(tokens))
