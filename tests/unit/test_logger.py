"""
测试日志系统
"""

import logging

import pytest

from aicode.utils.logger import get_logger


class TestLogger:
    """测试日志功能"""

    def test_get_logger_returns_logger(self):
        """get_logger应该返回Logger实例"""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_name(self):
        """get_logger应该使用指定的名称"""
        logger = get_logger("my_test_logger")
        assert logger.name == "my_test_logger"

    def test_get_logger_default_level(self):
        """默认日志级别应该是INFO"""
        logger = get_logger("test_default_level")
        assert logger.level == logging.INFO

    def test_get_logger_custom_level(self):
        """应该能设置自定义日志级别"""
        logger = get_logger("test_debug", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_get_logger_warning_level(self):
        """应该能设置WARNING级别"""
        logger = get_logger("test_warning", level="WARNING")
        assert logger.level == logging.WARNING

    def test_get_logger_error_level(self):
        """应该能设置ERROR级别"""
        logger = get_logger("test_error", level="ERROR")
        assert logger.level == logging.ERROR

    def test_logger_has_handler(self):
        """Logger应该有handler"""
        logger = get_logger("test_handler")
        assert len(logger.handlers) > 0

    def test_logger_handler_is_stream_handler(self):
        """Handler应该是StreamHandler"""
        logger = get_logger("test_stream")
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_logger_handler_has_formatter(self):
        """Handler应该有formatter"""
        logger = get_logger("test_formatter")
        for handler in logger.handlers:
            assert handler.formatter is not None

    def test_logger_can_log_info(self):
        """应该能记录INFO日志（不抛异常）"""
        logger = get_logger("test_info")
        try:
            logger.info("Test info message")
        except Exception as e:
            pytest.fail(f"Logger.info() raised an exception: {e}")

    def test_logger_can_log_debug(self):
        """应该能记录DEBUG日志"""
        logger = get_logger("test_debug_msg", level="DEBUG")
        try:
            logger.debug("Test debug message")
        except Exception as e:
            pytest.fail(f"Logger.debug() raised an exception: {e}")

    def test_logger_can_log_warning(self):
        """应该能记录WARNING日志"""
        logger = get_logger("test_warning_msg")
        try:
            logger.warning("Test warning message")
        except Exception as e:
            pytest.fail(f"Logger.warning() raised an exception: {e}")

    def test_logger_can_log_error(self):
        """应该能记录ERROR日志"""
        logger = get_logger("test_error_msg")
        try:
            logger.error("Test error message")
        except Exception as e:
            pytest.fail(f"Logger.error() raised an exception: {e}")

    def test_get_same_logger_twice(self):
        """多次获取同一logger应该返回同一实例"""
        logger1 = get_logger("test_same")
        logger2 = get_logger("test_same")
        assert logger1 is logger2

    def test_case_insensitive_level(self):
        """日志级别应该不区分大小写"""
        logger = get_logger("test_case", level="debug")
        assert logger.level == logging.DEBUG
