"""
测试全局常量定义
"""
import pytest
from aicode.config.constants import (
    VERSION,
    PROJECT_NAME,
    DEFAULT_DB_NAME,
    DEFAULT_DB_PATH,
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_MAX_TOKENS,
    TOKEN_BUFFER_RATIO,
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    DEFAULT_LOG_LEVEL,
    MIN_SCORE,
    MAX_SCORE,
    SPECIALTIES,
)


class TestConstants:
    """测试常量值"""

    def test_version_exists(self):
        """版本号应该存在"""
        assert VERSION is not None
        assert isinstance(VERSION, str)
        assert len(VERSION) > 0

    def test_project_name(self):
        """项目名称应该是 aicode"""
        assert PROJECT_NAME == "aicode"

    def test_database_config(self):
        """数据库配置应该正确"""
        assert DEFAULT_DB_NAME == "aicode.db"
        assert DEFAULT_DB_PATH.endswith("aicode.db")
        assert "~/.aicode" in DEFAULT_DB_PATH

    def test_config_paths(self):
        """配置路径应该正确"""
        assert DEFAULT_CONFIG_DIR == "~/.aicode"
        assert DEFAULT_CONFIG_FILE == "config.yaml"

    def test_token_config(self):
        """Token配置应该合理"""
        assert DEFAULT_MAX_TOKENS > 0
        assert 0 < TOKEN_BUFFER_RATIO < 1
        assert TOKEN_BUFFER_RATIO == 0.9

    def test_api_config(self):
        """API配置应该正确"""
        assert DEFAULT_API_URL.startswith("https://")
        assert DEFAULT_TIMEOUT > 0
        assert isinstance(DEFAULT_TIMEOUT, int)

    def test_log_config(self):
        """日志配置应该正确"""
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT
        assert DEFAULT_LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_score_range(self):
        """评分范围应该正确"""
        assert MIN_SCORE == 0.0
        assert MAX_SCORE == 10.0
        assert MIN_SCORE < MAX_SCORE

    def test_specialties_list(self):
        """专长列表应该包含预期值"""
        assert isinstance(SPECIALTIES, list)
        assert len(SPECIALTIES) > 0
        assert "code" in SPECIALTIES
        assert "reasoning" in SPECIALTIES
        assert "chat" in SPECIALTIES

    def test_all_specialties_are_strings(self):
        """所有专长应该是字符串"""
        for specialty in SPECIALTIES:
            assert isinstance(specialty, str)
            assert len(specialty) > 0
