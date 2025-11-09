"""
测试配置管理器
"""

import json
import os
import tempfile

import pytest
import yaml

from aicode.config.config_manager import ConfigManager
from aicode.llm.exceptions import (
    ConfigError,
    ConfigFileNotFoundError,
    InvalidConfigError,
)


@pytest.fixture
def temp_config_yaml():
    """临时YAML配置文件"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config = {
            "global": {"api_key": "sk-test", "api_url": "https://api.openai.com/v1"},
            "models": [{"name": "gpt-4", "provider": "openai", "code_score": 9.0}],
        }
        yaml.safe_dump(config, f)
        config_path = f.name
    yield config_path
    if os.path.exists(config_path):
        os.unlink(config_path)


@pytest.fixture
def temp_config_json():
    """临时JSON配置文件"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {"global": {"api_key": "sk-test"}}
        json.dump(config, f)
        config_path = f.name
    yield config_path
    if os.path.exists(config_path):
        os.unlink(config_path)


@pytest.fixture
def config_manager(temp_config_yaml):
    """配置管理器fixture"""
    return ConfigManager(temp_config_yaml)


class TestConfigManager:
    """测试ConfigManager基本功能"""

    def test_init_with_path(self, temp_config_yaml):
        """应该能用指定路径初始化"""
        cm = ConfigManager(temp_config_yaml)
        assert cm.config_path == temp_config_yaml

    def test_init_default_path(self):
        """应该能用默认路径初始化"""
        cm = ConfigManager()
        assert ".aicode" in cm.config_path
        assert "config.yaml" in cm.config_path

    def test_load_yaml(self, temp_config_yaml):
        """应该能加载YAML配置"""
        cm = ConfigManager(temp_config_yaml)
        config = cm.load()
        assert "global" in config
        assert config["global"]["api_key"] == "sk-test"

    def test_load_json(self, temp_config_json):
        """应该能加载JSON配置"""
        cm = ConfigManager(temp_config_json)
        config = cm.load()
        assert "global" in config

    def test_load_nonexistent_file(self):
        """加载不存在的文件应该报错"""
        cm = ConfigManager("/nonexistent/config.yaml")
        with pytest.raises(ConfigFileNotFoundError):
            cm.load()

    def test_save_yaml(self):
        """应该能保存YAML配置"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            config_path = f.name

        try:
            cm = ConfigManager(config_path)
            cm.save({"test": "value"})
            assert os.path.exists(config_path)

            # 验证保存的内容
            with open(config_path) as f:
                loaded = yaml.safe_load(f)
            assert loaded["test"] == "value"
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_save_json(self):
        """应该能保存JSON配置"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_path = f.name

        try:
            cm = ConfigManager(config_path)
            cm.save({"test": "value"})

            with open(config_path) as f:
                loaded = json.load(f)
            assert loaded["test"] == "value"
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_config_exists(self, temp_config_yaml):
        """应该能检查配置文件是否存在"""
        cm = ConfigManager(temp_config_yaml)
        assert cm.config_exists()

        cm2 = ConfigManager("/nonexistent/config.yaml")
        assert not cm2.config_exists()


class TestConfigGetSet:
    """测试配置读写"""

    def test_get_simple_key(self, config_manager):
        """应该能获取简单键"""
        config_manager.load()
        value = config_manager.get("global")
        assert value is not None
        assert "api_key" in value

    def test_get_nested_key(self, config_manager):
        """应该能获取嵌套键"""
        config_manager.load()
        value = config_manager.get("global.api_key")
        assert value == "sk-test"

    def test_get_nonexistent_key(self, config_manager):
        """获取不存在的键应该返回默认值"""
        config_manager.load()
        value = config_manager.get("nonexistent", "default")
        assert value == "default"

    def test_set_simple_key(self, config_manager):
        """应该能设置简单键"""
        config_manager.load()
        config_manager.set("new_key", "new_value")
        assert config_manager.get("new_key") == "new_value"

    def test_set_nested_key(self, config_manager):
        """应该能设置嵌套键"""
        config_manager.load()
        config_manager.set("global.new_field", "value")
        assert config_manager.get("global.new_field") == "value"

    def test_get_global_config(self, config_manager):
        """应该能获取全局配置"""
        config_manager.load()
        global_config = config_manager.get_global_config()
        assert "api_key" in global_config

    def test_get_models_config(self, config_manager):
        """应该能获取模型配置列表"""
        config_manager.load()
        models = config_manager.get_models_config()
        assert isinstance(models, list)
        assert len(models) > 0


class TestConfigValidation:
    """测试配置验证"""

    def test_validate_valid_config(self, config_manager):
        """有效配置应该验证通过"""
        config_manager.load()
        assert config_manager.validate_config()

    def test_validate_empty_config(self):
        """空配置应该验证通过"""
        cm = ConfigManager()
        cm.config = {}
        assert cm.validate_config()

    def test_validate_invalid_config_type(self):
        """无效配置类型应该报错"""
        cm = ConfigManager()
        cm.config = []  # 应该是字典
        with pytest.raises(InvalidConfigError, match="must be a dictionary"):
            cm.validate_config()

    def test_validate_invalid_global_type(self):
        """无效的global配置类型应该报错"""
        cm = ConfigManager()
        cm.config = {"global": "invalid"}
        with pytest.raises(InvalidConfigError):
            cm.validate_config()

    def test_validate_invalid_models_type(self):
        """无效的models配置类型应该报错"""
        cm = ConfigManager()
        cm.config = {"models": "invalid"}
        with pytest.raises(InvalidConfigError):
            cm.validate_config()

    def test_validate_model_missing_name(self):
        """模型缺少name应该报错"""
        cm = ConfigManager()
        cm.config = {"models": [{"provider": "openai"}]}
        with pytest.raises(InvalidConfigError, match="missing 'name'"):
            cm.validate_config()

    def test_validate_model_missing_provider(self):
        """模型缺少provider应该报错"""
        cm = ConfigManager()
        cm.config = {"models": [{"name": "gpt-4"}]}
        with pytest.raises(InvalidConfigError, match="missing 'provider'"):
            cm.validate_config()


class TestConfigImport:
    """测试模型导入"""

    def test_import_models(self, config_manager):
        """应该能从配置导入模型"""
        config_manager.load()
        models = config_manager.import_models()
        assert len(models) > 0
        assert models[0].name == "gpt-4"

    def test_import_models_empty(self):
        """空模型列表应该返回空"""
        cm = ConfigManager()
        cm.config = {"models": []}
        models = cm.import_models()
        assert models == []

    def test_import_invalid_model(self):
        """导入无效模型应该报错"""
        cm = ConfigManager()
        cm.config = {"models": [{"provider": "openai"}]}  # 缺少name
        with pytest.raises(InvalidConfigError):
            cm.import_models()


class TestConfigMerge:
    """测试配置合并"""

    def test_merge_simple(self):
        """应该能合并简单配置"""
        cm = ConfigManager()
        cm.config = {"a": 1, "b": 2}
        cm.merge_config({"c": 3})
        assert cm.config == {"a": 1, "b": 2, "c": 3}

    def test_merge_overwrite(self):
        """合并应该覆盖已有键"""
        cm = ConfigManager()
        cm.config = {"a": 1, "b": 2}
        cm.merge_config({"a": 10})
        assert cm.config["a"] == 10

    def test_merge_nested(self):
        """应该能递归合并嵌套字典"""
        cm = ConfigManager()
        cm.config = {"global": {"api_key": "old", "timeout": 30}}
        cm.merge_config({"global": {"api_key": "new"}})
        assert cm.config["global"]["api_key"] == "new"
        assert cm.config["global"]["timeout"] == 30


class TestDefaultConfig:
    """测试默认配置"""

    def test_create_default_config(self):
        """应该能创建默认配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            cm = ConfigManager(config_path)
            cm.create_default_config()

            assert os.path.exists(config_path)
            cm.load()
            assert "global" in cm.config
            assert "models" in cm.config
