"""
Token计数和管理
"""
from typing import Optional
import tiktoken
from aicode.models.schema import ModelSchema
from aicode.llm.exceptions import TokenError, TokenLimitExceededError
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class TokenManager:
    """Token计数和管理器"""

    # 默认编码器（用于未知模型）
    DEFAULT_ENCODING = "cl100k_base"

    # 模型到编码器的映射
    MODEL_ENCODINGS = {
        'gpt-4': 'cl100k_base',
        'gpt-4-32k': 'cl100k_base',
        'gpt-4-turbo': 'cl100k_base',
        'gpt-3.5-turbo': 'cl100k_base',
        'text-embedding-ada-002': 'cl100k_base',
        'text-davinci-003': 'p50k_base',
        'text-davinci-002': 'p50k_base',
    }

    def __init__(self, model_name: Optional[str] = None, encoding_name: Optional[str] = None):
        """
        初始化Token管理器

        Args:
            model_name: 模型名称（用于自动选择编码器）
            encoding_name: 编码器名称（手动指定，优先级高于model_name）
        """
        self.model_name = model_name
        self.encoding_name = encoding_name or self._get_encoding_name(model_name)

        try:
            self.encoding = tiktoken.get_encoding(self.encoding_name)
            logger.debug(f"TokenManager initialized with encoding: {self.encoding_name}")
        except Exception as e:
            logger.error(f"Failed to load encoding {self.encoding_name}: {e}")
            raise TokenError(f"Failed to load encoding: {e}")

    def _get_encoding_name(self, model_name: Optional[str]) -> str:
        """
        根据模型名称获取编码器名称

        Args:
            model_name: 模型名称

        Returns:
            编码器名称
        """
        if model_name is None:
            return self.DEFAULT_ENCODING

        # 精确匹配
        if model_name in self.MODEL_ENCODINGS:
            return self.MODEL_ENCODINGS[model_name]

        # 前缀匹配
        for model_prefix, encoding in self.MODEL_ENCODINGS.items():
            if model_name.startswith(model_prefix):
                return encoding

        # 默认编码器
        logger.debug(f"Unknown model {model_name}, using default encoding")
        return self.DEFAULT_ENCODING

    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量

        Args:
            text: 文本内容

        Returns:
            token数量
        """
        if not text:
            return 0

        try:
            tokens = self.encoding.encode(text)
            count = len(tokens)
            logger.debug(f"Counted {count} tokens in text of {len(text)} chars")
            return count
        except Exception as e:
            logger.error(f"Failed to count tokens: {e}")
            raise TokenError(f"Failed to count tokens: {e}")

    def check_limit(self, text: str, model: ModelSchema) -> bool:
        """
        检查文本是否超过模型的token限制

        Args:
            text: 文本内容
            model: 模型Schema

        Returns:
            bool: 未超过限制返回True

        Raises:
            TokenLimitExceededError: token超过限制
        """
        token_count = self.count_tokens(text)
        limit = model.get_context_limit()

        if limit is None:
            logger.warning(f"No token limit defined for model {model.name}")
            return True

        if token_count > limit:
            raise TokenLimitExceededError(
                f"Token count {token_count} exceeds limit {limit} for model {model.name}"
            )

        logger.debug(f"Token check passed: {token_count}/{limit}")
        return True

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """
        截断文本到指定token数量

        Args:
            text: 文本内容
            max_tokens: 最大token数量

        Returns:
            截断后的文本
        """
        if not text or max_tokens <= 0:
            return ""

        try:
            tokens = self.encoding.encode(text)

            if len(tokens) <= max_tokens:
                return text

            # 截断并解码
            truncated_tokens = tokens[:max_tokens]
            truncated_text = self.encoding.decode(truncated_tokens)

            logger.debug(
                f"Truncated text from {len(tokens)} to {max_tokens} tokens"
            )
            return truncated_text

        except Exception as e:
            logger.error(f"Failed to truncate text: {e}")
            raise TokenError(f"Failed to truncate text: {e}")

    def estimate_cost(
        self,
        text: str,
        model: ModelSchema,
        output_tokens: Optional[int] = None
    ) -> Optional[float]:
        """
        估算API调用成本

        Args:
            text: 输入文本
            model: 模型Schema
            output_tokens: 预估的输出token数（可选）

        Returns:
            估算成本（美元），如果模型没有价格信息则返回None
        """
        input_tokens = self.count_tokens(text)

        # 检查是否有价格信息
        if model.cost_per_1k_input is None:
            return None

        input_cost = (input_tokens / 1000) * model.cost_per_1k_input

        output_cost = 0.0
        if output_tokens is not None and model.cost_per_1k_output is not None:
            output_cost = (output_tokens / 1000) * model.cost_per_1k_output

        total_cost = input_cost + output_cost
        logger.debug(
            f"Estimated cost: ${total_cost:.6f} "
            f"(input: {input_tokens} tokens, output: {output_tokens or 0} tokens)"
        )
        return total_cost

    def get_remaining_tokens(self, text: str, model: ModelSchema) -> Optional[int]:
        """
        获取剩余可用token数

        Args:
            text: 已使用的文本
            model: 模型Schema

        Returns:
            剩余token数，如果模型没有限制则返回None
        """
        limit = model.get_context_limit()
        if limit is None:
            return None

        used = self.count_tokens(text)
        remaining = limit - used

        logger.debug(f"Remaining tokens: {remaining}/{limit}")
        return max(0, remaining)
