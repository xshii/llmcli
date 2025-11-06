"""
测试数据验证工具
"""
import pytest
from aicode.utils.validators import (
    validate_model_name,
    validate_provider,
    validate_token_count,
    validate_score,
    validate_cost,
    validate_specialties,
    validate_url,
    validate_string,
    validate_model_data
)
from aicode.llm.exceptions import ValidationError


class TestValidateModelName:
    """测试模型名称验证"""

    def test_valid_name(self):
        """有效的模型名称"""
        assert validate_model_name("gpt-4") == "gpt-4"

    def test_name_with_spaces(self):
        """名称包含空格应该被trim"""
        assert validate_model_name("  gpt-4  ") == "gpt-4"

    def test_empty_name(self):
        """空名称应该报错"""
        with pytest.raises(ValidationError, match="required"):
            validate_model_name("")

    def test_none_name(self):
        """None名称应该报错"""
        with pytest.raises(ValidationError, match="required"):
            validate_model_name(None)

    def test_non_string_name(self):
        """非字符串名称应该报错"""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_model_name(123)

    def test_too_long_name(self):
        """过长名称应该报错"""
        with pytest.raises(ValidationError, match="too long"):
            validate_model_name("a" * 256)


class TestValidateProvider:
    """测试提供商验证"""

    def test_valid_provider(self):
        """有效的提供商"""
        assert validate_provider("openai") == "openai"

    def test_provider_with_spaces(self):
        """提供商名称包含空格应该被trim"""
        assert validate_provider("  anthropic  ") == "anthropic"

    def test_empty_provider(self):
        """空提供商应该报错"""
        with pytest.raises(ValidationError, match="required"):
            validate_provider("")

    def test_none_provider(self):
        """None提供商应该报错"""
        with pytest.raises(ValidationError, match="required"):
            validate_provider(None)

    def test_non_string_provider(self):
        """非字符串提供商应该报错"""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_provider(123)


class TestValidateTokenCount:
    """测试Token数量验证"""

    def test_valid_token_count(self):
        """有效的token数量"""
        assert validate_token_count(8192, "test") == 8192

    def test_none_token_count(self):
        """None应该返回None"""
        assert validate_token_count(None, "test") is None

    def test_zero_token_count(self):
        """零应该报错"""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_token_count(0, "test")

    def test_negative_token_count(self):
        """负数应该报错"""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_token_count(-100, "test")

    def test_non_integer_token_count(self):
        """非整数应该报错"""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_token_count(8192.5, "test")

    def test_too_large_token_count(self):
        """过大的数值应该报错"""
        with pytest.raises(ValidationError, match="too large"):
            validate_token_count(20_000_000, "test")


class TestValidateScore:
    """测试评分验证"""

    def test_valid_score_int(self):
        """有效的整数评分"""
        assert validate_score(9, "test") == 9.0

    def test_valid_score_float(self):
        """有效的浮点数评分"""
        assert validate_score(8.5, "test") == 8.5

    def test_none_score(self):
        """None应该返回None"""
        assert validate_score(None, "test") is None

    def test_min_score(self):
        """最小评分"""
        assert validate_score(0.0, "test") == 0.0

    def test_max_score(self):
        """最大评分"""
        assert validate_score(10.0, "test") == 10.0

    def test_score_too_low(self):
        """评分过低应该报错"""
        with pytest.raises(ValidationError, match="must be between"):
            validate_score(-1, "test")

    def test_score_too_high(self):
        """评分过高应该报错"""
        with pytest.raises(ValidationError, match="must be between"):
            validate_score(11, "test")

    def test_non_numeric_score(self):
        """非数字评分应该报错"""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_score("high", "test")


class TestValidateCost:
    """测试成本验证"""

    def test_valid_cost(self):
        """有效的成本"""
        assert validate_cost(0.03, "test") == 0.03

    def test_none_cost(self):
        """None应该返回None"""
        assert validate_cost(None, "test") is None

    def test_zero_cost(self):
        """零成本应该有效"""
        assert validate_cost(0, "test") == 0.0

    def test_negative_cost(self):
        """负成本应该报错"""
        with pytest.raises(ValidationError, match="cannot be negative"):
            validate_cost(-0.01, "test")

    def test_too_large_cost(self):
        """过大成本应该报错"""
        with pytest.raises(ValidationError, match="too large"):
            validate_cost(1001, "test")

    def test_non_numeric_cost(self):
        """非数字成本应该报错"""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_cost("expensive", "test")


class TestValidateSpecialties:
    """测试专长验证"""

    def test_valid_specialties_list(self):
        """有效的专长列表"""
        result = validate_specialties(["code", "reasoning"])
        assert result == ["code", "reasoning"]

    def test_valid_specialties_string(self):
        """有效的专长字符串"""
        result = validate_specialties("code,reasoning,chat")
        assert result == ["code", "reasoning", "chat"]

    def test_none_specialties(self):
        """None应该返回None"""
        assert validate_specialties(None) is None

    def test_empty_list(self):
        """空列表应该返回None"""
        assert validate_specialties([]) is None

    def test_specialties_with_spaces(self):
        """带空格的专长应该被trim"""
        result = validate_specialties("  code  , reasoning ")
        assert result == ["code", "reasoning"]

    def test_invalid_specialty(self):
        """无效的专长应该报错"""
        with pytest.raises(ValidationError, match="Invalid specialty"):
            validate_specialties(["invalid_specialty"])

    def test_case_insensitive(self):
        """专长应该不区分大小写"""
        result = validate_specialties(["CODE", "Reasoning"])
        assert result == ["code", "reasoning"]

    def test_duplicate_specialties(self):
        """重复的专长应该去重"""
        result = validate_specialties(["code", "code", "reasoning"])
        assert result == ["code", "reasoning"]

    def test_non_string_specialty(self):
        """非字符串专长应该报错"""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_specialties([123])

    def test_non_list_non_string(self):
        """非列表非字符串应该报错"""
        with pytest.raises(ValidationError, match="must be a list"):
            validate_specialties(123)


class TestValidateUrl:
    """测试URL验证"""

    def test_valid_https_url(self):
        """有效的HTTPS URL"""
        url = "https://api.openai.com/v1"
        assert validate_url(url, "test") == url

    def test_valid_http_url(self):
        """有效的HTTP URL"""
        url = "http://localhost:8080"
        assert validate_url(url, "test") == url

    def test_none_url(self):
        """None应该返回None"""
        assert validate_url(None, "test") is None

    def test_empty_url(self):
        """空URL应该返回None"""
        assert validate_url("", "test") is None

    def test_url_with_spaces(self):
        """URL包含空格应该被trim"""
        url = "  https://api.example.com  "
        assert validate_url(url, "test") == "https://api.example.com"

    def test_invalid_protocol(self):
        """无效协议应该报错"""
        with pytest.raises(ValidationError, match="must start with http"):
            validate_url("ftp://example.com", "test")

    def test_no_protocol(self):
        """无协议应该报错"""
        with pytest.raises(ValidationError, match="must start with http"):
            validate_url("api.openai.com", "test")

    def test_too_long_url(self):
        """过长URL应该报错"""
        with pytest.raises(ValidationError, match="too long"):
            validate_url("https://" + "a" * 2048, "test")

    def test_non_string_url(self):
        """非字符串URL应该报错"""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_url(123, "test")


class TestValidateString:
    """测试字符串验证"""

    def test_valid_string(self):
        """有效的字符串"""
        assert validate_string("test value", "test") == "test value"

    def test_none_string(self):
        """None应该返回None"""
        assert validate_string(None, "test") is None

    def test_empty_string(self):
        """空字符串应该返回None"""
        assert validate_string("", "test") is None

    def test_string_with_spaces(self):
        """字符串包含空格应该被trim"""
        assert validate_string("  test  ", "test") == "test"

    def test_whitespace_only(self):
        """仅空格应该返回None"""
        assert validate_string("   ", "test") is None

    def test_too_long_string(self):
        """过长字符串应该报错"""
        with pytest.raises(ValidationError, match="too long"):
            validate_string("a" * 1001, "test", 1000)

    def test_custom_max_length(self):
        """自定义最大长度"""
        validate_string("a" * 50, "test", 50)
        with pytest.raises(ValidationError):
            validate_string("a" * 51, "test", 50)

    def test_non_string(self):
        """非字符串应该报错"""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_string(123, "test")


class TestValidateModelData:
    """测试完整模型数据验证"""

    def test_valid_minimal_data(self):
        """有效的最小数据"""
        data = {
            'name': 'gpt-4',
            'provider': 'openai'
        }
        validated = validate_model_data(data)
        assert validated['name'] == 'gpt-4'
        assert validated['provider'] == 'openai'

    def test_valid_full_data(self):
        """有效的完整数据"""
        data = {
            'name': 'claude-3',
            'provider': 'anthropic',
            'api_key': 'sk-test',
            'api_url': 'https://api.anthropic.com',
            'max_input_tokens': 200000,
            'max_output_tokens': 4096,
            'context_window': 200000,
            'code_score': 9.5,
            'reasoning_score': 9.0,
            'speed_score': 8.0,
            'cost_per_1k_input': 0.015,
            'cost_per_1k_output': 0.075,
            'specialties': ['code', 'reasoning'],
            'notes': 'Excellent for coding'
        }
        validated = validate_model_data(data)
        assert validated['name'] == 'claude-3'
        assert validated['max_input_tokens'] == 200000
        assert validated['code_score'] == 9.5
        assert validated['specialties'] == ['code', 'reasoning']

    def test_missing_name(self):
        """缺少name应该报错"""
        data = {'provider': 'openai'}
        with pytest.raises(ValidationError, match="name"):
            validate_model_data(data)

    def test_missing_provider(self):
        """缺少provider应该报错"""
        data = {'name': 'gpt-4'}
        with pytest.raises(ValidationError, match="Provider"):
            validate_model_data(data)

    def test_invalid_score_in_data(self):
        """数据中包含无效评分应该报错"""
        data = {
            'name': 'test',
            'provider': 'test',
            'code_score': 11.0
        }
        with pytest.raises(ValidationError, match="must be between"):
            validate_model_data(data)

    def test_invalid_token_count_in_data(self):
        """数据中包含无效token数量应该报错"""
        data = {
            'name': 'test',
            'provider': 'test',
            'max_input_tokens': -100
        }
        with pytest.raises(ValidationError, match="must be positive"):
            validate_model_data(data)

    def test_validate_trims_whitespace(self):
        """验证应该去除空格"""
        data = {
            'name': '  gpt-4  ',
            'provider': '  openai  '
        }
        validated = validate_model_data(data)
        assert validated['name'] == 'gpt-4'
        assert validated['provider'] == 'openai'

    def test_validate_converts_specialty_string(self):
        """验证应该转换专长字符串为列表"""
        data = {
            'name': 'test',
            'provider': 'test',
            'specialties': 'code,reasoning'
        }
        validated = validate_model_data(data)
        assert validated['specialties'] == ['code', 'reasoning']
