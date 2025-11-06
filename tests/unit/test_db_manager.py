"""
测试数据库管理器
"""
import pytest
import tempfile
import os
from aicode.database.db_manager import DatabaseManager
from aicode.models.schema import ModelSchema
from aicode.llm.exceptions import (
    DatabaseError,
    ModelNotFoundError,
    ModelAlreadyExistsError
)


@pytest.fixture
def temp_db():
    """临时数据库fixture"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db_manager(temp_db):
    """数据库管理器fixture"""
    return DatabaseManager(temp_db)


@pytest.fixture
def sample_model():
    """示例模型fixture"""
    return ModelSchema(
        name="gpt-4",
        provider="openai",
        max_input_tokens=8192,
        code_score=9.0
    )


class TestDatabaseManager:
    """测试DatabaseManager基本功能"""

    def test_init_creates_database(self, temp_db):
        """初始化应该创建数据库文件"""
        db = DatabaseManager(temp_db)
        assert os.path.exists(temp_db)

    def test_init_creates_tables(self, db_manager):
        """初始化应该创建表"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='models'"
            )
            assert cursor.fetchone() is not None

    def test_insert_model(self, db_manager, sample_model):
        """应该能插入模型"""
        db_manager.insert_model(sample_model)
        assert db_manager.model_exists("gpt-4")

    def test_insert_duplicate_model(self, db_manager, sample_model):
        """插入重复模型应该报错"""
        db_manager.insert_model(sample_model)
        with pytest.raises(ModelAlreadyExistsError):
            db_manager.insert_model(sample_model)

    def test_get_model(self, db_manager, sample_model):
        """应该能获取模型"""
        db_manager.insert_model(sample_model)
        retrieved = db_manager.get_model("gpt-4")
        assert retrieved.name == "gpt-4"
        assert retrieved.provider == "openai"
        assert retrieved.max_input_tokens == 8192

    def test_get_nonexistent_model(self, db_manager):
        """获取不存在的模型应该报错"""
        with pytest.raises(ModelNotFoundError):
            db_manager.get_model("nonexistent")

    def test_update_model(self, db_manager, sample_model):
        """应该能更新模型"""
        db_manager.insert_model(sample_model)
        db_manager.update_model("gpt-4", {"code_score": 9.5})
        updated = db_manager.get_model("gpt-4")
        assert updated.code_score == 9.5

    def test_update_nonexistent_model(self, db_manager):
        """更新不存在的模型应该报错"""
        with pytest.raises(ModelNotFoundError):
            db_manager.update_model("nonexistent", {"code_score": 9.0})

    def test_delete_model(self, db_manager, sample_model):
        """应该能删除模型"""
        db_manager.insert_model(sample_model)
        db_manager.delete_model("gpt-4")
        assert not db_manager.model_exists("gpt-4")

    def test_delete_nonexistent_model(self, db_manager):
        """删除不存在的模型应该报错"""
        with pytest.raises(ModelNotFoundError):
            db_manager.delete_model("nonexistent")

    def test_model_exists(self, db_manager, sample_model):
        """model_exists应该正确返回"""
        assert not db_manager.model_exists("gpt-4")
        db_manager.insert_model(sample_model)
        assert db_manager.model_exists("gpt-4")

    def test_list_models_empty(self, db_manager):
        """列出空数据库应该返回空列表"""
        models = db_manager.list_models()
        assert models == []

    def test_list_models(self, db_manager):
        """应该能列出所有模型"""
        model1 = ModelSchema(name="gpt-4", provider="openai")
        model2 = ModelSchema(name="claude-3", provider="anthropic")
        db_manager.insert_model(model1)
        db_manager.insert_model(model2)

        models = db_manager.list_models()
        assert len(models) == 2
        names = [m.name for m in models]
        assert "gpt-4" in names
        assert "claude-3" in names

    def test_count_models(self, db_manager):
        """应该能统计模型数量"""
        assert db_manager.count_models() == 0

        model1 = ModelSchema(name="gpt-4", provider="openai")
        model2 = ModelSchema(name="claude-3", provider="anthropic")
        db_manager.insert_model(model1)
        db_manager.insert_model(model2)

        assert db_manager.count_models() == 2


class TestQueryModels:
    """测试模型查询功能"""

    def test_query_all_models(self, db_manager):
        """无筛选条件应该返回所有模型"""
        model1 = ModelSchema(name="gpt-4", provider="openai")
        model2 = ModelSchema(name="claude-3", provider="anthropic")
        db_manager.insert_model(model1)
        db_manager.insert_model(model2)

        models = db_manager.query_models()
        assert len(models) == 2

    def test_query_by_provider(self, db_manager):
        """应该能按提供商筛选"""
        model1 = ModelSchema(name="gpt-4", provider="openai")
        model2 = ModelSchema(name="claude-3", provider="anthropic")
        db_manager.insert_model(model1)
        db_manager.insert_model(model2)

        models = db_manager.query_models({"provider": "openai"})
        assert len(models) == 1
        assert models[0].name == "gpt-4"

    def test_query_by_min_code_score(self, db_manager):
        """应该能按最小评分筛选"""
        model1 = ModelSchema(name="gpt-4", provider="openai", code_score=9.0)
        model2 = ModelSchema(name="gpt-3.5", provider="openai", code_score=7.0)
        db_manager.insert_model(model1)
        db_manager.insert_model(model2)

        models = db_manager.query_models({"min_code_score": 8.0})
        assert len(models) == 1
        assert models[0].name == "gpt-4"

    def test_query_by_specialty(self, db_manager):
        """应该能按专长筛选"""
        model1 = ModelSchema(
            name="gpt-4",
            provider="openai",
            specialties=["code", "reasoning"]
        )
        model2 = ModelSchema(
            name="gpt-3.5",
            provider="openai",
            specialties=["chat"]
        )
        db_manager.insert_model(model1)
        db_manager.insert_model(model2)

        models = db_manager.query_models({"specialty": "code"})
        assert len(models) == 1
        assert models[0].name == "gpt-4"


class TestBatchOperations:
    """测试批量操作"""

    def test_import_batch(self, db_manager):
        """应该能批量导入模型"""
        models = [
            {"name": "gpt-4", "provider": "openai"},
            {"name": "claude-3", "provider": "anthropic"}
        ]
        stats = db_manager.import_batch(models)
        assert stats['imported'] == 2
        assert stats['skipped'] == 0
        assert stats['errors'] == 0

    def test_import_batch_with_duplicates(self, db_manager):
        """批量导入重复模型应该跳过"""
        model1 = ModelSchema(name="gpt-4", provider="openai")
        db_manager.insert_model(model1)

        models = [
            {"name": "gpt-4", "provider": "openai"},
            {"name": "claude-3", "provider": "anthropic"}
        ]
        stats = db_manager.import_batch(models)
        assert stats['imported'] == 1
        assert stats['skipped'] == 1

    def test_import_batch_with_errors(self, db_manager):
        """批量导入包含错误数据应该统计错误"""
        models = [
            {"name": "gpt-4", "provider": "openai"},
            {"provider": "anthropic"},  # 缺少name
        ]
        stats = db_manager.import_batch(models)
        assert stats['imported'] == 1
        assert stats['errors'] == 1

    def test_export_all(self, db_manager):
        """应该能导出所有模型"""
        model1 = ModelSchema(name="gpt-4", provider="openai")
        model2 = ModelSchema(name="claude-3", provider="anthropic")
        db_manager.insert_model(model1)
        db_manager.insert_model(model2)

        exported = db_manager.export_all()
        assert len(exported) == 2
        assert all(isinstance(m, dict) for m in exported)
