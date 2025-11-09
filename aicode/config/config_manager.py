"""
配置文件管理器（支持YAML/JSON）
"""

import json
import os
from typing import Any, Dict, List, Optional

import yaml

from aicode.config.constants import DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE
from aicode.llm.exceptions import (
    ConfigError,
    ConfigFileNotFoundError,
    InvalidConfigError,
)
from aicode.models.schema import import_model_from_preconfig
from aicode.utils.logger import get_logger
from aicode.utils.validators import validate_model_data

logger = get_logger(__name__)


class ConfigManager:
    """配置文件管理器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认使用 ~/.aicode/config.yaml
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.expanduser(DEFAULT_CONFIG_DIR), DEFAULT_CONFIG_FILE
            )
        self.config_path = os.path.expanduser(config_path)
        self.config: Dict[str, Any] = {}
        logger.debug(f"ConfigManager initialized with path: {self.config_path}")

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            Dict[str, Any]: 配置字典

        Raises:
            ConfigFileNotFoundError: 配置文件不存在
            InvalidConfigError: 配置文件格式错误
        """
        if not os.path.exists(self.config_path):
            raise ConfigFileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                # 根据文件扩展名选择解析器
                if self.config_path.endswith(".json"):
                    self.config = json.load(f)
                else:
                    # 默认使用YAML
                    self.config = yaml.safe_load(f) or {}

            logger.info(f"Loaded config from {self.config_path}")
            return self.config

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            logger.error(f"Invalid config file format: {e}")
            raise InvalidConfigError(f"Invalid config file format: {e}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise ConfigError(f"Failed to load config: {e}")

    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        保存配置到文件

        Args:
            config: 要保存的配置字典，None则保存当前配置

        Raises:
            ConfigError: 保存失败
        """
        if config is not None:
            self.config = config

        # 确保目录存在
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            logger.debug(f"Created config directory: {config_dir}")

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                if self.config_path.endswith(".json"):
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                else:
                    yaml.safe_dump(
                        self.config, f, default_flow_style=False, allow_unicode=True
                    )

            logger.info(f"Saved config to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise ConfigError(f"Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'global.api_key'）
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
        """
        keys = key.split(".")
        config = self.config

        # 导航到最后一级的父字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value
        logger.debug(f"Set config: {key} = {value}")

    def get_global_config(self) -> Dict[str, Any]:
        """
        获取全局配置

        Returns:
            Dict[str, Any]: 全局配置字典
        """
        return self.config.get("global", {})

    def get_models_config(self) -> List[Dict[str, Any]]:
        """
        获取模型配置列表

        Returns:
            List[Dict[str, Any]]: 模型配置列表
        """
        models = self.config.get("models", [])
        if not isinstance(models, list):
            logger.warning("models config is not a list, returning empty list")
            return []
        return models

    def validate_config(self) -> bool:
        """
        验证配置文件

        Returns:
            bool: 配置有效返回True

        Raises:
            InvalidConfigError: 配置无效
        """
        # 检查基本结构
        if not isinstance(self.config, dict):
            raise InvalidConfigError("Config must be a dictionary")

        # 验证全局配置（如果存在）
        if "global" in self.config:
            global_config = self.config["global"]
            if not isinstance(global_config, dict):
                raise InvalidConfigError("global config must be a dictionary")

        # 验证模型配置（如果存在）
        if "models" in self.config:
            models = self.config["models"]
            if not isinstance(models, list):
                raise InvalidConfigError("models config must be a list")

            # 验证每个模型
            for i, model in enumerate(models):
                if not isinstance(model, dict):
                    raise InvalidConfigError(f"Model {i} must be a dictionary")

                # 验证必需字段
                if "name" not in model:
                    raise InvalidConfigError(f"Model {i} missing 'name' field")
                if "provider" not in model:
                    raise InvalidConfigError(f"Model {i} missing 'provider' field")

                # 使用验证器验证模型数据
                try:
                    validate_model_data(model)
                except Exception as e:
                    raise InvalidConfigError(
                        f"Model {i} ({model.get('name', 'unknown')}) validation failed: {e}"
                    )

        logger.info("Config validation passed")
        return True

    def import_models(self):
        """
        从配置导入模型

        Returns:
            List[ModelSchema]: 导入的模型列表

        Raises:
            InvalidConfigError: 模型配置无效
        """
        from aicode.models.schema import ModelSchema

        models_config = self.get_models_config()
        models = []

        for model_config in models_config:
            try:
                model = import_model_from_preconfig(model_config)
                models.append(model)
                logger.debug(f"Imported model from config: {model.name}")
            except Exception as e:
                logger.error(f"Failed to import model {model_config.get('name')}: {e}")
                raise InvalidConfigError(f"Failed to import model: {e}")

        logger.info(f"Imported {len(models)} models from config")
        return models

    def merge_config(self, other: Dict[str, Any]) -> None:
        """
        合并配置（递归合并）

        Args:
            other: 要合并的配置字典
        """
        self.config = self._deep_merge(self.config, other)
        logger.debug("Merged config")

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """
        递归合并字典

        Args:
            base: 基础字典
            update: 更新字典

        Returns:
            合并后的字典
        """
        result = base.copy()

        for key, value in update.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def config_exists(self) -> bool:
        """
        检查配置文件是否存在

        Returns:
            bool: 存在返回True
        """
        return os.path.exists(self.config_path)

    def create_default_config(self) -> None:
        """
        创建默认配置文件
        """
        default_config = {
            "global": {
                "api_key": "",
                "api_url": "https://api.openai.com/v1",
                "default_model": "gpt-4",
            },
            "models": [],
        }

        self.save(default_config)
        logger.info(f"Created default config at {self.config_path}")
