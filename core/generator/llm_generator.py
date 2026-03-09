from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

from config.settings import settings
from core.generator.domain_adapter import DomainAdapter
from core.generator.response_formatter import ResponseFormatter
from utils.security import redact_sensitive_text

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
            logger.info("Using Gemini model %s", self.model_name)
        elif self.ai_provider == "claude" and settings.CLAUDE_API_KEY:
            self.model_name = settings.CLAUDE_MODEL
            self.temperature = settings.CLAUDE_TEMPERATURE
            self.max_tokens = settings.CLAUDE_MAX_TOKENS
            logger.info("Using Claude model %s", self.model_name)
        else:
            if self.ai_provider in {"gemini", "claude"}:
                logger.warning("%s is selected but API key is missing, fallback to mock mode", self.ai_provider)
            self.ai_provider = "mock"
            logger.info("Using mock generator for %s", game_id)

    async def generate(
        self,
        question: str,
        context_docs: List[Dict[str, Any]],
        user_context: Optional[Dict] = None,
    ) -> str:
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
        accessibility_note = "如果用户是老年人，请尽量用更简单、分步骤的中文回答。" if user_type == "elderly" else ""

        system_prompt = (
            "你是一个专业的游戏问答助手。"
            "请优先依据检索到的知识上下文回答，不能编造不存在的信息。"
            "如果上下文不足，请明确说明信息有限，并给出保守建议。"
        )

        user_prompt = f"""
游戏ID：{self.game_id}

知识上下文：
{context or "当前没有检索到可靠上下文。"}

用户问题：{question}

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
        if self.ai_provider == "claude":
            return await self._call_claude(system_prompt, user_prompt)
        return self._generate_mock_answer(question, context_docs)

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        endpoint = (
            f"{settings.GEMINI_API_BASE.rstrip('/')}/models/"
            f"{self.model_name}:generateContent"
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
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
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
            return self._provider_http_error_message("Gemini", exc)
        except requests.RequestException as exc:
            logger.warning("Gemini request failed: %s", redact_sensitive_text(exc))
            return "Gemini 连接失败，请检查网络、API Base 或代理设置。"
        except Exception as exc:
            logger.error("Gemini request error: %s", redact_sensitive_text(exc), exc_info=True)
            return "Gemini 请求异常，请稍后重试。"

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
            return f"Gemini 未返回可用内容，原因是 {block_reason}。"
        return "Gemini 未返回可用内容，请稍后重试。"

    async def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        endpoint = f"{settings.CLAUDE_API_BASE.rstrip('/')}/v1/messages"
        payload = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": settings.CLAUDE_API_KEY,
            "anthropic-version": settings.CLAUDE_API_VERSION,
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
            return self._provider_http_error_message("Claude", exc)
        except requests.RequestException as exc:
            logger.warning("Claude request failed: %s", redact_sensitive_text(exc))
            return "Claude 连接失败，请检查网络、API Base 或代理设置。"
        except Exception as exc:
            logger.error("Claude request error: %s", redact_sensitive_text(exc), exc_info=True)
            return "Claude 请求异常，请稍后重试。"

        content = data.get("content") or []
        text_parts = [item.get("text", "") for item in content if item.get("type") == "text" and item.get("text")]
        if text_parts:
            return "\n".join(text_parts).strip()
        return "Claude 未返回可用内容，请稍后重试。"

    def _provider_http_error_message(self, provider_name: str, exc: requests.HTTPError) -> str:
        status = exc.response.status_code if exc.response is not None else None
        body = ""
        try:
            body = exc.response.text[:300] if exc.response is not None else str(exc)
        except Exception:
            body = str(exc)
        logger.warning(
            "%s API request failed: status=%s detail=%s",
            provider_name,
            status,
            redact_sensitive_text(body),
        )
        if status in {401, 403}:
            return f"{provider_name} 鉴权失败，请检查 API Key 与权限。"
        if status == 404:
            return f"{provider_name} 模型不存在，请检查模型名称。"
        if status == 429:
            return f"{provider_name} 调用过于频繁，请稍后重试。"
        if status and status >= 500:
            return f"{provider_name} 服务暂时不可用，请稍后重试。"
        return f"{provider_name} 调用失败，请检查配置后重试。"

    def _generate_mock_answer(self, question: str, context_docs: List[Dict[str, Any]]) -> str:
        try:
            logger.info("Generating mock answer: %s", question[:50])
            if context_docs:
                answer_parts = [f"根据检索到的资料，关于“{question}”，可以先参考这些信息：\n"]
                for index, doc in enumerate(context_docs[:3], 1):
                    content = doc.get("content", "")
                    if content:
                        answer_parts.append(f"{index}. {content}")
                answer_parts.append("\n如果你愿意，我还可以继续把这些内容整理成更易懂的步骤说明。")
                return "\n".join(answer_parts)
            return self._generate_generic_answer(question)
        except Exception as exc:
            logger.error("Mock answer generation failed: %s", redact_sensitive_text(exc), exc_info=True)
            return "抱歉，暂时无法回答你的问题。当前系统已自动回退到本地演示模式。"

    def _generate_generic_answer(self, question: str) -> str:
        keywords = {
            "学习": "学习技能通常需要访问职业训练师，他们一般位于主城或营地。",
            "技能": "技能通常可以通过职业训练师学习，需要达到相应等级并支付一定金币。",
            "装备": "装备可以通过完成任务、击败怪物或在拍卖行购买获得。",
            "任务": "任务一般由 NPC 发布，完成后可获得经验值和奖励。",
            "副本": "进入副本前建议先了解机制、准备补给，并和队友确认分工。",
            "组队": "你可以通过组队查找器、好友邀请或大厅匹配来完成组队。",
            "升级": "完成任务、击败怪物和参与活动都是常见的升级方式。",
            "金币": "金币通常可以通过出售物品、完成任务或交易获得。",
        }
        for keyword, answer in keywords.items():
            if keyword in question:
                return (
                    f"关于“{keyword}”相关的问题：\n{answer}\n\n"
                    "当前回答来自本地演示模式，适合做功能展示和接口联调。"
                )

        return (
            f"关于你的问题“{question}”，当前系统还没有检索到足够明确的信息。"
            "如果你已经配置了 Gemini 或 Claude API，我可以结合检索结果给出更自然、更完整的回答。"
        )
