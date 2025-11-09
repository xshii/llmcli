"""
Ollama 工具函数
提供 Ollama 模型管理功能
"""

import httpx
from typing import Dict, List, Optional

from aicode.utils.logger import get_logger

logger = get_logger(__name__)

# Ollama 默认地址
OLLAMA_BASE_URL = "http://localhost:11434"


def is_ollama_available(base_url: str = OLLAMA_BASE_URL, timeout: float = 2.0) -> bool:
    """
    检查 Ollama 服务是否可用

    Args:
        base_url: Ollama 服务地址
        timeout: 超时时间（秒）

    Returns:
        bool: 服务可用返回 True
    """
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=timeout)
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Ollama not available: {e}")
        return False


def list_local_models(base_url: str = OLLAMA_BASE_URL) -> List[Dict]:
    """
    列出本地已安装的模型

    Args:
        base_url: Ollama 服务地址

    Returns:
        List[Dict]: 模型列表，每个模型包含 name, size, modified_at 等信息

    Raises:
        httpx.HTTPStatusError: API 请求失败
    """
    response = httpx.get(f"{base_url}/api/tags", timeout=10.0)
    response.raise_for_status()

    data = response.json()
    models = data.get("models", [])

    logger.debug(f"Found {len(models)} local models")
    return models


def pull_model(name: str, base_url: str = OLLAMA_BASE_URL) -> None:
    """
    下载模型（流式输出进度）

    Args:
        name: 模型名称（如 llama2:13b）
        base_url: Ollama 服务地址

    Raises:
        httpx.HTTPStatusError: API 请求失败
    """
    logger.info(f"Pulling model: {name}")

    with httpx.stream(
        "POST",
        f"{base_url}/api/pull",
        json={"name": name},
        timeout=None,  # 下载可能很久
    ) as response:
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                # Ollama 返回 JSON 格式的进度信息
                try:
                    import json

                    data = json.loads(line)
                    status = data.get("status", "")

                    # 打印进度
                    if "total" in data and "completed" in data:
                        total = data["total"]
                        completed = data["completed"]
                        percent = int((completed / total) * 100) if total > 0 else 0
                        print(f"\r{status}: {percent}%", end="", flush=True)
                    else:
                        print(f"\r{status}", end="", flush=True)

                except json.JSONDecodeError:
                    print(line)

    print()  # 换行
    logger.info(f"Model {name} pulled successfully")


def delete_model(name: str, base_url: str = OLLAMA_BASE_URL) -> None:
    """
    删除模型

    Args:
        name: 模型名称
        base_url: Ollama 服务地址

    Raises:
        httpx.HTTPStatusError: API 请求失败
    """
    logger.info(f"Deleting model: {name}")

    response = httpx.delete(f"{base_url}/api/delete", json={"name": name}, timeout=10.0)
    response.raise_for_status()

    logger.info(f"Model {name} deleted successfully")


def show_model_info(name: str, base_url: str = OLLAMA_BASE_URL) -> Dict:
    """
    显示模型详细信息

    Args:
        name: 模型名称
        base_url: Ollama 服务地址

    Returns:
        Dict: 模型详细信息

    Raises:
        httpx.HTTPStatusError: API 请求失败
    """
    response = httpx.post(f"{base_url}/api/show", json={"name": name}, timeout=10.0)
    response.raise_for_status()

    return response.json()


def list_remote_models(search: Optional[str] = None) -> List[Dict]:
    """
    列出远端可用的模型（使用社区 API）

    Args:
        search: 搜索关键词（可选）

    Returns:
        List[Dict]: 模型列表

    Note:
        使用第三方 API (ollamadb.dev)，如果失败则返回内置列表
    """
    try:
        params = {}
        if search:
            params["search"] = search

        response = httpx.get(
            "https://ollamadb.dev/api/v1/models", params=params, timeout=10.0
        )
        response.raise_for_status()

        models = response.json()
        logger.debug(f"Fetched {len(models)} remote models")
        return models

    except Exception as e:
        logger.warning(f"Failed to fetch remote models: {e}, using builtin list")
        return _get_builtin_models(search)


def _get_builtin_models(search: Optional[str] = None) -> List[Dict]:
    """
    获取内置常用模型列表（备用）

    Args:
        search: 搜索关键词（可选）

    Returns:
        List[Dict]: 模型列表
    """
    models = [
        {
            "name": "llama3.3:latest",
            "size": "42GB",
            "description": "Meta Llama 3.3",
        },
        {"name": "llama3.1:8b", "size": "4.7GB", "description": "Meta Llama 3.1 8B"},
        {"name": "llama2:13b", "size": "7.3GB", "description": "Meta Llama 2 13B"},
        {"name": "llama2:7b", "size": "3.8GB", "description": "Meta Llama 2 7B"},
        {"name": "codellama:7b", "size": "3.8GB", "description": "Code Llama 7B"},
        {"name": "codellama:13b", "size": "7.3GB", "description": "Code Llama 13B"},
        {
            "name": "deepseek-r1:7b",
            "size": "4.1GB",
            "description": "DeepSeek R1 7B (reasoning)",
        },
        {"name": "gemma2:9b", "size": "5.4GB", "description": "Google Gemma 2 9B"},
        {"name": "gemma2:2b", "size": "1.6GB", "description": "Google Gemma 2 2B"},
        {"name": "qwen2.5:7b", "size": "4.4GB", "description": "Alibaba Qwen 2.5 7B"},
        {
            "name": "qwen2.5-coder:7b",
            "size": "4.4GB",
            "description": "Qwen 2.5 Coder 7B",
        },
        {"name": "mistral:7b", "size": "4.1GB", "description": "Mistral 7B"},
        {"name": "phi4:latest", "size": "8.4GB", "description": "Microsoft Phi-4"},
    ]

    # 如果有搜索关键词，过滤模型
    if search:
        search_lower = search.lower()
        models = [
            m
            for m in models
            if search_lower in m["name"].lower()
            or search_lower in m.get("description", "").lower()
        ]

    return models


def search_models(keyword: str) -> List[Dict]:
    """
    搜索远端模型（便捷函数）

    Args:
        keyword: 搜索关键词

    Returns:
        List[Dict]: 匹配的模型列表
    """
    return list_remote_models(search=keyword)
