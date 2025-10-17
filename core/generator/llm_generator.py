# 大语言模型生成器 - 模拟模式
from typing import List, Dict, Any, Optional
import logging
from core.generator.domain_adapter import DomainAdapter
from core.generator.response_formatter import ResponseFormatter
from config.settings import settings

logger = logging.getLogger(__name__)


class LLMGenerator:
    """大语言模型生成器 - 模拟模式（用于开发测试）"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.domain_adapter = DomainAdapter(game_id)
        self.response_formatter = ResponseFormatter(game_id)
        
        # 模拟模式
        self.ai_provider = "mock"
        self.model_name = "mock-llm-v1"
        self.temperature = 0.7
        self.max_tokens = 2000
        
        logger.info(f"[模拟模式] 使用Mock LLM生成器: {game_id}")

    async def generate(
        self,
        question: str,
        context_docs: List[Dict[str, Any]],
        user_context: Optional[Dict] = None,
    ) -> str:
        """
        生成答案 - 模拟模式
        
        Args:
            question: 用户问题
            context_docs: 检索到的上下文文档
            user_context: 用户上下文信息
            
        Returns:
            生成的答案
        """
        # 1. 适配领域知识
        adapted_context = await self.domain_adapter.adapt(context_docs, user_context)

        # 2. 构建提示词
        prompt = self._build_prompt(question, adapted_context, user_context)

        # 3. 调用模拟LLM生成答案
        response = await self._call_llm(prompt, question, context_docs)

        # 4. 格式化响应
        formatted_response = await self.response_formatter.format(response, user_context)

        return formatted_response

    def _build_prompt(self, question: str, context: str, user_context: Optional[Dict]) -> str:
        """构建提示词"""
        user_type = (user_context or {}).get("user_type", "normal")
        accessibility_note = "为老年用户使用更简单表述，步骤化回答。" if user_type == "elderly" else ""

        prompt = f"""
你是一个专业的游戏问答助手，专门回答关于{self.game_id}游戏的问题。

上下文信息：
{context}

用户问题：{question}

请基于上下文信息回答用户的问题，要求：
1. 答案准确、详细
2. 语言简洁明了
3. 如果上下文信息不足，请说明
4. 提供具体的操作步骤或建议
{accessibility_note}

答案：
"""
        return prompt

    async def _call_llm(self, prompt: str, question: str, context_docs: List[Dict]) -> str:
        """调用模拟LLM - 基于问题关键词生成答案"""
        try:
            logger.info(f"[模拟模式] 生成问题答案: {question[:50]}")
            
            # 从上下文文档中提取信息
            if context_docs:
                # 使用检索到的文档内容作为答案基础
                answer_parts = []
                answer_parts.append(f"根据相关资料，关于'{question}'，这里是答案：\n")
                
                for i, doc in enumerate(context_docs[:3], 1):
                    content = doc.get('content', '')
                    if content:
                        answer_parts.append(f"{i}. {content}")
                
                answer_parts.append("\n希望这些信息能帮到你！")
                return "\n".join(answer_parts)
            else:
                # 没有上下文时的通用回答
                return self._generate_generic_answer(question)
            
        except Exception as e:
            logger.error(f"[模拟模式] 生成失败: {str(e)}")
            return f"抱歉，暂时无法回答您的问题。这是模拟模式的回答。"

    def _generate_generic_answer(self, question: str) -> str:
        """生成通用答案"""
        keywords = {
            '学习': '学习技能通常需要访问职业训练师，他们通常位于主城或营地。',
            '技能': '技能可以通过职业训练师学习，需要达到相应等级并支付金币。',
            '装备': '装备可以通过完成任务、击败怪物或在拍卖行购买获得。',
            '任务': '任务可以从NPC处接取，完成后可获得经验值和奖励。',
            '副本': '副本需要组队进入，建议提前了解机制和攻略。',
            '组队': '可以通过组队查找器或好友邀请组队。',
            '升级': '通过完成任务、击杀怪物和参与活动可以获得经验值升级。',
            '金币': '金币可以通过出售物品、完成任务或拍卖行交易获得。',
        }
        
        for keyword, answer in keywords.items():
            if keyword in question:
                return f"关于{keyword}相关的问题：\n{answer}\n\n这是基于常见游戏机制的一般性回答。"
        
        return f"""
        关于您的问题：{question}
        
        这是一个模拟回答。在实际使用中，系统会：
        1. 检索相关的游戏知识
        2. 使用大语言模型生成详细答案
        3. 根据您的需求格式化回答
        
        要获得真实答案，需要配置正式的API Key。
        """
