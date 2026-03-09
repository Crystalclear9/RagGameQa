# 大语言模型生成器
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

from config.settings import settings
from core.generator.domain_adapter import DomainAdapter
from core.generator.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)


class LLMGenerator:
    """支持真实 Provider 与回退模式的大语言模型生成器。"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.domain_adapter = DomainAdapter(game_id)
        self.response_formatter = ResponseFormatter(game_id)
        self.ai_provider = (settings.AI_PROVIDER or "mock").lower()
        self.model_name = "mock-llm-v1"
        self.temperature = 0.7
        self.max_tokens = 2000

        if self.ai_provider == "gemini" and settings.GEMINI_API_KEY:
            self.model_name = settings.GEMINI_MODEL
            self.temperature = settings.GEMINI_TEMPERATURE
            self.max_tokens = settings.GEMINI_MAX_TOKENS
            logger.info("启用 Gemini 生成器: %s", self.model_name)
        else:
            if self.ai_provider == "gemini" and not settings.GEMINI_API_KEY:
                logger.warning("AI_PROVIDER=gemini，但 GEMINI_API_KEY 未配置，自动回退到 mock")
            self.ai_provider = "mock"
            logger.info("[回退模式] 使用 Mock LLM 生成器: %s", game_id)

    async def generate(
        self,
        question: str,
        context_docs: List[Dict[str, Any]],
        user_context: Optional[Dict] = None,
    ) -> str:
        """
        生成答案。
        """
        adapted_context = await self.domain_adapter.adapt(context_docs, user_context)
        system_prompt, user_prompt = self._build_prompts(question, adapted_context, user_context)

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            question=question,
            context_docs=context_docs,
        )
        formatted_response = await self.response_formatter.format(response, user_context)
        return formatted_response

    def _build_prompts(
        self,
        question: str,
        context: str,
        user_context: Optional[Dict[str, Any]],
    ) -> Tuple[str, str]:
        user_type = (user_context or {}).get("user_type", "normal")
        accessibility_note = "为老年用户使用更简单表述，尽量分步骤回答。" if user_type == "elderly" else ""

        system_prompt = (
            "你是一个专业的游戏问答助手。"
            "你必须优先依据提供的知识上下文回答，不能编造不存在的信息。"
            "如果上下文不足，请明确说明信息有限，并给出保守建议。"
        )

        user_prompt = f"""
游戏ID：{self.game_id}

知识上下文：
{context or "当前没有检索到可靠上下文。"}

用户问题：
{question}

回答要求：
1. 先直接回答核心问题。
2. 再给出 2-4 条清晰建议或步骤。
3. 只在上下文支持时给出确定性结论。
4. 使用中文输出。
{accessibility_note}
"""
        return system_prompt, user_prompt.strip()

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        question: str,
        context_docs: List[Dict[str, Any]],
    ) -> str:
        if self.ai_provider == "gemini":
            return await self._call_gemini(system_prompt, user_prompt)
        return self._generate_mock_answer(question, context_docs)

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """按 Gemini 官方 generateContent REST 接口发起请求。"""
        endpoint = (
            f"{settings.GEMINI_API_BASE.rstrip('/')}/models/"
            f"{settings.GEMINI_MODEL}:generateContent"
        )
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": settings.GEMINI_TEMPERATURE,
                "maxOutputTokens": settings.GEMINI_MAX_TOKENS,
            },
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY,
        }

        try:
            response = await asyncio.to_thread(
                requests.post,
                endpoint,
                headers=headers,
                json=payload,
                timeout=settings.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except requests.HTTPError as exc:
            detail = ""
            try:
                detail = exc.response.text[:300]
            except Exception:
                detail = str(exc)
            logger.error("Gemini API 调用失败: %s", detail)
            return f"Gemini API 调用失败：{detail}"
        except Exception as exc:
            logger.error("Gemini 请求异常: %s", exc)
            return f"Gemini 请求异常：{exc}"

        candidates = data.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            text_parts = [part.get("text", "") for part in parts if part.get("text")]
            if text_parts:
                return "\n".join(text_parts).strip()

        prompt_feedback = data.get("promptFeedback") or {}
        block_reason = prompt_feedback.get("blockReason")
        if block_reason:
            return f"Gemini 未返回可用内容，原因：{block_reason}"
        return "Gemini 未返回可用内容，请稍后重试。"

    def _generate_mock_answer(self, question: str, context_docs: List[Dict[str, Any]]) -> str:
        """未配置真实 Provider 时的回退答案。"""
        try:
            logger.info("[回退模式] 生成问题答案: %s", question[:50])
            if context_docs:
                answer_parts = [f"根据相关资料，关于“{question}”，可以参考以下信息：\n"]
                for index, doc in enumerate(context_docs[:3], 1):
                    content = doc.get("content", "")
                    if content:
                        answer_parts.append(f"{index}. {content}")
                answer_parts.append("\n如果你需要，我还可以把这些内容整理成更清晰的步骤。")
                return "\n".join(answer_parts)
            return self._generate_generic_answer(question)
        except Exception as exc:
            logger.error("[回退模式] 生成失败: %s", exc)
            return "抱歉，暂时无法回答您的问题。当前是回退模式。"

    def _generate_generic_answer(self, question: str) -> str:
        keywords = {
            "学习": "学习技能通常需要访问职业训练师，他们通常位于主城或营地。",
            "技能": "技能可以通过职业训练师学习，需要达到相应等级并支付金币。",
            "装备": "装备可以通过完成任务、击败怪物或在拍卖行购买获得。",
            "任务": "任务可以从 NPC 处接取，完成后可获得经验值和奖励。",
            "副本": "副本通常需要组队进入，建议先了解机制和角色定位。",
            "组队": "可以通过组队查找器、好友邀请或大厅匹配来完成组队。",
            "升级": "通过完成任务、击杀怪物和参与活动可以获得经验值升级。",
            "金币": "金币可以通过出售物品、完成任务或拍卖行交易获得。",
        }
        for keyword, answer in keywords.items():
            if keyword in question:
                return f"关于“{keyword}”相关的问题：\n{answer}\n\n这是在未接入真实大模型时的本地回退回答。"

        return (
            f"关于你的问题“{question}”，当前系统没有检索到足够明确的信息。"
            "如果你已经配置 Gemini API，我可以结合检索结果给出更自然、更完整的回答。"
        )
