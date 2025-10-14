# 大语言模型生成器
from typing import List, Dict, Any, Optional
import openai
from core.generator.domain_adapter import DomainAdapter
from core.generator.response_formatter import ResponseFormatter

class LLMGenerator:
    """大语言模型生成器"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.domain_adapter = DomainAdapter(game_id)
        self.response_formatter = ResponseFormatter(game_id)
        self.client = openai.OpenAI()
    
    async def generate(
        self, 
        question: str, 
        context_docs: List[Dict[str, Any]], 
        user_context: Optional[Dict] = None
    ) -> str:
        """
        生成答案
        
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
        
        # 3. 调用LLM生成答案
        response = await self._call_llm(prompt)
        
        # 4. 格式化响应
        formatted_response = await self.response_formatter.format(response, user_context)
        
        return formatted_response
    
    def _build_prompt(self, question: str, context: str, user_context: Optional[Dict]) -> str:
        """构建提示词"""
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

答案：
"""
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """调用大语言模型"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的游戏问答助手。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"抱歉，生成答案时出现错误：{str(e)}"
