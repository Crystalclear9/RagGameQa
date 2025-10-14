# 领域适配器
from typing import List, Dict, Any, Optional

from config.game_configs import load_game_config


class DomainAdapter:
    """领域适配器，将通用知识适配到特定游戏领域"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.game_config = self._load_game_config()

    async def adapt(
        self,
        context_docs: List[Dict[str, Any]],
        user_context: Optional[Dict] = None,
    ) -> str:
        """
        适配领域知识

        Args:
            context_docs: 原始上下文文档
            user_context: 用户上下文

        Returns:
            适配后的上下文
        """
        # 1. 过滤相关文档（基于用户偏好/关键词/类别）
        relevant_docs = self._filter_relevant_docs(context_docs, user_context)

        # 2. 转换文档格式（带来源、类别与分数）
        formatted_docs = self._format_documents(relevant_docs)

        # 3. 添加游戏特定信息（名称、版本、平台）
        enhanced_context = self._enhance_with_game_info(formatted_docs)

        return enhanced_context

    def _filter_relevant_docs(
        self, docs: List[Dict], user_context: Optional[Dict]
    ) -> List[Dict]:
        """过滤相关文档"""
        if not user_context:
            return docs

        preferred_categories = set(user_context.get("preferred_categories", []))
        keywords = set(user_context.get("keywords", []))

        filtered_docs: List[Dict] = []
        for doc in docs:
            if self._is_relevant(doc, user_context, preferred_categories, keywords):
                filtered_docs.append(doc)

        return filtered_docs

    def _format_documents(self, docs: List[Dict]) -> str:
        """格式化文档"""
        formatted_text = ""
        for i, doc in enumerate(docs, 1):
            source = doc.get("metadata", {}).get("source", "未知") if doc.get("metadata") else "未知"
            category = doc.get("category", "未分类")
            score = doc.get("score") or doc.get("similarity")
            score_text = f" 分数:{score:.3f}" if isinstance(score, (int, float)) else ""

            formatted_text += f"[文档{i}{score_text}] 类别:{category} 来源:{source}\n"
            formatted_text += f"内容：{doc.get('content', '')}\n\n"

        return formatted_text

    def _enhance_with_game_info(self, context: str) -> str:
        """添加游戏特定信息"""
        name = self.game_config.get("game_name", self.game_id)
        version = self.game_config.get("version", "未知")
        platforms = ", ".join(self.game_config.get("platforms", []))
        languages = ", ".join(self.game_config.get("languages", []))

        header = (
            f"游戏：{name}\n版本：{version}\n平台：{platforms}\n语言：{languages}\n\n"
        )
        return header + context

    def _is_relevant(
        self,
        doc: Dict,
        user_context: Dict,
        preferred_categories: Optional[set] = None,
        keywords: Optional[set] = None,
    ) -> bool:
        """判断文档是否相关"""
        # 类别偏好
        if preferred_categories:
            doc_cat = doc.get("category")
            if doc_cat and doc_cat not in preferred_categories:
                return False

        # 关键词匹配（标题/内容）
        if keywords:
            text = (doc.get("title") or "") + " " + (doc.get("content") or "")
            if text:
                hit = any(k in text for k in keywords)
                if not hit:
                    return False

        # 用户类型简单适配（示例：elderly优先更简洁的指南类文档）
        user_type = user_context.get("user_type")
        if user_type == "elderly":
            if doc.get("category") in {"操作步骤", "新手指南", "任务流程"}:
                return True

        return True

    def _load_game_config(self) -> Dict:
        """加载游戏配置"""
        try:
            return load_game_config(self.game_id)
        except Exception:
            return {}
