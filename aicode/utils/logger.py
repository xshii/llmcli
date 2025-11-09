"""
简单的日志系统
"""

import logging
from typing import Optional

from aicode.config.constants import DEFAULT_LOG_LEVEL, LOG_DATE_FORMAT, LOG_FORMAT


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    获取logger实例

    Args:
        name: logger名称，通常使用 __name__
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)

    # 如果已经有handler，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = level or DEFAULT_LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))

    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # 设置格式
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    console_handler.setFormatter(formatter)

    # 添加handler
    logger.addHandler(console_handler)

    return logger
