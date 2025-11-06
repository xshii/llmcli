"""
异常体系定义
"""


class AICodeError(Exception):
    """基础异常类"""
    pass


# 数据库相关异常
class DatabaseError(AICodeError):
    """数据库操作异常"""
    pass


class ModelNotFoundError(DatabaseError):
    """模型未找到"""
    pass


class ModelAlreadyExistsError(DatabaseError):
    """模型已存在"""
    pass


# 配置相关异常
class ConfigError(AICodeError):
    """配置错误"""
    pass


class ConfigFileNotFoundError(ConfigError):
    """配置文件未找到"""
    pass


class InvalidConfigError(ConfigError):
    """无效的配置"""
    pass


# 验证相关异常
class ValidationError(AICodeError):
    """数据验证错误"""
    pass


# Token相关异常
class TokenError(AICodeError):
    """Token处理错误"""
    pass


class TokenLimitExceededError(TokenError):
    """Token超出限制"""
    pass


# API相关异常
class APIError(AICodeError):
    """API调用错误"""
    pass


class APIConnectionError(APIError):
    """API连接失败"""
    pass


class APITimeoutError(APIError):
    """API超时"""
    pass


class InvalidAPIKeyError(APIError):
    """无效的API密钥"""
    pass
