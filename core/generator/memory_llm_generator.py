import logging
from typing import Any, Dict, List

from config.settings import settings
from utils.security import redact_sensitive_text

logger = logging.getLogger(__name__)


class MemoryLLMGenerator:
    """内存模式下的轻量生成器，优先复用实时 Provider。"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.live_generator = None
        if settings.AI_PROVIDER.lower() in {"gemini", "claude"} and settings.has_live_llm_config():
            from core.generator.llm_generator import LLMGenerator

            self.live_generator = LLMGenerator(game_id)
        logger.info("MemoryLLMGenerator initialized for %s", game_id)

    async def generate(
        self,
        question: str,
        context_docs: List[Dict[str, Any]],
        user_context: Dict[str, Any] | None = None,
    ) -> str:
        try:
            if self.live_generator is not None:
                return await self.live_generator.generate(question, context_docs, user_context)

            if not context_docs:
                return f"抱歉，我没有找到关于“{question}”的相关信息。请尝试换一种问法。"

            best_doc = context_docs[0]
            content = best_doc.get("content", "")
            title = best_doc.get("title", "") or "检索结果"

            if content:
                answer = f"根据 {title} 的信息：\n\n{content}\n\n"
                if len(context_docs) > 1:
                    answer += "\n其他相关信息：\n"
                    for index, doc in enumerate(context_docs[1:3], 1):
                        doc_title = doc.get("title", "补充资料")
                        doc_content = doc.get("content", "")[:100]
                        answer += f"{index}. {doc_title}: {doc_content}...\n"
                return answer

            return f"我找到了关于“{question}”的一些资料，但内容还不够完整，建议你再换一个更具体的问题。"
        except Exception as exc:
            logger.error("Memory answer generation failed: %s", redact_sensitive_text(exc), exc_info=True)
            return "抱歉，处理你的问题时出现了异常，请稍后再试。"
