# 语义压缩服务
from typing import List, Dict, Any
import logging
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

logger = logging.getLogger(__name__)

class SemanticCompression:
    """语义压缩服务"""
    
    def __init__(self, model_name: str = "bert-base-chinese"):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        logger.info(f"语义压缩服务初始化完成: {model_name}")
    
    async def compress_documents(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """
        压缩文档列表
        
        Args:
            documents: 文档对象列表
            
        Returns:
            压缩后的文档列表
        """
        try:
            compressed_docs = []
            
            for doc in documents:
                # 提取文档内容
                content = getattr(doc, 'content', '') if hasattr(doc, 'content') else str(doc)
                
                # 执行语义压缩
                compressed_content = await self._compress_text(content)
                
                # 构建压缩后的文档
                compressed_doc = {
                    'id': getattr(doc, 'id', None),
                    'content': compressed_content,
                    'metadata': {
                        'original_length': len(content),
                        'compressed_length': len(compressed_content),
                        'compression_ratio': len(compressed_content) / len(content) if content else 0,
                        'compression_method': 'semantic_extraction'
                    }
                }
                
                compressed_docs.append(compressed_doc)
            
            logger.info(f"成功压缩{len(documents)}个文档")
            return compressed_docs
            
        except Exception as e:
            logger.error(f"文档压缩失败: {str(e)}")
            return []
    
    async def _compress_text(self, text: str, max_length: int = 200) -> str:
        """
        压缩单个文本
        
        Args:
            text: 输入文本
            max_length: 最大长度
            
        Returns:
            压缩后的文本
        """
        try:
            if len(text) <= max_length:
                return text
            
            # 使用BERT提取关键信息
            sentences = self._split_into_sentences(text)
            
            if len(sentences) <= 1:
                return text[:max_length]
            
            # 计算句子重要性
            sentence_scores = await self._calculate_sentence_scores(sentences)
            
            # 选择最重要的句子
            selected_sentences = self._select_top_sentences(sentences, sentence_scores, max_length)
            
            return ' '.join(selected_sentences)
            
        except Exception as e:
            logger.error(f"文本压缩失败: {str(e)}")
            return text[:max_length]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割为句子"""
        import re
        
        # 简单的中文句子分割
        sentences = re.split(r'[。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    async def _calculate_sentence_scores(self, sentences: List[str]) -> List[float]:
        """
        计算句子重要性分数
        
        Args:
            sentences: 句子列表
            
        Returns:
            分数列表
        """
        try:
            scores = []
            
            for sentence in sentences:
                # 使用多种特征计算重要性
                score = 0.0
                
                # 1. 长度特征
                score += min(len(sentence) / 50, 1.0) * 0.2
                
                # 2. 关键词特征
                keywords = ['技能', '装备', '任务', '副本', '攻略', '方法', '步骤']
                keyword_count = sum(1 for keyword in keywords if keyword in sentence)
                score += keyword_count * 0.3
                
                # 3. 位置特征（前面的句子更重要）
                position_score = 1.0 - (len(scores) / len(sentences)) * 0.2
                score += position_score
                
                # 4. 语义特征（使用BERT）
                semantic_score = await self._calculate_semantic_score(sentence)
                score += semantic_score * 0.3
                
                scores.append(score)
            
            return scores
            
        except Exception as e:
            logger.error(f"句子分数计算失败: {str(e)}")
            return [1.0] * len(sentences)
    
    async def _calculate_semantic_score(self, sentence: str) -> float:
        """
        计算句子的语义重要性
        
        Args:
            sentence: 输入句子
            
        Returns:
            语义分数
        """
        try:
            # 使用BERT计算句子的语义表示
            inputs = self.tokenizer(sentence, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                # 使用CLS token的表示
                cls_embedding = outputs.last_hidden_state[:, 0, :]
                
                # 计算与重要概念的相似度
                important_concepts = ["技能", "装备", "任务", "方法", "攻略"]
                max_similarity = 0.0
                
                for concept in important_concepts:
                    concept_inputs = self.tokenizer(concept, return_tensors="pt")
                    with torch.no_grad():
                        concept_outputs = self.model(**concept_inputs)
                        concept_embedding = concept_outputs.last_hidden_state[:, 0, :]
                        
                        # 计算余弦相似度
                        similarity = torch.cosine_similarity(cls_embedding, concept_embedding, dim=1)
                        max_similarity = max(max_similarity, similarity.item())
                
                return max_similarity
                
        except Exception as e:
            logger.error(f"语义分数计算失败: {str(e)}")
            return 0.0
    
    def _select_top_sentences(self, sentences: List[str], scores: List[float], max_length: int) -> List[str]:
        """
        选择最重要的句子
        
        Args:
            sentences: 句子列表
            scores: 分数列表
            max_length: 最大长度
            
        Returns:
            选中的句子列表
        """
        try:
            # 按分数排序
            sentence_score_pairs = list(zip(sentences, scores))
            sentence_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            selected_sentences = []
            current_length = 0
            
            for sentence, score in sentence_score_pairs:
                if current_length + len(sentence) <= max_length:
                    selected_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            return selected_sentences
            
        except Exception as e:
            logger.error(f"句子选择失败: {str(e)}")
            return sentences[:1] if sentences else []
    
    def get_compression_stats(self, original_docs: List[Any], compressed_docs: List[Dict]) -> Dict[str, Any]:
        """
        获取压缩统计信息
        
        Args:
            original_docs: 原始文档
            compressed_docs: 压缩后文档
            
        Returns:
            统计信息
        """
        try:
            original_lengths = [len(getattr(doc, 'content', '')) for doc in original_docs]
            compressed_lengths = [len(doc['content']) for doc in compressed_docs]
            
            total_original = sum(original_lengths)
            total_compressed = sum(compressed_lengths)
            
            return {
                'total_documents': len(original_docs),
                'total_original_length': total_original,
                'total_compressed_length': total_compressed,
                'compression_ratio': total_compressed / total_original if total_original > 0 else 0,
                'space_saved': total_original - total_compressed,
                'space_saved_percentage': (total_original - total_compressed) / total_original * 100 if total_original > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"统计信息计算失败: {str(e)}")
            return {}