# 语义耐心值模型
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import jieba
import time
from collections import defaultdict, deque
import json

class PatienceModel:
    """语义耐心值模型，检测老年玩家重复提问并触发分步引导"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.similarity_threshold = 0.85
        self.max_patience = 3
        self.patience_decay_time = 3600  # 1小时后耐心值衰减
        self.question_history = defaultdict(lambda: deque(maxlen=10))  # 每个用户最多保存10个问题
        self.user_patience = defaultdict(int)  # 用户耐心值
        self.user_last_question_time = defaultdict(float)  # 用户最后提问时间
        
        # 初始化语义模型
        try:
            self.sentence_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        except:
            self.sentence_model = None
        
        # TF-IDF向量化器
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # 中文停用词需要单独处理
            ngram_range=(1, 2)
        )
        
        # 问题类型分类器
        self.question_types = {
            "operation": ["怎么", "如何", "操作", "点击", "选择", "进入", "打开", "关闭"],
            "equipment": ["装备", "技能", "武器", "道具", "获得", "升级", "强化"],
            "task": ["任务", "完成", "目标", "要求", "挑战", "关卡"],
            "social": ["组队", "好友", "聊天", "公会", "邀请", "加入"],
            "bug": ["错误", "问题", "卡住", "不动", "闪退", "崩溃"],
            "general": ["什么", "哪里", "为什么", "怎么办"]
        }
    
    async def check_patience(self, question: str, user_id: str) -> Dict[str, Any]:
        """
        检查用户耐心值
        
        Args:
            question: 当前问题
            user_id: 用户ID
            
        Returns:
            耐心值检查结果
        """
        try:
            current_time = time.time()
            
            # 1. 预处理问题
            processed_question = await self._preprocess_question(question)
            
            # 2. 获取用户历史问题
            user_history = self._get_user_history(user_id)
            
            # 3. 计算语义相似度
            similarities = []
            for hist_question in user_history:
                similarity = await self._calculate_semantic_similarity(processed_question, hist_question)
                similarities.append(similarity)
            
            # 4. 判断是否重复
            max_similarity = max(similarities) if similarities else 0
            is_repetitive = max_similarity > self.similarity_threshold
            
            # 5. 分析问题类型
            question_type = await self._classify_question_type(processed_question)
            
            # 6. 更新耐心值
            patience_level = await self._update_patience(user_id, is_repetitive, current_time)
            
            # 7. 判断是否需要触发分步引导
            needs_guidance = patience_level >= self.max_patience
            
            # 8. 生成引导建议
            guidance_suggestion = await self._generate_guidance_suggestion(
                question_type, patience_level, is_repetitive
            )
            
            # 9. 记录当前问题
            self._record_question(user_id, processed_question, current_time)
            
            return {
                "patience_level": patience_level,
                "is_repetitive": is_repetitive,
                "similarity_score": max_similarity,
                "needs_guidance": needs_guidance,
                "guidance_type": guidance_suggestion["type"],
                "guidance_content": guidance_suggestion["content"],
                "question_type": question_type,
                "time_since_last": current_time - self.user_last_question_time.get(user_id, 0),
                "suggestions": await self._generate_user_suggestions(question_type, patience_level)
            }
            
        except Exception as e:
            return {
                "patience_level": 1,
                "is_repetitive": False,
                "similarity_score": 0.0,
                "needs_guidance": False,
                "guidance_type": None,
                "guidance_content": None,
                "question_type": "general",
                "error": str(e)
            }
    
    async def _preprocess_question(self, question: str) -> str:
        """预处理问题文本"""
        # 1. 基础清理
        question = question.strip()
        
        # 2. 中文分词
        words = list(jieba.cut(question))
        
        # 3. 过滤停用词和标点
        filtered_words = []
        stop_words = {"的", "了", "在", "是", "我", "你", "他", "她", "它", "们", "这", "那", "什么", "怎么", "如何"}
        
        for word in words:
            if len(word) > 1 and word not in stop_words and word.isalnum():
                filtered_words.append(word)
        
        return " ".join(filtered_words)
    
    def _get_user_history(self, user_id: str) -> List[str]:
        """获取用户历史问题"""
        return list(self.question_history[user_id])
    
    async def _calculate_semantic_similarity(self, question1: str, question2: str) -> float:
        """计算语义相似度"""
        try:
            if self.sentence_model:
                # 使用SentenceTransformer计算语义相似度
                embeddings = self.sentence_model.encode([question1, question2])
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(similarity)
            else:
                # 回退到TF-IDF相似度
                return await self._calculate_tfidf_similarity(question1, question2)
        except Exception:
            # 最终回退到简单的词汇重叠
            return await self._calculate_word_overlap(question1, question2)
    
    async def _calculate_tfidf_similarity(self, question1: str, question2: str) -> float:
        """使用TF-IDF计算相似度"""
        try:
            # 获取所有历史问题用于训练TF-IDF
            all_questions = list(self.question_history.values())
            flat_questions = [q for user_questions in all_questions for q in user_questions]
            flat_questions.extend([question1, question2])
            
            if len(flat_questions) < 2:
                return 0.0
            
            # 训练TF-IDF向量化器
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(flat_questions)
            
            # 计算最后两个向量的相似度
            similarity = cosine_similarity(tfidf_matrix[-2:], tfidf_matrix[-1:])[0][0]
            return float(similarity)
        except Exception:
            return await self._calculate_word_overlap(question1, question2)
    
    async def _calculate_word_overlap(self, question1: str, question2: str) -> float:
        """计算词汇重叠相似度"""
        words1 = set(question1.split())
        words2 = set(question2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _classify_question_type(self, question: str) -> str:
        """分类问题类型"""
        question_lower = question.lower()
        
        type_scores = {}
        for q_type, keywords in self.question_types.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            type_scores[q_type] = score
        
        # 返回得分最高的类型
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        return "general"
    
    async def _update_patience(self, user_id: str, is_repetitive: bool, current_time: float) -> int:
        """更新耐心值"""
        last_time = self.user_last_question_time.get(user_id, 0)
        time_diff = current_time - last_time
        
        # 如果超过衰减时间，重置耐心值
        if time_diff > self.patience_decay_time:
            self.user_patience[user_id] = 0
        
        # 更新耐心值
        if is_repetitive:
            self.user_patience[user_id] += 1
        else:
            # 非重复问题，耐心值轻微增加
            self.user_patience[user_id] = max(0, self.user_patience[user_id] - 0.5)
        
        # 限制耐心值范围
        self.user_patience[user_id] = min(self.user_patience[user_id], self.max_patience)
        
        return int(self.user_patience[user_id])
    
    async def _generate_guidance_suggestion(
        self, 
        question_type: str, 
        patience_level: int, 
        is_repetitive: bool
    ) -> Dict[str, Any]:
        """生成引导建议"""
        if patience_level >= self.max_patience:
            return {
                "type": "step_by_step",
                "content": await self._get_step_by_step_guidance(question_type),
                "priority": "high"
            }
        elif patience_level >= 2:
            return {
                "type": "simplified",
                "content": await self._get_simplified_guidance(question_type),
                "priority": "medium"
            }
        elif is_repetitive:
            return {
                "type": "clarification",
                "content": await self._get_clarification_guidance(question_type),
                "priority": "low"
            }
        else:
            return {
                "type": "normal",
                "content": "正常回答",
                "priority": "normal"
            }
    
    async def _get_step_by_step_guidance(self, question_type: str) -> str:
        """获取分步引导内容"""
        guidance_templates = {
            "operation": "我将为您提供详细的操作步骤，请按照步骤逐一进行：",
            "equipment": "让我为您详细介绍装备相关信息，分步骤说明：",
            "task": "任务完成需要以下步骤，请仔细阅读：",
            "social": "社交功能使用指南，按步骤操作：",
            "bug": "遇到问题不要着急，让我们一步步解决：",
            "general": "让我为您详细解释这个问题："
        }
        return guidance_templates.get(question_type, "让我为您详细解释：")
    
    async def _get_simplified_guidance(self, question_type: str) -> str:
        """获取简化引导内容"""
        return "让我用简单的方式为您解释："
    
    async def _get_clarification_guidance(self, question_type: str) -> str:
        """获取澄清引导内容"""
        return "您是想了解哪个具体方面呢？我可以为您详细说明。"
    
    async def _generate_user_suggestions(self, question_type: str, patience_level: int) -> List[str]:
        """生成用户建议"""
        suggestions = []
        
        if patience_level >= 2:
            suggestions.extend([
                "建议您先熟悉基本操作",
                "可以请家人协助操作",
                "建议分步骤学习游戏功能"
            ])
        
        if question_type == "operation":
            suggestions.extend([
                "可以先练习基本点击操作",
                "建议观看游戏教程视频"
            ])
        elif question_type == "equipment":
            suggestions.extend([
                "建议先了解装备属性",
                "可以咨询有经验的玩家"
            ])
        elif question_type == "social":
            suggestions.extend([
                "建议先了解基本社交功能",
                "可以请家人帮忙设置"
            ])
        
        return suggestions[:3]  # 最多返回3个建议
    
    def _record_question(self, user_id: str, question: str, timestamp: float):
        """记录用户问题"""
        self.question_history[user_id].append(question)
        self.user_last_question_time[user_id] = timestamp
    
    async def reset_user_patience(self, user_id: str):
        """重置用户耐心值"""
        self.user_patience[user_id] = 0
        self.question_history[user_id].clear()
        self.user_last_question_time[user_id] = 0
    
    async def get_user_patience_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户耐心值统计"""
        return {
            "current_patience": self.user_patience[user_id],
            "max_patience": self.max_patience,
            "question_count": len(self.question_history[user_id]),
            "last_question_time": self.user_last_question_time.get(user_id, 0),
            "time_since_last": time.time() - self.user_last_question_time.get(user_id, 0)
        }
    
    async def adjust_patience_threshold(self, new_threshold: float):
        """调整相似度阈值"""
        self.similarity_threshold = new_threshold
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """导出用户数据"""
        return {
            "user_id": user_id,
            "patience_level": self.user_patience[user_id],
            "question_history": list(self.question_history[user_id]),
            "last_question_time": self.user_last_question_time.get(user_id, 0),
            "export_time": time.time()
        }
    
    async def import_user_data(self, user_data: Dict[str, Any]):
        """导入用户数据"""
        user_id = user_data["user_id"]
        self.user_patience[user_id] = user_data["patience_level"]
        self.question_history[user_id] = deque(user_data["question_history"], maxlen=10)
        self.user_last_question_time[user_id] = user_data["last_question_time"]
