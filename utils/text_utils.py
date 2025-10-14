# 文本工具
import re
import jieba
from typing import List, Dict, Any


class TextUtils:
    """文本处理工具"""

    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        return text.strip()

    @staticmethod
    def tokenize_chinese(text: str) -> List[str]:
        """中文分词"""
        return list(jieba.cut(text))

    @staticmethod
    def extract_keywords(text: str, top_k: int = 10) -> List[str]:
        """提取关键词（基于词频的简单实现）"""
        words = TextUtils.tokenize_chinese(text)
        word_freq: Dict[str, int] = {}
        for word in words:
            if len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_k]]

    @staticmethod
    def jaccard_similarity(a: str, b: str) -> float:
        """计算Jaccard相似度"""
        sa = set(TextUtils.tokenize_chinese(TextUtils.clean_text(a)))
        sb = set(TextUtils.tokenize_chinese(TextUtils.clean_text(b)))
        if not sa or not sb:
            return 0.0
        inter = len(sa & sb)
        union = len(sa | sb)
        return inter / union if union > 0 else 0.0

    @staticmethod
    def cosine_similarity_bow(a: str, b: str) -> float:
        """基于词袋的余弦相似度（简化实现）"""
        tokens_a = TextUtils.tokenize_chinese(TextUtils.clean_text(a))
        tokens_b = TextUtils.tokenize_chinese(TextUtils.clean_text(b))
        vocab = {w for w in tokens_a + tokens_b if len(w) > 1}
        if not vocab:
            return 0.0
        index = {w: i for i, w in enumerate(sorted(vocab))}
        vec_a = [0] * len(index)
        vec_b = [0] * len(index)
        for w in tokens_a:
            if w in index:
                vec_a[index[w]] += 1
        for w in tokens_b:
            if w in index:
                vec_b[index[w]] += 1
        dot = sum(x * y for x, y in zip(vec_a, vec_b))
        norm_a = sum(x * x for x in vec_a) ** 0.5
        norm_b = sum(y * y for y in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
