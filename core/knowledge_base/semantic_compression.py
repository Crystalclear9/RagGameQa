# 语义压缩
from typing import List, Dict, Any
import re
from transformers import AutoTokenizer, AutoModel
import torch

class SemanticCompression:
    """语义压缩，减少存储空间同时保持语义信息"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
        self.model = AutoModel.from_pretrained("bert-base-chinese")
        self.compression_ratio = 0.7  # 压缩比
    
    async def compress(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        压缩文档列表
        
        Args:
            documents: 原始文档列表
            
        Returns:
            压缩后的文档列表
        """
        compressed_docs = []
        
        for doc in documents:
            compressed_doc = await self._compress_single_doc(doc)
            compressed_docs.append(compressed_doc)
        
        return compressed_docs
    
    async def _compress_single_doc(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """压缩单个文档"""
        original_content = doc.get('content', '')
        
        # 1. 文本预处理
        cleaned_content = self._preprocess_text(original_content)
        
        # 2. 关键信息提取
        key_info = await self._extract_key_info(cleaned_content)
        
        # 3. 语义压缩
        compressed_content = await self._semantic_compress(key_info)
        
        # 4. 构建压缩文档
        compressed_doc = {
            'content': compressed_content,
            'metadata': doc.get('metadata', {}),
            'original_length': len(original_content),
            'compressed_length': len(compressed_content),
            'compression_ratio': len(compressed_content) / len(original_content) if original_content else 1.0
        }
        
        return compressed_doc
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 移除多余空格和换行
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        
        return text.strip()
    
    async def _extract_key_info(self, text: str) -> str:
        """提取关键信息"""
        # 使用BERT提取关键句子
        sentences = self._split_sentences(text)
        
        if len(sentences) <= 3:
            return text
        
        # 计算句子重要性
        sentence_scores = []
        for sentence in sentences:
            score = await self._calculate_sentence_importance(sentence, text)
            sentence_scores.append((sentence, score))
        
        # 选择最重要的句子
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        num_key_sentences = max(1, int(len(sentences) * self.compression_ratio))
        key_sentences = [s[0] for s in sentence_scores[:num_key_sentences]]
        
        return ' '.join(key_sentences)
    
    async def _semantic_compress(self, text: str) -> str:
        """语义压缩"""
        # 使用同义词替换减少词汇量
        compressed_text = self._replace_synonyms(text)
        
        # 简化句式结构
        compressed_text = self._simplify_syntax(compressed_text)
        
        return compressed_text
    
    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        sentences = re.split(r'[。！？]', text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _calculate_sentence_importance(self, sentence: str, full_text: str) -> float:
        """计算句子重要性"""
        # 使用BERT计算句子与全文的相关性
        inputs = self.tokenizer(
            sentence, 
            full_text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # 使用CLS token的表示
            cls_representation = outputs.last_hidden_state[:, 0, :]
            importance = torch.norm(cls_representation, dim=1).item()
        
        return importance
    
    def _replace_synonyms(self, text: str) -> str:
        """同义词替换"""
        # 游戏术语同义词映射
        synonym_map = {
            '技能': '能力',
            '装备': '道具',
            '副本': '关卡',
            '任务': '工作',
            '玩家': '用户',
            '角色': '人物'
        }
        
        for old, new in synonym_map.items():
            text = text.replace(old, new)
        
        return text
    
    def _simplify_syntax(self, text: str) -> str:
        """简化句式结构"""
        # 移除冗余的修饰词
        redundant_words = ['非常', '特别', '极其', '十分', '相当']
        for word in redundant_words:
            text = text.replace(word, '')
        
        return text
