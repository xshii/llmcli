"""
Ollama 集成测试

注意：这些测试需要 Ollama 服务运行才能执行
如果 Ollama 未运行，测试将被跳过
"""

import pytest

from aicode.config.constants import DEFAULT_DB_PATH
from aicode.database.db_manager import DatabaseManager
from aicode.llm import ollama_utils
from aicode.llm.client import LLMClient
from aicode.models.schema import ModelSchema


# 检查 Ollama 是否可用
def is_ollama_running():
    """检查 Ollama 是否运行"""
    return ollama_utils.is_ollama_available()


# 如果 Ollama 未运行，跳过所有测试
pytestmark = pytest.mark.skipif(
    not is_ollama_running(), reason="Ollama is not running"
)


class TestOllamaService:
    """测试 Ollama 服务基本功能"""

    def test_ollama_is_available(self):
        """测试 Ollama 服务可用"""
        assert ollama_utils.is_ollama_available() is True

    def test_list_local_models(self):
        """测试列出本地模型"""
        models = ollama_utils.list_local_models()

        # 应该返回列表（可能为空）
        assert isinstance(models, list)

        # 如果有模型，检查格式
        if models:
            assert "name" in models[0]

    def test_list_remote_models(self):
        """测试列出远端模型"""
        models = ollama_utils.list_remote_models()

        # 应该返回模型列表
        assert isinstance(models, list)
        assert len(models) > 0

        # 检查模型格式
        assert "name" in models[0]

    def test_search_remote_models(self):
        """测试搜索远端模型"""
        models = ollama_utils.search_models("llama")

        assert isinstance(models, list)
        # 应该至少有一个包含 "llama" 的模型
        if models:  # 如果 API 可用
            assert any("llama" in m["name"].lower() for m in models)


class TestOllamaModelManagement:
    """测试 Ollama 模型管理（需要实际操作，谨慎运行）"""

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires actual model download, run manually")
    def test_pull_model(self):
        """测试下载模型（手动运行）"""
        # 下载一个小模型用于测试
        test_model = "qwen2.5:0.5b"  # 很小的模型

        try:
            ollama_utils.pull_model(test_model)

            # 验证模型已下载
            models = ollama_utils.list_local_models()
            model_names = [m["name"] for m in models]
            assert any(test_model in name for name in model_names)

        finally:
            # 清理：删除测试模型
            try:
                ollama_utils.delete_model(test_model)
            except:
                pass  # 忽略清理错误

    @pytest.mark.skip(reason="Requires existing model, configure manually")
    def test_show_model_info(self):
        """测试显示模型信息（需要已安装的模型）"""
        # 假设系统中有 llama2 模型
        models = ollama_utils.list_local_models()

        if not models:
            pytest.skip("No models installed")

        # 获取第一个模型的信息
        model_name = models[0]["name"]
        info = ollama_utils.show_model_info(model_name)

        # 验证返回的信息
        assert isinstance(info, dict)
        # 通常包含 modelfile, parameters 等字段
        assert len(info) > 0


class TestOllamaLLMClient:
    """测试 Ollama 与 LLMClient 集成"""

    def test_create_local_model_schema(self):
        """测试创建本地模型 Schema"""
        model = ModelSchema(
            name="llama2:7b",
            provider="ollama",
            is_local=True,
            api_url="http://localhost:11434/v1",
            api_key=None,  # 本地模型不需要 key
            max_input_tokens=4096,
            max_output_tokens=2048,
        )

        assert model.name == "llama2:7b"
        assert model.provider == "ollama"
        assert model.is_local is True
        assert model.api_key is None

    def test_create_llm_client_without_api_key(self):
        """测试创建不需要 API key 的 LLMClient"""
        model = ModelSchema(
            name="llama2:7b",
            provider="ollama",
            is_local=True,
            api_url="http://localhost:11434/v1",
        )

        # 应该不抛出异常
        client = LLMClient(model)

        assert client.model == model
        assert client.api_key is None
        assert client.api_url == "http://localhost:11434/v1"

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires installed model and actual API call")
    def test_chat_with_ollama_model(self):
        """测试使用 Ollama 模型对话（需要已安装的模型）"""
        # 检查是否有可用模型
        models = ollama_utils.list_local_models()
        if not models:
            pytest.skip("No Ollama models installed")

        # 使用第一个模型
        model_name = models[0]["name"]

        model = ModelSchema(
            name=model_name,
            provider="ollama",
            is_local=True,
            api_url="http://localhost:11434/v1",
        )

        client = LLMClient(model)

        # 发送简单的对话请求
        messages = [{"role": "user", "content": "Say 'test' and nothing else"}]

        response = client.chat(messages, temperature=0.1)

        # 验证响应
        assert isinstance(response, str)
        assert len(response) > 0


class TestOllamaDatabase:
    """测试 Ollama 模型的数据库操作"""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """创建临时数据库"""
        db_path = tmp_path / "test_ollama.db"
        db = DatabaseManager(str(db_path))
        yield db
        # 清理
        if db_path.exists():
            db_path.unlink()

    def test_add_ollama_model_to_db(self, temp_db):
        """测试将 Ollama 模型添加到数据库"""
        model = ModelSchema(
            name="llama2:13b",
            provider="ollama",
            is_local=True,
            api_url="http://localhost:11434/v1",
            code_score=7.5,
        )

        temp_db.add_model(model)

        # 验证已添加
        retrieved = temp_db.get_model("llama2:13b")
        assert retrieved.name == "llama2:13b"
        assert retrieved.provider == "ollama"
        assert retrieved.is_local is True
        assert retrieved.api_url == "http://localhost:11434/v1"

    def test_list_ollama_models_from_db(self, temp_db):
        """测试从数据库列出 Ollama 模型"""
        # 添加多个模型
        temp_db.add_model(
            ModelSchema(
                name="llama2:7b", provider="ollama", is_local=True, api_url="http://localhost:11434/v1"
            )
        )
        temp_db.add_model(
            ModelSchema(
                name="gpt-4", provider="openai", is_local=False, api_url="https://api.openai.com/v1"
            )
        )

        # 列出所有模型
        all_models = temp_db.list_models()
        assert len(all_models) == 2

        # 过滤 Ollama 模型
        ollama_models = [m for m in all_models if m.provider == "ollama"]
        assert len(ollama_models) == 1
        assert ollama_models[0].name == "llama2:7b"


class TestOllamaEndToEnd:
    """端到端测试（完整流程）"""

    @pytest.mark.slow
    @pytest.mark.skip(reason="End-to-end test, run manually")
    def test_full_workflow(self, tmp_path):
        """
        完整工作流测试：
        1. 检查 Ollama 服务
        2. 列出远端模型
        3. 下载模型
        4. 添加到数据库
        5. 创建客户端
        6. 发送对话
        7. 清理
        """
        # 1. 检查服务
        assert ollama_utils.is_ollama_available()

        # 2. 列出远端模型
        remote_models = ollama_utils.list_remote_models()
        assert len(remote_models) > 0

        # 3. 下载一个小模型（实际运行时取消注释）
        test_model = "qwen2.5:0.5b"
        # ollama_utils.pull_model(test_model)

        # 4. 添加到数据库
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))

        model = ModelSchema(
            name=test_model,
            provider="ollama",
            is_local=True,
            api_url="http://localhost:11434/v1",
        )
        db.add_model(model)

        # 5. 创建客户端
        client = LLMClient(model)

        # 6. 发送对话（实际运行时取消注释）
        # messages = [{"role": "user", "content": "Hello"}]
        # response = client.chat(messages)
        # assert isinstance(response, str)

        # 7. 清理（实际运行时取消注释）
        # ollama_utils.delete_model(test_model)

        assert True  # Placeholder
