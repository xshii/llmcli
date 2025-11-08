"""
工具调用系统 - Function Calling 支持
"""
from .registry import ToolRegistry, tool, get_registry
from .definitions import ToolDefinition, ToolCall, ToolResult

# TODO: 实现适配器
# from .adapters import (
#     ToolAdapter,
#     ClaudeToolAdapter,
#     OpenAIToolAdapter,
#     PromptBasedToolAdapter
# )

__all__ = [
    'ToolRegistry',
    'tool',
    'get_registry',
    'ToolDefinition',
    'ToolCall',
    'ToolResult',
    # 'ToolAdapter',
    # 'ClaudeToolAdapter',
    # 'OpenAIToolAdapter',
    # 'PromptBasedToolAdapter',
]
