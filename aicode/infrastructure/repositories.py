"""
Repository 具体实现 - 适配器模式
将现有的 DatabaseManager 和 ConfigManager 适配到抽象接口
"""

from typing import Any, Dict, List, Optional

from aicode.config.config_manager import ConfigManager
from aicode.database.db_manager import DatabaseManager
from aicode.interfaces.repositories import IConfigRepository, IModelRepository
from aicode.models.schema import ModelSchema


class SQLiteModelRepository(IModelRepository):
    """
    基于 SQLite 的模型仓储实现
    适配 DatabaseManager 到 IModelRepository 接口
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化仓储

        Args:
            db_manager: 数据库管理器实例
        """
        self._db = db_manager

    def get_model(self, name: str) -> ModelSchema:
        """获取单个模型"""
        return self._db.get_model(name)

    def insert_model(self, model: ModelSchema) -> None:
        """插入新模型"""
        self._db.insert_model(model)

    def update_model(self, name: str, **kwargs) -> None:
        """更新模型"""
        self._db.update_model(name, **kwargs)

    def delete_model(self, name: str) -> None:
        """删除模型"""
        self._db.delete_model(name)

    def query_models(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelSchema]:
        """查询模型列表"""
        return self._db.query_models(filters)


class YAMLConfigRepository(IConfigRepository):
    """
    基于 YAML 的配置仓储实现
    适配 ConfigManager 到 IConfigRepository 接口
    """

    def __init__(self, config_manager: ConfigManager):
        """
        初始化仓储

        Args:
            config_manager: 配置管理器实例
        """
        self._config = config_manager

    def config_exists(self) -> bool:
        """检查配置是否存在"""
        return self._config.config_exists()

    def load(self) -> None:
        """加载配置"""
        self._config.load()

    def save(self) -> None:
        """保存配置"""
        self._config.save()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self._config.set(key, value)

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.get_all()
