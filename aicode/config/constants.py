"""
全局常量配置
"""

# 版本信息
VERSION = "0.1.0"
PROJECT_NAME = "aicode"

# 配置文件
DEFAULT_CONFIG_DIR = "~/.aicode"
DEFAULT_CONFIG_FILE = "config.yaml"

# 数据库配置
DEFAULT_DB_NAME = "aicode.db"
DEFAULT_DB_PATH = "~/.aicode/aicode.db"

# Token相关
DEFAULT_MAX_TOKENS = 4096
TOKEN_BUFFER_RATIO = 0.9  # 安全缓冲：使用最大值的90%

# API配置
DEFAULT_API_URL = "https://api.openai.com/v1"
DEFAULT_TIMEOUT = 30  # 秒

# 日志配置
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = "INFO"

# 模型评分范围
MIN_SCORE = 0.0
MAX_SCORE = 10.0

# 模型专长类型
SPECIALTIES = ["code", "reasoning", "chat", "vision", "multilingual"]
