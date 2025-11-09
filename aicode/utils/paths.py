"""
路径工具 - 获取可配置的路径
"""

import os
from pathlib import Path
from typing import Optional

from aicode.config.constants import DEFAULT_CONFIG_DIR, DEFAULT_DB_PATH


def get_db_path(config_manager=None) -> str:
    """
    获取数据库路径（支持配置）

    优先级：
    1. 环境变量 AICODE_DB_PATH
    2. 配置文件 database.path
    3. 默认路径 ~/.aicode/aicode.db

    Args:
        config_manager: ConfigManager 实例（可选）

    Returns:
        str: 数据库路径
    """
    # 1. 环境变量
    env_path = os.environ.get("AICODE_DB_PATH")
    if env_path:
        return env_path

    # 2. 配置文件
    if config_manager and config_manager.config_exists():
        try:
            config_path = config_manager.get("database.path")
            if config_path:
                return config_path
        except:
            pass

    # 3. 默认路径
    return DEFAULT_DB_PATH


def get_config_dir() -> str:
    """
    获取配置目录

    优先级：
    1. 环境变量 AICODE_CONFIG_DIR
    2. 默认路径 ~/.aicode

    Returns:
        str: 配置目录路径
    """
    env_dir = os.environ.get("AICODE_CONFIG_DIR")
    if env_dir:
        return env_dir

    return DEFAULT_CONFIG_DIR


def ensure_dir(path: str) -> Path:
    """
    确保目录存在

    Args:
        path: 目录或文件路径

    Returns:
        Path: 路径对象
    """
    path_obj = Path(path).expanduser()

    # 如果是文件路径，获取父目录
    if path_obj.suffix:
        dir_path = path_obj.parent
    else:
        dir_path = path_obj

    # 创建目录
    dir_path.mkdir(parents=True, exist_ok=True)

    return path_obj


def get_db_manager():
    """
    获取配置好的 DatabaseManager 实例

    Returns:
        DatabaseManager: 数据库管理器
    """
    from aicode.config.config_manager import ConfigManager
    from aicode.database.db_manager import DatabaseManager

    try:
        config_manager = ConfigManager()
        if config_manager.config_exists():
            config_manager.load()
            db_path = get_db_path(config_manager)
        else:
            db_path = get_db_path(None)
    except:
        db_path = get_db_path(None)

    return DatabaseManager(db_path)
