# 嵌入服务
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """嵌入向量服务"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"嵌入服务初始化完成: {model_name}")
    
    async def encode_text(self, text: str) -> np.ndarray:
        """
        编码单个文本
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        try:
            if not text.strip():
                # 返回零向量
                return np.zeros(self.model.get_sentence_embedding_dimension())
            
            embedding = self.model.encode([text])
            return embedding[0]
            
        except Exception as e:
            logger.error(f"文本编码失败: {str(e)}")
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    async def encode_texts(self, texts: List[str]) -> np.ndarray:
        """
        批量编码文本
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量矩阵
        """
        try:
            if not texts:
                return np.array([])
            
            # 过滤空文本
            filtered_texts = [text for text in texts if text.strip()]
            
            if not filtered_texts:
                return np.zeros((len(texts), self.model.get_sentence_embedding_dimension()))
            
            embeddings = self.model.encode(filtered_texts)
            
            # 如果有些文本被过滤了，需要补充零向量
            if len(filtered_texts) < len(texts):
                full_embeddings = np.zeros((len(texts), embeddings.shape[1]))
                j = 0
                for i, text in enumerate(texts):
                    if text.strip():
                        full_embeddings[i] = embeddings[j]
                        j += 1
                return full_embeddings
            
            return embeddings
            
        except Exception as e:
            logger.error(f"批量文本编码失败: {str(e)}")
            return np.zeros((len(texts), self.model.get_sentence_embedding_dimension()))
    
    async def encode_query(self, query: str, query_type: str = "general") -> np.ndarray:
        """
        编码查询文本（支持查询类型优化）
        
        Args:
            query: 查询文本
            query_type: 查询类型 (general, skill, equipment, quest)
            
        Returns:
            优化的嵌入向量
        """
        try:
            # 根据查询类型添加前缀
            prefixes = {
                "skill": "技能查询: ",
                "equipment": "装备查询: ",
                "quest": "任务查询: ",
                "general": ""
            }
            
            prefixed_query = prefixes.get(query_type, "") + query
            return await self.encode_text(prefixed_query)
            
        except Exception as e:
            logger.error(f"查询编码失败: {str(e)}")
            return await self.encode_text(query)
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self.model.get_sentence_embedding_dimension()
    
    def calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数
        """
        try:
            # 确保向量是numpy数组
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"相似度计算失败: {str(e)}")
            return 0.0
    
    def batch_similarity(self, query_vec: np.ndarray, doc_vectors: List[np.ndarray]) -> List[float]:
        """
        批量计算相似度
        
        Args:
            query_vec: 查询向量
            doc_vectors: 文档向量列表
            
        Returns:
            相似度分数列表
        """
        try:
            similarities = []
            for doc_vec in doc_vectors:
                similarity = self.calculate_similarity(query_vec, doc_vec)
                similarities.append(similarity)
            
            return similarities
            
        except Exception as e:
            logger.error(f"批量相似度计算失败: {str(e)}")
            return [0.0] * len(doc_vectors)
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.get_embedding_dimension(),
            "max_seq_length": self.model.max_seq_length,
            "device": str(self.model.device)
        }