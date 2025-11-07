"""
LLM API 客户端
"""
from typing import List, Dict, Any, Optional, Iterator
import json
import requests
from aicode.models.schema import ModelSchema
from aicode.llm.token_manager import TokenManager
from aicode.llm.exceptions import APIError, APIConnectionError, APITimeoutError
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """LLM API 客户端（OpenAI兼容）"""

    def __init__(
        self,
        model: ModelSchema,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化LLM客户端

        Args:
            model: 模型Schema
            api_key: API密钥（优先级高于model中的配置，本地服务如Ollama可选）
            api_url: API地址（优先级高于model中的配置）
            timeout: 请求超时时间（秒）
        """
        self.model = model
        self.api_key = api_key or model.api_key
        self.api_url = api_url or model.api_url
        self.timeout = timeout

        # API URL 是必需的
        if not self.api_url:
            raise APIError("API URL is required")

        # 对于本地服务（如 Ollama），API key 不是必需的
        is_local = self.api_url.startswith("http://localhost") or \
                   self.api_url.startswith("http://127.0.0.1")

        if not self.api_key and not is_local:
            raise APIError("API key is required for non-local services")

        self.token_manager = TokenManager(model_name=model.name)
        logger.info(f"LLMClient initialized for model: {model.name}, URL: {self.api_url}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
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
        input_text = '\n'.join([m['content'] for m in messages])
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
                    last_msg['content'],
                    limit - input_tokens + len(last_msg['content'])
                )
                messages[-1]['content'] = truncated

        # 构建请求
        payload = {
            'model': self.model.name,
            'messages': messages,
            'temperature': temperature,
            'stream': stream
        }

        if max_tokens:
            payload['max_tokens'] = max_tokens
        elif self.model.max_output_tokens:
            payload['max_tokens'] = self.model.max_output_tokens

        logger.debug(f"Sending chat request: {len(messages)} messages, {input_tokens} tokens")

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
        发送HTTP请求到 OpenAI 兼容的 API

        Args:
            payload: 请求payload

        Returns:
            str: 响应内容

        Raises:
            APIConnectionError: 连接失败
            APITimeoutError: 请求超时
            APIError: API 返回错误
        """
        # 构建请求 URL（兼容 OpenAI 和 Ollama）
        # Ollama: http://localhost:11434/api/chat
        # OpenAI: https://api.openai.com/v1/chat/completions
        if "localhost" in self.api_url or "127.0.0.1" in self.api_url:
            # Ollama 格式
            url = f"{self.api_url.rstrip('/')}/api/chat"
            # 转换为 Ollama 格式
            ollama_payload = {
                "model": payload["model"],
                "messages": payload["messages"],
                "stream": payload.get("stream", False)
            }
            if "temperature" in payload:
                ollama_payload["temperature"] = payload["temperature"]
            if "max_tokens" in payload:
                ollama_payload["max_tokens"] = payload["max_tokens"]

            headers = {"Content-Type": "application/json"}
            request_payload = ollama_payload
        else:
            # OpenAI 格式
            url = f"{self.api_url.rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            request_payload = payload

        logger.debug(f"Making HTTP request to: {url}")

        try:
            response = requests.post(
                url,
                json=request_payload,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code != 200:
                error_msg = f"API returned status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise APIError(error_msg)

            # 解析响应
            result = response.json()

            # Ollama 格式响应
            if "message" in result:
                return result["message"]["content"]
            # OpenAI 格式响应
            elif "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise APIError(f"Unexpected response format: {result}")

        except requests.exceptions.Timeout:
            raise APITimeoutError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Connection failed: {e}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")

    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        计算消息列表的token数

        Args:
            messages: 消息列表

        Returns:
            int: token数量
        """
        text = '\n'.join([m['content'] for m in messages])
        return self.token_manager.count_tokens(text)

    def estimate_cost(
        self,
        messages: List[Dict[str, str]],
        output_tokens: Optional[int] = None
    ) -> Optional[float]:
        """
        估算对话成本

        Args:
            messages: 消息列表
            output_tokens: 预估输出token数

        Returns:
            float: 成本（美元），如果模型无价格信息则返回None
        """
        text = '\n'.join([m['content'] for m in messages])
        return self.token_manager.estimate_cost(text, self.model, output_tokens)

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict: 模型信息
        """
        return {
            'name': self.model.name,
            'provider': self.model.provider,
            'max_input_tokens': self.model.max_input_tokens,
            'max_output_tokens': self.model.max_output_tokens,
            'context_limit': self.model.get_context_limit(),
            'code_score': self.model.code_score,
            'reasoning_score': self.model.reasoning_score,
        }
