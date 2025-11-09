"""
依赖注入容器 - Dependency Injection Container
支持惰性加载（Lazy Loading）和单例模式（Singleton）
"""

from typing import Callable, Generic, Optional, TypeVar

from aicode.config.config_manager import ConfigManager
from aicode.database.db_manager import DatabaseManager
from aicode.infrastructure.repositories import (
    SQLiteModelRepository,
    YAMLConfigRepository,
)
from aicode.interfaces.repositories import IConfigRepository, IModelRepository
from aicode.utils.logger import get_logger
from aicode.utils.paths import get_db_path

logger = get_logger(__name__)

T = TypeVar("T")


class LazyDependency(Generic[T]):
    """
    惰性依赖包装器
    只在第一次访问时才创建实例（Lazy Loading + Singleton）
    """

    def __init__(self, factory: Callable[[], T]):
        """
        初始化惰性依赖

        Args:
            factory: 工厂函数，用于创建实例
        """
        self._factory = factory
        self._instance: Optional[T] = None
        self._initialized = False

    def get(self) -> T:
        """
        获取实例（惰性初始化）

        Returns:
            T: 依赖实例
        """
        if not self._initialized:
            logger.debug(f"Lazy loading dependency: {self._factory.__name__}")
            self._instance = self._factory()
            self._initialized = True
        return self._instance

    def reset(self) -> None:
        """重置实例（用于测试）"""
        self._instance = None
        self._initialized = False


class DIContainer:
    """
    依赖注入容器
    管理应用程序的所有依赖，支持惰性加载
    """

    _instance: Optional["DIContainer"] = None
    _initialized = False

    def __new__(cls):
        """单例模式：确保全局只有一个容器实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化容器（只执行一次）"""
        if not DIContainer._initialized:
            # 使用惰性依赖包装器
            self._config_repo = LazyDependency(self._create_config_repository)
            self._model_repo = LazyDependency(self._create_model_repository)
            DIContainer._initialized = True
            logger.info("DIContainer initialized (lazy loading enabled)")

    # ==================== Repository Getters ====================

    def get_model_repository(self) -> IModelRepository:
        """
        获取模型仓储（惰性加载）

        Returns:
            IModelRepository: 模型仓储实例
        """
        return self._model_repo.get()

    def get_config_repository(self) -> IConfigRepository:
        """
        获取配置仓储（惰性加载）

        Returns:
            IConfigRepository: 配置仓储实例
        """
        return self._config_repo.get()

    # ==================== Factory Methods ====================

    def _create_config_repository(self) -> IConfigRepository:
        """
        创建配置仓储实例

        Returns:
            IConfigRepository: 配置仓储
        """
        logger.debug("Creating ConfigRepository...")
        config_manager = ConfigManager()
        return YAMLConfigRepository(config_manager)

    def _create_model_repository(self) -> IModelRepository:
        """
        创建模型仓储实例

        Returns:
            IModelRepository: 模型仓储
        """
        logger.debug("Creating ModelRepository...")
        # 获取配置来确定数据库路径
        config_repo = self.get_config_repository()

        # 确定数据库路径
        try:
            if config_repo.config_exists():
                config_repo.load()
                db_path = get_db_path(None)  # 从环境变量或默认路径获取
            else:
                db_path = get_db_path(None)
        except Exception:
            db_path = get_db_path(None)

        db_manager = DatabaseManager(db_path)
        return SQLiteModelRepository(db_manager)

    # ==================== Testing Support ====================

    def reset(self) -> None:
        """
        重置所有依赖（仅用于测试）

        警告：在生产代码中不要调用此方法！
        """
        logger.warning("Resetting DIContainer (should only be used in tests)")
        self._config_repo.reset()
        self._model_repo.reset()

    def register_model_repository(self, repo: IModelRepository) -> None:
        """
        手动注册模型仓储（用于测试 mock）

        Args:
            repo: 模型仓储实例
        """
        self._model_repo = LazyDependency(lambda: repo)

    def register_config_repository(self, repo: IConfigRepository) -> None:
        """
        手动注册配置仓储（用于测试 mock）

        Args:
            repo: 配置仓储实例
        """
        self._config_repo = LazyDependency(lambda: repo)


# ==================== 全局容器实例 ====================

_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """
    获取全局依赖容器（单例）

    Returns:
        DIContainer: 依赖容器实例
    """
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def reset_container() -> None:
    """
    重置全局容器（仅用于测试）
    """
    global _container
    if _container:
        _container.reset()
    _container = None
