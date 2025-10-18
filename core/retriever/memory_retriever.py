# 内存模式检索器
import json
import os
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class MemoryRetriever:
    """内存模式检索器，从JSON文件加载数据"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
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
                
                # 生成嵌入向量
                for doc in game_docs:
                    content = doc.get('content', '')
                    if content:
                        embedding = self.model.encode([content])[0]
                        doc['embedding'] = embedding.tolist()
                        self.documents.append(doc)
                
                logger.info(f"加载了 {len(self.documents)} 个文档 for {self.game_id}")
            else:
                logger.warning(f"数据文件不存在: {data_file}")
        except Exception as e:
            logger.error(f"加载文档失败: {e}")
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索相关文档"""
        if not self.documents:
            return []
        
        try:
            # 将查询转换为向量
            query_vector = self.model.encode([query])[0]
            
            # 计算相似度
            results = []
            for doc in self.documents:
                if 'embedding' in doc:
                    doc_vector = np.array(doc['embedding'])
                    similarity = np.dot(query_vector, doc_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(doc_vector)
                    )
                    results.append({
                        'content': doc.get('content', ''),
                        'title': doc.get('title', ''),
                        'category': doc.get('category', ''),
                        'source': doc.get('source', ''),
                        'score': float(similarity)
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
