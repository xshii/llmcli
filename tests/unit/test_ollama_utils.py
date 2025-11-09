"""
ollama_utils 单元测试
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from aicode.llm import ollama_utils


class TestIsOllamaAvailable:
    """测试 Ollama 服务可用性检查"""

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_ollama_available(self, mock_get):
        """测试 Ollama 可用"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert ollama_utils.is_ollama_available() is True
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", timeout=2.0
        )

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_ollama_unavailable(self, mock_get):
        """测试 Ollama 不可用"""
        mock_get.side_effect = Exception("Connection refused")

        assert ollama_utils.is_ollama_available() is False

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_custom_base_url(self, mock_get):
        """测试自定义基础 URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        ollama_utils.is_ollama_available(base_url="http://custom:8080")
        mock_get.assert_called_once_with(
            "http://custom:8080/api/tags", timeout=2.0
        )


class TestListLocalModels:
    """测试列出本地模型"""

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_list_models_success(self, mock_get):
        """测试成功列出模型"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:13b", "size": 7300000000, "modified_at": "2024-01-01"},
                {"name": "codellama:7b", "size": 3800000000, "modified_at": "2024-01-02"},
            ]
        }
        mock_get.return_value = mock_response

        models = ollama_utils.list_local_models()

        assert len(models) == 2
        assert models[0]["name"] == "llama2:13b"
        assert models[1]["name"] == "codellama:7b"

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_list_models_empty(self, mock_get):
        """测试空模型列表"""
        mock_response = Mock()
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        models = ollama_utils.list_local_models()

        assert models == []

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_list_models_error(self, mock_get):
        """测试 API 错误"""
        import httpx

        mock_get.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock()
        )

        with pytest.raises(httpx.HTTPStatusError):
            ollama_utils.list_local_models()


class TestPullModel:
    """测试下载模型"""

    @patch("aicode.llm.ollama_utils.httpx.stream")
    @patch("builtins.print")
    def test_pull_model_success(self, mock_print, mock_stream):
        """测试成功下载模型"""
        # 模拟流式响应
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status = Mock()
        mock_response.iter_lines.return_value = [
            json.dumps({"status": "downloading", "completed": 50, "total": 100}),
            json.dumps({"status": "downloading", "completed": 100, "total": 100}),
            json.dumps({"status": "success"}),
        ]

        mock_stream.return_value = mock_response

        ollama_utils.pull_model("llama2:13b")

        mock_stream.assert_called_once()
        # 验证打印了进度
        assert mock_print.call_count > 0

    @patch("aicode.llm.ollama_utils.httpx.stream")
    def test_pull_model_error(self, mock_stream):
        """测试下载失败"""
        import httpx

        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=Mock(), response=Mock()
        )

        mock_stream.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            ollama_utils.pull_model("invalid-model")


class TestDeleteModel:
    """测试删除模型"""

    @patch("aicode.llm.ollama_utils.httpx.delete")
    def test_delete_model_success(self, mock_delete):
        """测试成功删除模型"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_delete.return_value = mock_response

        ollama_utils.delete_model("llama2:13b")

        mock_delete.assert_called_once_with(
            "http://localhost:11434/api/delete",
            json={"name": "llama2:13b"},
            timeout=10.0,
        )

    @patch("aicode.llm.ollama_utils.httpx.delete")
    def test_delete_model_error(self, mock_delete):
        """测试删除失败"""
        import httpx

        mock_delete.side_effect = httpx.HTTPStatusError(
            "Not found", request=Mock(), response=Mock()
        )

        with pytest.raises(httpx.HTTPStatusError):
            ollama_utils.delete_model("nonexistent")


class TestShowModelInfo:
    """测试显示模型信息"""

    @patch("aicode.llm.ollama_utils.httpx.post")
    def test_show_model_info_success(self, mock_post):
        """测试成功获取模型信息"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "modelfile": "FROM llama2",
            "parameters": "temperature 0.7",
            "template": "{{.System}}\n{{.Prompt}}",
        }
        mock_post.return_value = mock_response

        info = ollama_utils.show_model_info("llama2:13b")

        assert "modelfile" in info
        assert "parameters" in info
        mock_post.assert_called_once()


class TestListRemoteModels:
    """测试列出远端模型"""

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_list_remote_models_success(self, mock_get):
        """测试成功获取远端模型列表"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"name": "llama3:latest", "size": "42GB", "description": "Llama 3"},
            {"name": "gemma2:9b", "size": "5.4GB", "description": "Gemma 2"},
        ]
        mock_get.return_value = mock_response

        models = ollama_utils.list_remote_models()

        assert len(models) == 2
        assert models[0]["name"] == "llama3:latest"

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_list_remote_models_with_search(self, mock_get):
        """测试搜索远端模型"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"name": "codellama:7b", "size": "3.8GB", "description": "Code Llama"}
        ]
        mock_get.return_value = mock_response

        models = ollama_utils.list_remote_models(search="code")

        mock_get.assert_called_once_with(
            "https://ollamadb.dev/api/v1/models",
            params={"search": "code"},
            timeout=10.0,
        )
        assert len(models) == 1

    @patch("aicode.llm.ollama_utils.httpx.get")
    def test_list_remote_models_fallback(self, mock_get):
        """测试 API 失败时使用内置列表"""
        mock_get.side_effect = Exception("Network error")

        models = ollama_utils.list_remote_models()

        # 应该返回内置列表
        assert len(models) > 0
        assert any("llama" in m["name"].lower() for m in models)


class TestGetBuiltinModels:
    """测试内置模型列表"""

    def test_get_all_builtin_models(self):
        """测试获取所有内置模型"""
        models = ollama_utils._get_builtin_models()

        assert len(models) > 0
        assert all("name" in m for m in models)
        assert all("size" in m for m in models)
        assert all("description" in m for m in models)

    def test_search_builtin_models(self):
        """测试搜索内置模型"""
        models = ollama_utils._get_builtin_models(search="code")

        # 应该只返回包含 "code" 的模型
        assert all("code" in m["name"].lower() or "code" in m["description"].lower() for m in models)

    def test_search_builtin_models_case_insensitive(self):
        """测试大小写不敏感搜索"""
        models_lower = ollama_utils._get_builtin_models(search="llama")
        models_upper = ollama_utils._get_builtin_models(search="LLAMA")

        assert len(models_lower) == len(models_upper)


class TestSearchModels:
    """测试搜索模型（便捷函数）"""

    @patch("aicode.llm.ollama_utils.list_remote_models")
    def test_search_models(self, mock_list):
        """测试搜索模型"""
        mock_list.return_value = [{"name": "llama2:7b"}]

        result = ollama_utils.search_models("llama")

        mock_list.assert_called_once_with(search="llama")
        assert result == [{"name": "llama2:7b"}]
