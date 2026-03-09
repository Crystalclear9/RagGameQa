# 内存模式LLM生成器
import logging
from typing import List, Dict, Any

from config.settings import settings

logger = logging.getLogger(__name__)

class MemoryLLMGenerator:
    """内存模式LLM生成器，基于检索文档生成答案"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.live_generator = None
        if settings.AI_PROVIDER.lower() == "gemini" and settings.GEMINI_API_KEY:
            from core.generator.llm_generator import LLMGenerator

            self.live_generator = LLMGenerator(game_id)
        logger.info(f"内存模式LLM生成器初始化: {game_id}")
    
    async def generate(self, question: str, context_docs: List[Dict[str, Any]], user_context: Dict[str, Any] = None) -> str:
        """基于检索文档生成答案"""
        try:
            if self.live_generator is not None:
                return await self.live_generator.generate(question, context_docs, user_context)

            if not context_docs:
                return f"抱歉，我没有找到关于'{question}'的相关信息。请尝试其他问题。"
            
            # 获取最相关的文档
            best_doc = context_docs[0]
            content = best_doc.get('content', '')
            title = best_doc.get('title', '')
            
            # 简单的答案生成逻辑
            if content:
                # 基于文档内容生成答案
                answer = f"根据{title}的信息：\n\n{content}\n\n"
                
                # 添加更多相关文档的信息
                if len(context_docs) > 1:
                    answer += "\n其他相关信息：\n"
                    for i, doc in enumerate(context_docs[1:3], 1):  # 最多显示2个额外文档
                        answer += f"{i}. {doc.get('title', '')}: {doc.get('content', '')[:100]}...\n"
                
                return answer
            else:
                return f"我找到了关于'{question}'的一些信息，但内容不够详细。建议您查看游戏官方文档或社区攻略。"
                
        except Exception as e:
            logger.error(f"生成答案失败: {e}")
            return f"抱歉，处理您的问题时出现了错误。请稍后重试。"
