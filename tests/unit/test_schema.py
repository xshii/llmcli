"""
测试数据模型
"""
import pytest
from aicode.models.schema import (
    ModelSchema,
    CREATE_MODELS_TABLE,
    row_to_model,
    import_model_from_preconfig
)


class TestModelSchema:
    """测试 ModelSchema 数据类"""

    def test_create_minimal_model(self):
        """创建最小模型（仅必需字段）"""
        model = ModelSchema(name="gpt-4", provider="openai")
        assert model.name == "gpt-4"
        assert model.provider == "openai"
        assert model.api_key is None

    def test_create_full_model(self):
        """创建完整模型"""
        model = ModelSchema(
            name="gpt-4",
            provider="openai",
            api_key="sk-test",
            api_url="https://api.openai.com/v1",
            max_input_tokens=8192,
            max_output_tokens=4096,
            context_window=128000,
            code_score=9.0,
            reasoning_score=9.5,
            speed_score=7.0,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            specialties=["code", "reasoning"],
            notes="Best for complex tasks"
        )
        assert model.name == "gpt-4"
        assert model.max_input_tokens == 8192
        assert model.code_score == 9.0
        assert model.specialties == ["code", "reasoning"]

    def test_to_dict(self):
        """测试转换为字典"""
        model = ModelSchema(
            name="claude-3",
            provider="anthropic",
            specialties=["code", "reasoning"]
        )
        data = model.to_dict()
        assert isinstance(data, dict)
        assert data['name'] == "claude-3"
        assert data['specialties'] == "code,reasoning"  # 转为字符串

    def test_to_dict_no_specialties(self):
        """测试无专长时转换为字典"""
        model = ModelSchema(name="test", provider="test")
        data = model.to_dict()
        assert data['specialties'] is None

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'name': 'gpt-4',
            'provider': 'openai',
            'max_input_tokens': 8192,
            'specialties': 'code,reasoning'
        }
        model = ModelSchema.from_dict(data)
        assert model.name == "gpt-4"
        assert model.max_input_tokens == 8192
        assert model.specialties == ["code", "reasoning"]

    def test_from_dict_with_list_specialties(self):
        """测试从字典创建（专长已是列表）"""
        data = {
            'name': 'test',
            'provider': 'test',
            'specialties': ['code', 'chat']
        }
        model = ModelSchema.from_dict(data)
        assert model.specialties == ['code', 'chat']

    def test_get_context_limit_with_context_window(self):
        """测试获取上下文限制（优先使用context_window）"""
        model = ModelSchema(
            name="test",
            provider="test",
            context_window=100000,
            max_input_tokens=8192
        )
        limit = model.get_context_limit()
        assert limit == int(100000 * 0.9)  # 使用缓冲比例

    def test_get_context_limit_with_max_input(self):
        """测试获取上下文限制（使用max_input_tokens）"""
        model = ModelSchema(
            name="test",
            provider="test",
            max_input_tokens=8192
        )
        limit = model.get_context_limit()
        assert limit == int(8192 * 0.9)

    def test_get_context_limit_none(self):
        """测试获取上下文限制（无数据）"""
        model = ModelSchema(name="test", provider="test")
        limit = model.get_context_limit()
        assert limit is None

    def test_validate_scores_valid(self):
        """测试验证有效评分"""
        model = ModelSchema(
            name="test",
            provider="test",
            code_score=9.0,
            reasoning_score=8.5,
            speed_score=7.0
        )
        assert model.validate_scores() is True

    def test_validate_scores_invalid(self):
        """测试验证无效评分"""
        model = ModelSchema(
            name="test",
            provider="test",
            code_score=11.0  # 超出范围
        )
        assert model.validate_scores() is False

    def test_validate_scores_with_none(self):
        """测试验证评分（包含None）"""
        model = ModelSchema(
            name="test",
            provider="test",
            code_score=9.0,
            reasoning_score=None
        )
        assert model.validate_scores() is True


class TestCreateModelsTable:
    """测试数据库表结构"""

    def test_create_table_sql_exists(self):
        """CREATE TABLE SQL应该存在"""
        assert CREATE_MODELS_TABLE is not None
        assert isinstance(CREATE_MODELS_TABLE, str)
        assert "CREATE TABLE" in CREATE_MODELS_TABLE

    def test_table_has_primary_key(self):
        """表应该有主键"""
        assert "PRIMARY KEY" in CREATE_MODELS_TABLE

    def test_table_has_required_fields(self):
        """表应该包含必需字段"""
        assert "name" in CREATE_MODELS_TABLE
        assert "provider" in CREATE_MODELS_TABLE


class TestRowToModel:
    """测试行转换函数"""

    def test_row_to_model_from_dict(self):
        """测试从字典转换"""
        row = {
            'name': 'gpt-4',
            'provider': 'openai',
            'max_input_tokens': 8192,
            'specialties': 'code,reasoning',
            'created_at': '2024-01-01',
            'updated_at': '2024-01-02'
        }
        model = row_to_model(row)
        assert isinstance(model, ModelSchema)
        assert model.name == 'gpt-4'
        assert model.specialties == ['code', 'reasoning']

    def test_row_to_model_invalid_type(self):
        """测试不支持的行类型"""
        with pytest.raises(ValueError):
            row_to_model(("gpt-4", "openai"))


class TestImportModelFromPreconfig:
    """测试从预配置导入"""

    def test_import_minimal_config(self):
        """导入最小配置"""
        config = {
            'name': 'gpt-4',
            'provider': 'openai'
        }
        model = import_model_from_preconfig(config)
        assert model.name == 'gpt-4'
        assert model.provider == 'openai'

    def test_import_full_config(self):
        """导入完整配置"""
        config = {
            'name': 'claude-3',
            'provider': 'anthropic',
            'max_input_tokens': 200000,
            'code_score': 9.5,
            'specialties': ['code', 'reasoning']
        }
        model = import_model_from_preconfig(config)
        assert model.name == 'claude-3'
        assert model.max_input_tokens == 200000
        assert model.specialties == ['code', 'reasoning']

    def test_import_missing_name(self):
        """导入缺少name应该报错"""
        config = {'provider': 'openai'}
        with pytest.raises(ValueError, match="name and provider are required"):
            import_model_from_preconfig(config)

    def test_import_missing_provider(self):
        """导入缺少provider应该报错"""
        config = {'name': 'gpt-4'}
        with pytest.raises(ValueError, match="name and provider are required"):
            import_model_from_preconfig(config)

    def test_import_empty_name(self):
        """导入空name应该报错"""
        config = {'name': '', 'provider': 'openai'}
        with pytest.raises(ValueError):
            import_model_from_preconfig(config)
