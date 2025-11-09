"""
LLM API 客户端
"""

import json
from typing import Any, Dict, Iterator, List, Optional

from aicode.llm.exceptions import APIConnectionError, APIError, APITimeoutError
from aicode.llm.token_manager import TokenManager
from aicode.models.schema import ModelSchema
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """LLM API 客户端（OpenAI兼容）"""

    def __init__(
        self,
        model: ModelSchema,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        """
        初始化LLM客户端

        Args:
            model: 模型Schema
            api_key: API密钥（优先级高于model中的配置）
            api_url: API地址（优先级高于model中的配置）
        """
        self.model = model
        self.api_key = api_key or model.api_key
        self.api_url = api_url or model.api_url

        if not self.api_key:
            raise APIError("API key is required")
        if not self.api_url:
            raise APIError("API URL is required")

        self.token_manager = TokenManager(model_name=model.name)
        logger.info(f"LLMClient initialized for model: {model.name}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        发送对话请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            stream: 是否流式返回
            temperature: 温度参数
            max_tokens: 最大输出token数

        Returns:
            str: LLM响应内容

        Raises:
            APIError: API调用失败
            TokenLimitExceededError: Token超限
        """
        # 计算输入token
        input_text = "\n".join([m["content"] for m in messages])
        input_tokens = self.token_manager.count_tokens(input_text)

        # 检查限制
        if self.model.max_input_tokens is not None:
            limit = int(self.model.max_input_tokens * 0.9)
            if input_tokens > limit:
                logger.warning(
                    f"Input tokens {input_tokens} exceeds limit {limit}, truncating..."
                )
                # 简单截断最后一条消息
                last_msg = messages[-1]
                truncated = self.token_manager.truncate_text(
                    last_msg["content"], limit - input_tokens + len(last_msg["content"])
                )
                messages[-1]["content"] = truncated

        # 构建请求
        payload = {
            "model": self.model.name,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens
        elif self.model.max_output_tokens:
            payload["max_tokens"] = self.model.max_output_tokens

        logger.debug(
            f"Sending chat request: {len(messages)} messages, {input_tokens} tokens"
        )

        try:
            # 这里使用简单的实现，实际应该用 httpx 或 openai SDK
            response_text = self._make_request(payload)
            logger.info(f"Received response: {len(response_text)} chars")
            return response_text

        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise APIError(f"Failed to call LLM API: {e}")

    def _make_request(self, payload: Dict[str, Any]) -> str:
        """
        发送HTTP请求（简化版）

        实际实现应该使用 httpx 或 openai SDK

        Args:
            payload: 请求payload

        Returns:
            str: 响应内容
        """
        # TODO: 实际实现需要使用 httpx 发送 POST 请求
        # 这里返回模拟响应，用于测试
        logger.debug("Making HTTP request to LLM API")

        # 模拟响应（实际应该调用真实API）
        return "This is a mock response. Implement with httpx or openai SDK."

    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        计算消息列表的token数

        Args:
            messages: 消息列表

        Returns:
            int: token数量
        """
        text = "\n".join([m["content"] for m in messages])
        return self.token_manager.count_tokens(text)

    def estimate_cost(
        self, messages: List[Dict[str, str]], output_tokens: Optional[int] = None
    ) -> Optional[float]:
        """
        估算对话成本

        Args:
            messages: 消息列表
            output_tokens: 预估输出token数

        Returns:
            float: 成本（美元），如果模型无价格信息则返回None
        """
        text = "\n".join([m["content"] for m in messages])
        return self.token_manager.estimate_cost(text, self.model, output_tokens)

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict: 模型信息
        """
        return {
            "name": self.model.name,
            "provider": self.model.provider,
            "max_input_tokens": self.model.max_input_tokens,
            "max_output_tokens": self.model.max_output_tokens,
            "context_limit": self.model.get_context_limit(),
            "code_score": self.model.code_score,
            "reasoning_score": self.model.reasoning_score,
        }
