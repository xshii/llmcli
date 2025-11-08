"""
工具注册表 - 管理所有可用工具
"""
from typing import Dict, List, Optional, Callable, Set
from functools import wraps
from aicode.llm.tools.definitions import ToolDefinition
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    工具注册表（单例模式）

    用法：
        1. 装饰器注册：
            @tool(name="get_weather", description="获取天气")
            def get_weather(location: str) -> str:
                return f"{location}: 晴天"

        2. 手动注册：
            registry = ToolRegistry.get_instance()
            registry.register(tool_def)

        3. 获取工具：
            tools = registry.get_tools()  # 所有工具
            tools = registry.get_tools(tags=['weather'])  # 按标签筛选
    """

    _instance = None

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._tags: Dict[str, Set[str]] = {}  # tag -> tool_names
        logger.debug("ToolRegistry initialized")

    @classmethod
    def get_instance(cls) -> 'ToolRegistry':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """重置单例（主要用于测试）"""
        cls._instance = None

    def register(
        self,
        tool: ToolDefinition,
        tags: Optional[List[str]] = None,
        override: bool = False
    ) -> None:
        """
        注册工具

        Args:
            tool: 工具定义
            tags: 标签列表（用于分类和筛选）
            override: 是否覆盖已存在的工具

        Raises:
            ValueError: 工具已存在且 override=False
        """
        if tool.name in self._tools and not override:
            raise ValueError(f"Tool '{tool.name}' already registered. Use override=True to replace.")

        self._tools[tool.name] = tool

        # 注册标签
        if tags:
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = set()
                self._tags[tag].add(tool.name)

        logger.info(f"Registered tool: {tool.name} (tags: {tags or []})")

    def register_function(
        self,
        func: Callable,
        name: str = None,
        description: str = None,
        tags: Optional[List[str]] = None
    ) -> ToolDefinition:
        """
        从函数注册工具（便捷方法）

        Args:
            func: Python 函数
            name: 工具名（默认函数名）
            description: 描述（默认 docstring）
            tags: 标签列表

        Returns:
            ToolDefinition
        """
        tool = ToolDefinition.from_function(func, name=name, description=description)
        self.register(tool, tags=tags)
        return tool

    def unregister(self, tool_name: str) -> None:
        """
        注销工具

        Args:
            tool_name: 工具名
        """
        if tool_name in self._tools:
            del self._tools[tool_name]

            # 清理标签
            for tag_set in self._tags.values():
                tag_set.discard(tool_name)

            logger.info(f"Unregistered tool: {tool_name}")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """
        获取单个工具

        Args:
            name: 工具名

        Returns:
            ToolDefinition 或 None
        """
        return self._tools.get(name)

    def get_tools(
        self,
        names: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None
    ) -> List[ToolDefinition]:
        """
        获取工具列表（支持多种筛选方式）

        Args:
            names: 指定工具名列表（优先级最高）
            tags: 包含的标签（OR 关系）
            exclude_tags: 排除的标签

        Returns:
            工具列表

        Examples:
            # 获取所有工具
            tools = registry.get_tools()

            # 获取指定工具
            tools = registry.get_tools(names=['get_weather', 'search_web'])

            # 按标签筛选
            tools = registry.get_tools(tags=['weather', 'search'])

            # 排除某些标签
            tools = registry.get_tools(exclude_tags=['experimental'])
        """
        # 1. 如果指定了名称，直接返回
        if names is not None:
            return [self._tools[name] for name in names if name in self._tools]

        # 2. 获取候选集合
        candidate_names = set(self._tools.keys())

        # 3. 按标签筛选（OR 关系）
        if tags:
            tagged_names = set()
            for tag in tags:
                tagged_names.update(self._tags.get(tag, set()))
            candidate_names &= tagged_names

        # 4. 排除标签
        if exclude_tags:
            for tag in exclude_tags:
                candidate_names -= self._tags.get(tag, set())

        return [self._tools[name] for name in candidate_names]

    def list_tools(self) -> List[str]:
        """列出所有工具名"""
        return list(self._tools.keys())

    def list_tags(self) -> List[str]:
        """列出所有标签"""
        return list(self._tags.keys())

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        self._tags.clear()
        logger.info("Cleared all tools")


# 全局实例（便捷访问）
_global_registry = ToolRegistry.get_instance()


def tool(
    name: str = None,
    description: str = None,
    tags: Optional[List[str]] = None
):
    """
    装饰器：将函数注册为工具

    Args:
        name: 工具名（默认函数名）
        description: 描述（默认 docstring）
        tags: 标签列表

    Example:
        @tool(name="get_weather", tags=["weather"])
        def get_weather(location: str, unit: str = "celsius") -> str:
            '''获取指定城市的天气'''
            return f"{location}: 晴天, 15°C"

        # 自动注册到全局注册表
        # 客户端可以通过 registry.get_tools(tags=['weather']) 获取
    """
    def decorator(func: Callable) -> Callable:
        # 注册到全局注册表
        _global_registry.register_function(
            func,
            name=name,
            description=description,
            tags=tags
        )

        # 返回原函数（保持可调用）
        return func

    return decorator


def get_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return _global_registry
