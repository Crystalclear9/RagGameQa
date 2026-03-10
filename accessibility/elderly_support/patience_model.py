# 语义耐心值模型
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Any, Dict, List

import jieba

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore[assignment]

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - optional dependency
    TfidfVectorizer = None  # type: ignore[assignment]
    cosine_similarity = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class PatienceModel:
    """检测重复提问并在需要时触发更细的引导策略。"""

    _question_history = defaultdict(lambda: deque(maxlen=10))
    _user_patience = defaultdict(float)
    _user_last_question_time = defaultdict(float)

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.similarity_threshold = 0.85
        self.max_patience = 3
        self.patience_decay_time = 3600
        self.sentence_model = self._load_sentence_model()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2)) if TfidfVectorizer else None
        self.question_types = {
            "operation": ["怎么", "如何", "操作", "点击", "选择", "进入", "打开", "关闭"],
            "equipment": ["装备", "技能", "武器", "道具", "获得", "升级", "强化"],
            "task": ["任务", "完成", "目标", "要求", "挑战", "关卡"],
            "social": ["组队", "好友", "聊天", "公会", "邀请", "加入"],
            "bug": ["错误", "问题", "卡住", "不动", "闪退", "崩溃"],
            "general": ["什么", "哪里", "为什么", "怎么办"],
        }

    def _load_sentence_model(self):
        if SentenceTransformer is None:
            return None
        try:
            return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        except Exception as exc:
            logger.warning("Patience model embedding unavailable: %s", exc)
            return None

    def _user_key(self, user_id: str) -> str:
        return f"{self.game_id}:{user_id}"

    async def check_patience(self, question: str, user_id: str) -> Dict[str, Any]:
        try:
            current_time = time.time()
            key = self._user_key(user_id)
            processed_question = await self._preprocess_question(question)
            user_history = list(self._question_history[key])

            similarities = []
            for hist_question in user_history:
                similarities.append(await self._calculate_semantic_similarity(processed_question, hist_question))

            max_similarity = max(similarities) if similarities else 0.0
            is_repetitive = max_similarity > self.similarity_threshold
            question_type = await self._classify_question_type(question)
            patience_level = await self._update_patience(key, is_repetitive, current_time)
            needs_guidance = patience_level >= self.max_patience
            guidance_suggestion = await self._generate_guidance_suggestion(question_type, patience_level, is_repetitive)

            last_time = self._user_last_question_time.get(key, 0.0)
            self._record_question(key, processed_question, current_time)

            return {
                "patience_level": patience_level,
                "is_repetitive": is_repetitive,
                "similarity_score": round(max_similarity, 3),
                "needs_guidance": needs_guidance,
                "guidance_type": guidance_suggestion["type"],
                "guidance_content": guidance_suggestion["content"],
                "question_type": question_type,
                "time_since_last": current_time - last_time if last_time else None,
                "suggestions": await self._generate_user_suggestions(question_type, patience_level),
            }
        except Exception as exc:
            logger.warning("Patience check failed: %s", exc)
            return {
                "patience_level": 1,
                "is_repetitive": False,
                "similarity_score": 0.0,
                "needs_guidance": False,
                "guidance_type": None,
                "guidance_content": None,
                "question_type": "general",
                "error": str(exc),
            }

    async def _preprocess_question(self, question: str) -> str:
        question = question.strip()
        words = list(jieba.cut(question))
        stop_words = {"的", "了", "在", "是", "我", "你", "他", "她", "它", "们", "这", "那", "什么", "怎么", "如何"}
        filtered_words = [word for word in words if len(word) > 1 and word not in stop_words and word.isalnum()]
        return " ".join(filtered_words) or question

    async def _calculate_semantic_similarity(self, question1: str, question2: str) -> float:
        try:
            if self.sentence_model is not None and cosine_similarity is not None:
                embeddings = self.sentence_model.encode([question1, question2])
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(similarity)
            if self.tfidf_vectorizer is not None and cosine_similarity is not None:
                return await self._calculate_tfidf_similarity(question1, question2)
            return await self._calculate_word_overlap(question1, question2)
        except Exception:
            return await self._calculate_word_overlap(question1, question2)

    async def _calculate_tfidf_similarity(self, question1: str, question2: str) -> float:
        if self.tfidf_vectorizer is None or cosine_similarity is None:
            return await self._calculate_word_overlap(question1, question2)
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([question1, question2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception:
            return await self._calculate_word_overlap(question1, question2)

    async def _calculate_word_overlap(self, question1: str, question2: str) -> float:
        words1 = set(question1.split())
        words2 = set(question2.split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union else 0.0

    async def _classify_question_type(self, question: str) -> str:
        normalized = question.lower()
        type_scores = {
            q_type: sum(1 for keyword in keywords if keyword in normalized)
            for q_type, keywords in self.question_types.items()
        }
        return max(type_scores.items(), key=lambda item: item[1])[0] if type_scores else "general"

    async def _update_patience(self, key: str, is_repetitive: bool, current_time: float) -> int:
        last_time = self._user_last_question_time.get(key, 0.0)
        if last_time and current_time - last_time > self.patience_decay_time:
            self._user_patience[key] = 0.0

        if is_repetitive:
            self._user_patience[key] += 1.0
        else:
            self._user_patience[key] = max(0.0, self._user_patience[key] - 0.5)

        self._user_patience[key] = min(self._user_patience[key], float(self.max_patience))
        return int(self._user_patience[key])

    async def _generate_guidance_suggestion(self, question_type: str, patience_level: int, is_repetitive: bool) -> Dict[str, Any]:
        if patience_level >= self.max_patience:
            return {"type": "step_by_step", "content": await self._get_step_by_step_guidance(question_type), "priority": "high"}
        if patience_level >= 2:
            return {"type": "simplified", "content": await self._get_simplified_guidance(question_type), "priority": "medium"}
        if is_repetitive:
            return {"type": "clarification", "content": await self._get_clarification_guidance(question_type), "priority": "low"}
        return {"type": "normal", "content": "正常回答", "priority": "normal"}

    async def _get_step_by_step_guidance(self, question_type: str) -> str:
        guidance_templates = {
            "operation": "我将为您提供详细的操作步骤，请按照步骤逐一进行：",
            "equipment": "让我为您详细介绍装备相关信息，分步骤说明：",
            "task": "任务完成需要以下步骤，请仔细阅读：",
            "social": "社交功能使用指南，按步骤操作：",
            "bug": "遇到问题不要着急，让我们一步步解决：",
            "general": "让我为您详细解释这个问题：",
        }
        return guidance_templates.get(question_type, "让我为您详细解释：")

    async def _get_simplified_guidance(self, question_type: str) -> str:
        return "让我用更简单的方式为您解释："

    async def _get_clarification_guidance(self, question_type: str) -> str:
        return "您可以告诉我卡在哪一步，我会拆成更细的步骤继续说明。"

    async def _generate_user_suggestions(self, question_type: str, patience_level: int) -> List[str]:
        suggestions: List[str] = []
        if patience_level >= 2:
            suggestions.extend(["建议先熟悉基本操作", "可以请家人协助操作", "建议分步骤学习游戏功能"])
        if question_type == "operation":
            suggestions.extend(["可以先练习基本点击操作", "建议观看游戏教程视频"])
        elif question_type == "equipment":
            suggestions.extend(["建议先了解装备属性", "可以咨询有经验的玩家"])
        elif question_type == "social":
            suggestions.extend(["建议先了解基本社交功能", "可以请家人帮忙设置"])
        return suggestions[:3]

    def _record_question(self, key: str, question: str, timestamp: float):
        self._question_history[key].append(question)
        self._user_last_question_time[key] = timestamp

    async def reset_user_patience(self, user_id: str):
        key = self._user_key(user_id)
        self._user_patience[key] = 0.0
        self._question_history[key].clear()
        self._user_last_question_time[key] = 0.0

    async def get_user_patience_stats(self, user_id: str) -> Dict[str, Any]:
        key = self._user_key(user_id)
        last_time = self._user_last_question_time.get(key, 0.0)
        return {
            "current_patience": self._user_patience[key],
            "max_patience": self.max_patience,
            "question_count": len(self._question_history[key]),
            "last_question_time": last_time,
            "time_since_last": time.time() - last_time if last_time else None,
        }

    async def adjust_patience_threshold(self, new_threshold: float):
        self.similarity_threshold = new_threshold
