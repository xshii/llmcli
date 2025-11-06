"""
模型探测器 - 测试模型是否支持代码编辑格式
"""
import re
from typing import Dict, Any, Tuple
from aicode.llm.client import LLMClient
from aicode.llm.code_edit import CodeEditParser, create_inline_edit_prompt
from aicode.models.schema import ModelSchema
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class ModelProbe:
    """模型格式支持探测器"""

    # 测试提示词 - 简单的代码修改请求
    TEST_PROMPT = """Please modify the following Python function to add error handling:

```python
def divide(a, b):
    return a / b
```

Use the <file_edit> format to provide your changes."""

    # 污染模式检测（DeepSeek 等模型的思考标签）
    POLLUTION_PATTERNS = [
        r'<think>.*?</think>',  # DeepSeek 深度思考
        r'<thinking>.*?</thinking>',  # 其他思考标签
        r'<reflection>.*?</reflection>',  # 反思标签
        r'<内部思考>.*?</内部思考>',  # 中文思考标签
    ]

    def __init__(self, model: ModelSchema, api_key: str, api_url: str = None):
        """
        初始化探测器

        Args:
            model: 模型配置
            api_key: API 密钥
            api_url: API 地址
        """
        self.model = model
        self.client = LLMClient(model, api_key=api_key, api_url=api_url)
        logger.info(f"ModelProbe initialized for {model.name}")

    def probe(self) -> Dict[str, Any]:
        """
        探测模型格式支持能力

        Returns:
            Dict: 探测结果
            {
                'success': bool,
                'vscode_friendly': bool,
                'has_pollution': bool,
                'pollution_types': List[str],
                'edits_count': int,
                'raw_response': str,
                'error': str (if failed)
            }
        """
        result = {
            'success': False,
            'vscode_friendly': False,
            'has_pollution': False,
            'pollution_types': [],
            'edits_count': 0,
            'raw_response': '',
            'error': None
        }

        try:
            # 构建消息（包含系统提示）
            messages = [
                {'role': 'system', 'content': create_inline_edit_prompt()},
                {'role': 'user', 'content': self.TEST_PROMPT}
            ]

            # 发送请求
            logger.info(f"Probing model: {self.model.name}")
            response = self.client.chat(messages, temperature=0.7)
            result['raw_response'] = response
            result['success'] = True

            # 检测污染
            has_pollution, pollution_types = self._detect_pollution(response)
            result['has_pollution'] = has_pollution
            result['pollution_types'] = pollution_types

            # 清理污染后解析
            cleaned_response = self._clean_pollution(response)

            # 尝试解析编辑
            edits = CodeEditParser.parse(cleaned_response)
            result['edits_count'] = len(edits)

            # 判断是否 VSCode 友好
            # 标准：
            # 1. 能解析出至少 1 个编辑
            # 2. 没有严重污染（或污染可清理）
            # 3. 编辑格式正确
            result['vscode_friendly'] = (
                len(edits) > 0 and
                (not has_pollution or len(pollution_types) <= 1)
            )

            if result['vscode_friendly']:
                logger.info(f"✓ Model {self.model.name} is VSCode friendly")
            else:
                logger.warning(f"✗ Model {self.model.name} may not be VSCode friendly")

                if len(edits) == 0:
                    logger.warning("  Reason: No edits parsed")
                if has_pollution:
                    logger.warning(f"  Reason: Pollution detected - {pollution_types}")

        except Exception as e:
            logger.error(f"Probe failed for {self.model.name}: {e}")
            result['error'] = str(e)

        return result

    def _detect_pollution(self, text: str) -> Tuple[bool, list]:
        """
        检测文本中的污染标签

        Args:
            text: 响应文本

        Returns:
            Tuple[bool, List[str]]: (是否有污染, 污染类型列表)
        """
        pollution_types = []

        for pattern in self.POLLUTION_PATTERNS:
            if re.search(pattern, text, re.DOTALL | re.IGNORECASE):
                # 提取标签名
                tag_match = re.search(r'<(\w+)>', pattern)
                if tag_match:
                    pollution_types.append(tag_match.group(1))

        return len(pollution_types) > 0, pollution_types

    def _clean_pollution(self, text: str) -> str:
        """
        清理文本中的污染标签

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        cleaned = text
        for pattern in self.POLLUTION_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        return cleaned

    @staticmethod
    def clean_response(text: str) -> str:
        """
        静态方法：清理响应中的污染标签（供外部使用）

        Args:
            text: 原始响应

        Returns:
            str: 清理后的响应
        """
        cleaned = text
        for pattern in ModelProbe.POLLUTION_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        return cleaned


def probe_model(model: ModelSchema, api_key: str, api_url: str = None) -> Dict[str, Any]:
    """
    便捷函数：探测单个模型

    Args:
        model: 模型配置
        api_key: API 密钥
        api_url: API 地址

    Returns:
        Dict: 探测结果
    """
    probe = ModelProbe(model, api_key, api_url)
    return probe.probe()
