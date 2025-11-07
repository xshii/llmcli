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
        探测模型格式支持能力（仅 XML 格式）

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

    def probe_full(self) -> Dict[str, Any]:
        """
        完整探测模型能力：FC、XML、JSON

        如果支持 FC，则跳过 XML 和 JSON 测试

        Returns:
            Dict: 探测结果
            {
                'success': bool,
                'vscode_friendly': bool,
                'supports_function_calling': bool,
                'supports_xml_format': bool,
                'supports_json_mode': bool,
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
            'supports_function_calling': False,
            'supports_xml_format': False,
            'supports_json_mode': False,
            'has_pollution': False,
            'pollution_types': [],
            'edits_count': 0,
            'raw_response': '',
            'error': None
        }

        try:
            # 1. 测试 Function Calling
            logger.info("Testing Function Calling support...")
            fc_result = self._test_function_calling()

            if fc_result['success']:
                result['supports_function_calling'] = True
                result['success'] = True
                result['vscode_friendly'] = True
                logger.info("✓ Model supports Function Calling")
                logger.info("  Skipping XML and JSON tests (FC is preferred)")

                # FC 支持，直接返回，不测试其他格式
                return result

            # 2. 测试 XML 格式
            logger.info("Testing XML format support...")
            xml_result = self._test_xml_format()

            if xml_result['success']:
                result['supports_xml_format'] = True
                result['vscode_friendly'] = xml_result.get('vscode_friendly', False)
                result['has_pollution'] = xml_result.get('has_pollution', False)
                result['pollution_types'] = xml_result.get('pollution_types', [])
                result['edits_count'] = xml_result.get('edits_count', 0)
                result['raw_response'] = xml_result.get('raw_response', '')
                result['success'] = True
                logger.info(f"✓ Model supports XML format (edits: {result['edits_count']})")

            # 3. 测试 JSON Mode
            logger.info("Testing JSON mode support...")
            json_result = self._test_json_mode()

            if json_result['success']:
                result['supports_json_mode'] = True
                result['success'] = True
                logger.info("✓ Model supports JSON mode")

            # 综合判断
            if result['supports_function_calling']:
                result['vscode_friendly'] = True
            elif result['supports_xml_format'] and result['edits_count'] > 0:
                result['vscode_friendly'] = True

        except Exception as e:
            logger.error(f"Full probe failed for {self.model.name}: {e}")
            result['error'] = str(e)

        return result

    def _test_function_calling(self) -> Dict[str, Any]:
        """
        测试 Function Calling 支持

        Returns:
            Dict: 测试结果
        """
        # 简单的工具定义
        test_tool = {
            "name": "edit_file",
            "description": "Edit or create a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["file_path", "content"]
            }
        }

        try:
            # 构建请求
            messages = [{"role": "user", "content": "Test message"}]

            # 尝试调用（注意：LLMClient 当前可能不支持 tools 参数）
            # 这里我们简单测试是否会报错
            # 实际实现需要检查 API 响应

            # TODO: 需要 LLMClient 支持 tools 参数
            # response = self.client.chat(messages, tools=[test_tool])

            # 暂时返回 False，表示不支持
            # 当 LLMClient 实现 FC 后，这里需要真正测试
            logger.debug("FC test: LLMClient does not support tools parameter yet")
            return {'success': False, 'error': 'FC not implemented in LLMClient'}

        except Exception as e:
            # 如果是参数错误，说明不支持
            error_msg = str(e).lower()
            if 'tool' in error_msg or 'function' in error_msg:
                logger.debug(f"FC test failed (not supported): {e}")
                return {'success': False, 'error': str(e)}

            # 其他错误
            logger.error(f"FC test error: {e}")
            return {'success': False, 'error': str(e)}

    def _test_xml_format(self) -> Dict[str, Any]:
        """
        测试 XML 格式支持（使用现有的 probe 方法）

        Returns:
            Dict: 测试结果
        """
        return self.probe()

    def _test_json_mode(self) -> Dict[str, Any]:
        """
        测试 JSON Mode 支持

        Returns:
            Dict: 测试结果
        """
        try:
            # 构建请求
            messages = [
                {'role': 'system', 'content': 'You always respond with valid JSON'},
                {'role': 'user', 'content': 'Return {"status": "ok"}'}
            ]

            # 尝试请求（需要 response_format 参数）
            # TODO: 需要 LLMClient 支持 response_format 参数
            # response = self.client.chat(messages, response_format={"type": "json_object"})

            # 暂时返回 False
            logger.debug("JSON mode test: LLMClient does not support response_format yet")
            return {'success': False, 'error': 'JSON mode not implemented in LLMClient'}

        except Exception as e:
            logger.debug(f"JSON mode test failed: {e}")
            return {'success': False, 'error': str(e)}

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
    便捷函数：探测单个模型（仅 XML 格式）

    Args:
        model: 模型配置
        api_key: API 密钥
        api_url: API 地址

    Returns:
        Dict: 探测结果
    """
    probe = ModelProbe(model, api_key, api_url)
    return probe.probe()


def probe_model_full(model: ModelSchema, api_key: str, api_url: str = None) -> Dict[str, Any]:
    """
    便捷函数：完整探测模型能力（FC + XML + JSON）

    Args:
        model: 模型配置
        api_key: API 密钥
        api_url: API 地址

    Returns:
        Dict: 完整探测结果
    """
    probe = ModelProbe(model, api_key, api_url)
    return probe.probe_full()
