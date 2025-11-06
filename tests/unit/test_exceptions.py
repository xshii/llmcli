"""
测试异常体系
"""
import pytest
from aicode.llm.exceptions import (
    AICodeError,
    DatabaseError,
    ModelNotFoundError,
    ModelAlreadyExistsError,
    ConfigError,
    ConfigFileNotFoundError,
    InvalidConfigError,
    ValidationError,
    TokenError,
    TokenLimitExceededError,
    APIError,
    APIConnectionError,
    APITimeoutError,
    InvalidAPIKeyError,
)


class TestExceptionHierarchy:
    """测试异常继承关系"""

    def test_base_exception(self):
        """AICodeError应该继承自Exception"""
        assert issubclass(AICodeError, Exception)

    def test_database_error_hierarchy(self):
        """数据库异常应该继承自AICodeError"""
        assert issubclass(DatabaseError, AICodeError)
        assert issubclass(ModelNotFoundError, DatabaseError)
        assert issubclass(ModelAlreadyExistsError, DatabaseError)

    def test_config_error_hierarchy(self):
        """配置异常应该继承自AICodeError"""
        assert issubclass(ConfigError, AICodeError)
        assert issubclass(ConfigFileNotFoundError, ConfigError)
        assert issubclass(InvalidConfigError, ConfigError)

    def test_validation_error_hierarchy(self):
        """验证异常应该继承自AICodeError"""
        assert issubclass(ValidationError, AICodeError)

    def test_token_error_hierarchy(self):
        """Token异常应该继承自AICodeError"""
        assert issubclass(TokenError, AICodeError)
        assert issubclass(TokenLimitExceededError, TokenError)

    def test_api_error_hierarchy(self):
        """API异常应该继承自AICodeError"""
        assert issubclass(APIError, AICodeError)
        assert issubclass(APIConnectionError, APIError)
        assert issubclass(APITimeoutError, APIError)
        assert issubclass(InvalidAPIKeyError, APIError)


class TestExceptionRaising:
    """测试异常抛出和捕获"""

    def test_raise_base_exception(self):
        """应该能抛出基础异常"""
        with pytest.raises(AICodeError):
            raise AICodeError("test error")

    def test_raise_database_error(self):
        """应该能抛出数据库异常"""
        with pytest.raises(DatabaseError):
            raise DatabaseError("db error")

    def test_raise_model_not_found(self):
        """应该能抛出模型未找到异常"""
        with pytest.raises(ModelNotFoundError):
            raise ModelNotFoundError("model not found")

    def test_raise_model_already_exists(self):
        """应该能抛出模型已存在异常"""
        with pytest.raises(ModelAlreadyExistsError):
            raise ModelAlreadyExistsError("model exists")

    def test_raise_config_error(self):
        """应该能抛出配置错误"""
        with pytest.raises(ConfigError):
            raise ConfigError("config error")

    def test_raise_validation_error(self):
        """应该能抛出验证错误"""
        with pytest.raises(ValidationError):
            raise ValidationError("validation failed")

    def test_raise_token_error(self):
        """应该能抛出Token错误"""
        with pytest.raises(TokenError):
            raise TokenError("token error")

    def test_raise_token_limit_exceeded(self):
        """应该能抛出Token超限异常"""
        with pytest.raises(TokenLimitExceededError):
            raise TokenLimitExceededError("token limit exceeded")

    def test_raise_api_error(self):
        """应该能抛出API错误"""
        with pytest.raises(APIError):
            raise APIError("api error")

    def test_raise_api_connection_error(self):
        """应该能抛出API连接错误"""
        with pytest.raises(APIConnectionError):
            raise APIConnectionError("connection failed")

    def test_raise_api_timeout_error(self):
        """应该能抛出API超时错误"""
        with pytest.raises(APITimeoutError):
            raise APITimeoutError("timeout")

    def test_raise_invalid_api_key(self):
        """应该能抛出无效API密钥错误"""
        with pytest.raises(InvalidAPIKeyError):
            raise InvalidAPIKeyError("invalid key")


class TestExceptionCatching:
    """测试异常捕获"""

    def test_catch_child_as_parent(self):
        """应该能用父类捕获子类异常"""
        with pytest.raises(DatabaseError):
            raise ModelNotFoundError("not found")

    def test_catch_child_as_base(self):
        """应该能用基类捕获所有子类异常"""
        with pytest.raises(AICodeError):
            raise TokenLimitExceededError("limit exceeded")

    def test_exception_message(self):
        """异常应该能携带消息"""
        msg = "test error message"
        with pytest.raises(AICodeError) as exc_info:
            raise AICodeError(msg)
        assert str(exc_info.value) == msg

    def test_catch_specific_database_error(self):
        """应该能捕获特定的数据库异常"""
        try:
            raise ModelNotFoundError("model not found")
        except ModelNotFoundError as e:
            assert "model not found" in str(e)
        except DatabaseError:
            pytest.fail("Should catch ModelNotFoundError, not DatabaseError")

    def test_catch_specific_api_error(self):
        """应该能捕获特定的API异常"""
        try:
            raise APITimeoutError("timeout")
        except APITimeoutError as e:
            assert "timeout" in str(e)
        except APIError:
            pytest.fail("Should catch APITimeoutError, not APIError")
