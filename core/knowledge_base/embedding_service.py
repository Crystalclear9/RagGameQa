# 嵌入服务
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

class EmbeddingService:
    """嵌入服务，负责文本向量化"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.embedding_cache = {}
        self.cache_file = f"embeddings_{game_id}.pkl"
        self._load_cache()
    
    async def embed_text(self, text: str) -> np.ndarray:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        # 检查缓存
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        # 生成嵌入向量
        embedding = self.model.encode([text])[0]
        
        # 缓存结果
        self.embedding_cache[text] = embedding
        self._save_cache()
        
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量文本向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # 检查缓存
        for i, text in enumerate(texts):
            if text in self.embedding_cache:
                embeddings.append(self.embedding_cache[text])
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                embeddings.append(None)  # 占位符
        
        # 批量处理未缓存的文本
        if uncached_texts:
            new_embeddings = self.model.encode(uncached_texts)
            
            # 更新结果和缓存
            for i, embedding in zip(uncached_indices, new_embeddings):
                embeddings[i] = embedding
                self.embedding_cache[uncached_texts[i]] = embedding
        
        self._save_cache()
        return embeddings
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数 (0-1)
        """
        embedding1 = await self.embed_text(text1)
        embedding2 = await self.embed_text(text2)
        
        # 计算余弦相似度
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        
        return float(similarity)
    
    def _load_cache(self):
        """加载嵌入缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
            except Exception as e:
                print(f"加载嵌入缓存失败: {e}")
                self.embedding_cache = {}
    
    def _save_cache(self):
        """保存嵌入缓存"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
        except Exception as e:
            print(f"保存嵌入缓存失败: {e}")
