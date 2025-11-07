"""
Repository 抽象接口 - 依赖倒置的核心
遵循依赖倒置原则 (DIP): 高层模块依赖抽象，而非具体实现
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from aicode.models.schema import ModelSchema


class IModelRepository(ABC):
    """模型数据访问抽象接口"""

    @abstractmethod
    def get_model(self, name: str) -> ModelSchema:
        """
        获取单个模型

        Args:
            name: 模型名称

        Returns:
            ModelSchema: 模型对象

        Raises:
            ModelNotFoundError: 模型不存在
        """
        pass

    @abstractmethod
    def insert_model(self, model: ModelSchema) -> None:
        """
        插入新模型

        Args:
            model: 模型对象

        Raises:
            ModelAlreadyExistsError: 模型已存在
        """
        pass

    @abstractmethod
    def update_model(self, name: str, **kwargs) -> None:
        """
        更新模型

        Args:
            name: 模型名称
            **kwargs: 要更新的字段

        Raises:
            ModelNotFoundError: 模型不存在
        """
        pass

    @abstractmethod
    def delete_model(self, name: str) -> None:
        """
        删除模型

        Args:
            name: 模型名称

        Raises:
            ModelNotFoundError: 模型不存在
        """
        pass

    @abstractmethod
    def query_models(self, filters: Optional[Dict[str, Any]] = None) -> List[ModelSchema]:
        """
        查询模型列表

        Args:
            filters: 筛选条件

        Returns:
            List[ModelSchema]: 模型列表
        """
        pass


class IConfigRepository(ABC):
    """配置数据访问抽象接口"""

    @abstractmethod
    def config_exists(self) -> bool:
        """
        检查配置是否存在

        Returns:
            bool: 配置是否存在
        """
        pass

    @abstractmethod
    def load(self) -> None:
        """
        加载配置

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        pass

    @abstractmethod
    def save(self) -> None:
        """
        保存配置
        """
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键 (支持点号分隔, 如 'global.api_key')
            default: 默认值

        Returns:
            Any: 配置值
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项

        Args:
            key: 配置键
            value: 配置值
        """
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置

        Returns:
            Dict[str, Any]: 完整配置字典
        """
        pass
