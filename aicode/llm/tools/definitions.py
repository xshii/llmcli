"""
工具定义 - 统一的数据结构
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
import inspect
import uuid


@dataclass
class ToolDefinition:
    """工具定义（统一格式）"""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    function: Optional[Callable] = None  # 实际执行的函数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }

    @classmethod
    def from_function(cls, func: Callable, name: str = None, description: str = None) -> 'ToolDefinition':
        """
        从 Python 函数自动生成工具定义

        Args:
            func: Python 函数
            name: 工具名（默认使用函数名）
            description: 描述（默认使用函数 docstring）

        Returns:
            ToolDefinition

        Example:
            def get_weather(location: str, unit: str = "celsius") -> str:
                '''获取天气信息'''
                return f"{location}: 晴天"

            tool = ToolDefinition.from_function(get_weather)
        """
        import inspect
        from typing import get_type_hints

        # 获取函数签名
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # 构建参数 schema
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 获取类型
            param_type = type_hints.get(param_name, str)
            json_type = cls._python_type_to_json_type(param_type)

            # 提取注释作为描述
            param_info = {
                'type': json_type,
                'description': f'参数 {param_name}'
            }

            properties[param_name] = param_info

            # 判断是否必需（没有默认值）
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        parameters = {
            'type': 'object',
            'properties': properties,
            'required': required
        }

        return cls(
            name=name or func.__name__,
            description=description or (func.__doc__ or '').strip(),
            parameters=parameters,
            function=func
        )

    @staticmethod
    def _python_type_to_json_type(py_type) -> str:
        """将 Python 类型转换为 JSON Schema 类型"""
        type_mapping = {
            str: 'string',
            int: 'integer',
            float: 'number',
            bool: 'boolean',
            list: 'array',
            dict: 'object',
        }

        # 处理泛型类型（如 List[str]）
        if hasattr(py_type, '__origin__'):
            return type_mapping.get(py_type.__origin__, 'string')

        return type_mapping.get(py_type, 'string')

    def execute(self, arguments: Dict[str, Any]) -> Any:
        """
        执行工具函数

        Args:
            arguments: 参数字典

        Returns:
            函数执行结果
        """
        if self.function is None:
            raise ValueError(f"Tool '{self.name}' has no executable function")

        return self.function(**arguments)


@dataclass
class ToolCall:
    """工具调用请求"""

    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tool_name': self.tool_name,
            'arguments': self.arguments,
            'call_id': self.call_id
        }


@dataclass
class ToolResult:
    """工具执行结果"""

    call_id: str
    tool_name: str
    result: Any
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'call_id': self.call_id,
            'tool_name': self.tool_name,
            'result': self.result,
            'error': self.error
        }

    @property
    def is_error(self) -> bool:
        return self.error is not None

    def get_content(self) -> str:
        """获取用于返回给 LLM 的内容"""
        if self.is_error:
            return f"Error: {self.error}"
        return str(self.result)
