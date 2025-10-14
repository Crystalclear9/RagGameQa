# 文本工具
import re
import jieba
from typing import List, Dict, Any

class TextUtils:
    """文本处理工具"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        return text.strip()
    
    @staticmethod
    def tokenize_chinese(text: str) -> List[str]:
        """中文分词"""
        return list(jieba.cut(text))
    
    @staticmethod
    def extract_keywords(text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        words = TextUtils.tokenize_chinese(text)
        # 简单的关键词提取（实际应该使用TF-IDF等算法）
        word_freq = {}
        for word in words:
            if len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_k]]
