"""
测试Token管理器
"""
import pytest
from aicode.llm.token_manager import TokenManager
from aicode.models.schema import ModelSchema
from aicode.llm.exceptions import TokenError, TokenLimitExceededError


@pytest.fixture
def token_manager():
    """Token管理器fixture"""
    return TokenManager()


@pytest.fixture
def gpt4_token_manager():
    """GPT-4 Token管理器fixture"""
    return TokenManager(model_name="gpt-4")


@pytest.fixture
def sample_model():
    """示例模型fixture"""
    return ModelSchema(
        name="gpt-4",
        provider="openai",
        max_input_tokens=8192,
        context_window=128000
    )


class TestTokenManager:
    """测试TokenManager基本功能"""

    def test_init_default(self):
        """应该能用默认参数初始化"""
        tm = TokenManager()
        assert tm.encoding is not None
        assert tm.encoding_name == TokenManager.DEFAULT_ENCODING

    def test_init_with_model_name(self):
        """应该能用模型名称初始化"""
        tm = TokenManager(model_name="gpt-4")
        assert tm.model_name == "gpt-4"
        assert tm.encoding_name == "cl100k_base"

    def test_init_with_encoding_name(self):
        """应该能手动指定编码器"""
        tm = TokenManager(encoding_name="p50k_base")
        assert tm.encoding_name == "p50k_base"

    def test_init_encoding_priority(self):
        """手动指定的编码器应该优先"""
        tm = TokenManager(model_name="gpt-4", encoding_name="p50k_base")
        assert tm.encoding_name == "p50k_base"

    def test_get_encoding_name_known_model(self):
        """已知模型应该返回正确的编码器"""
        tm = TokenManager()
        encoding = tm._get_encoding_name("gpt-4")
        assert encoding == "cl100k_base"

    def test_get_encoding_name_unknown_model(self):
        """未知模型应该返回默认编码器"""
        tm = TokenManager()
        encoding = tm._get_encoding_name("unknown-model")
        assert encoding == TokenManager.DEFAULT_ENCODING

    def test_get_encoding_name_prefix_match(self):
        """应该支持前缀匹配"""
        tm = TokenManager()
        encoding = tm._get_encoding_name("gpt-4-turbo-preview")
        assert encoding == "cl100k_base"


class TestCountTokens:
    """测试token计数"""

    def test_count_empty_text(self, token_manager):
        """空文本应该返回0"""
        count = token_manager.count_tokens("")
        assert count == 0

    def test_count_simple_text(self, token_manager):
        """应该能计数简单文本"""
        text = "Hello, world!"
        count = token_manager.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_count_chinese_text(self, token_manager):
        """应该能计数中文文本"""
        text = "你好，世界！"
        count = token_manager.count_tokens(text)
        assert count > 0

    def test_count_code(self, token_manager):
        """应该能计数代码"""
        code = """
def hello():
    print("Hello, world!")
"""
        count = token_manager.count_tokens(code)
        assert count > 0

    def test_count_long_text(self, token_manager):
        """应该能计数长文本"""
        text = "test " * 1000
        count = token_manager.count_tokens(text)
        assert count > 1000


class TestCheckLimit:
    """测试token限制检查"""

    def test_check_limit_within(self, token_manager, sample_model):
        """未超过限制应该返回True"""
        text = "Hello, world!"
        result = token_manager.check_limit(text, sample_model)
        assert result is True

    def test_check_limit_exceeded(self, token_manager):
        """超过限制应该抛出异常"""
        # 创建一个小限制的模型
        model = ModelSchema(
            name="test",
            provider="test",
            max_input_tokens=10
        )
        text = "This is a very long text " * 100
        with pytest.raises(TokenLimitExceededError):
            token_manager.check_limit(text, model)

    def test_check_limit_no_limit(self, token_manager):
        """没有限制的模型应该返回True"""
        model = ModelSchema(name="test", provider="test")
        text = "Any text" * 1000
        result = token_manager.check_limit(text, model)
        assert result is True


class TestTruncateText:
    """测试文本截断"""

    def test_truncate_empty_text(self, token_manager):
        """空文本应该返回空"""
        result = token_manager.truncate_text("", 100)
        assert result == ""

    def test_truncate_within_limit(self, token_manager):
        """未超过限制的文本应该原样返回"""
        text = "Hello, world!"
        result = token_manager.truncate_text(text, 100)
        assert result == text

    def test_truncate_exceed_limit(self, token_manager):
        """超过限制应该截断"""
        text = "Hello, world! " * 100
        result = token_manager.truncate_text(text, 10)
        assert len(result) < len(text)
        token_count = token_manager.count_tokens(result)
        assert token_count <= 10

    def test_truncate_zero_tokens(self, token_manager):
        """max_tokens为0应该返回空"""
        text = "Hello, world!"
        result = token_manager.truncate_text(text, 0)
        assert result == ""

    def test_truncate_preserves_encoding(self, token_manager):
        """截断后的文本应该能正确解码"""
        text = "你好，世界！" * 50
        result = token_manager.truncate_text(text, 20)
        # 不应该包含乱码
        assert result  # 应该有内容


class TestEstimateCost:
    """测试成本估算"""

    def test_estimate_cost_input_only(self, token_manager):
        """应该能估算仅输入的成本"""
        model = ModelSchema(
            name="gpt-4",
            provider="openai",
            cost_per_1k_input=0.03
        )
        text = "Hello, world!"
        cost = token_manager.estimate_cost(text, model)
        assert cost is not None
        assert cost > 0

    def test_estimate_cost_with_output(self, token_manager):
        """应该能估算包含输出的成本"""
        model = ModelSchema(
            name="gpt-4",
            provider="openai",
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06
        )
        text = "Hello, world!"
        cost = token_manager.estimate_cost(text, model, output_tokens=100)
        assert cost is not None
        assert cost > 0

    def test_estimate_cost_no_pricing(self, token_manager):
        """没有价格信息应该返回None"""
        model = ModelSchema(name="test", provider="test")
        text = "Hello, world!"
        cost = token_manager.estimate_cost(text, model)
        assert cost is None

    def test_estimate_cost_calculation(self, token_manager):
        """成本计算应该正确"""
        model = ModelSchema(
            name="test",
            provider="test",
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.02
        )
        # 假设输入是10个token，输出是20个token
        text = "test"  # 实际token数可能不同，只是测试逻辑
        cost = token_manager.estimate_cost(text, model, output_tokens=1000)
        # 输出成本应该是 (1000/1000) * 0.02 = 0.02
        assert cost > 0.02  # 加上输入成本


class TestGetRemainingTokens:
    """测试剩余token计算"""

    def test_get_remaining_tokens(self, token_manager, sample_model):
        """应该能计算剩余token"""
        text = "Hello, world!"
        remaining = token_manager.get_remaining_tokens(text, sample_model)
        assert remaining is not None
        assert remaining > 0

    def test_get_remaining_tokens_no_limit(self, token_manager):
        """没有限制的模型应该返回None"""
        model = ModelSchema(name="test", provider="test")
        text = "Hello, world!"
        remaining = token_manager.get_remaining_tokens(text, model)
        assert remaining is None

    def test_get_remaining_tokens_nearly_full(self, token_manager):
        """接近限制应该返回较小的值"""
        model = ModelSchema(
            name="test",
            provider="test",
            max_input_tokens=100
        )
        text = "word " * 50  # 接近限制
        remaining = token_manager.get_remaining_tokens(text, model)
        assert remaining is not None
        assert remaining >= 0

    def test_get_remaining_tokens_negative(self, token_manager):
        """超过限制应该返回0（不是负数）"""
        model = ModelSchema(
            name="test",
            provider="test",
            max_input_tokens=10
        )
        text = "word " * 100
        remaining = token_manager.get_remaining_tokens(text, model)
        assert remaining == 0
