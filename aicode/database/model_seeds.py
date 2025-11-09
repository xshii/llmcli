"""
模型种子数据 - 常见 LLM 模型配置
"""

from typing import Any, Dict, List

# 常见模型配置
MODEL_SEEDS = [
    # OpenAI GPT 系列
    {
        "name": "gpt-4",
        "provider": "openai",
        "max_input_tokens": 8192,
        "max_output_tokens": 4096,
        "code_score": 9.0,
        "reasoning_score": 9.5,
        "speed_score": 7.0,
        "vscode_friendly": True,  # 格式遵循度高
        "api_url": "https://api.openai.com/v1",
        "notes": "GPT-4 - 最强通用模型",
    },
    {
        "name": "gpt-4-turbo",
        "provider": "openai",
        "max_input_tokens": 128000,
        "max_output_tokens": 4096,
        "code_score": 9.2,
        "reasoning_score": 9.5,
        "speed_score": 8.5,
        "vscode_friendly": True,
        "api_url": "https://api.openai.com/v1",
        "notes": "GPT-4 Turbo - 更快更长上下文",
    },
    {
        "name": "gpt-3.5-turbo",
        "provider": "openai",
        "max_input_tokens": 16385,
        "max_output_tokens": 4096,
        "code_score": 7.5,
        "reasoning_score": 8.0,
        "speed_score": 9.5,
        "vscode_friendly": True,
        "api_url": "https://api.openai.com/v1",
        "notes": "GPT-3.5 - 快速经济",
    },
    # Anthropic Claude 系列
    {
        "name": "claude-3-opus",
        "provider": "anthropic",
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "code_score": 9.5,
        "reasoning_score": 9.8,
        "speed_score": 7.0,
        "vscode_friendly": True,  # 格式遵循优秀
        "api_url": "https://api.anthropic.com/v1",
        "notes": "Claude 3 Opus - 最强推理",
    },
    {
        "name": "claude-3-sonnet",
        "provider": "anthropic",
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "code_score": 9.0,
        "reasoning_score": 9.0,
        "speed_score": 8.5,
        "vscode_friendly": True,
        "api_url": "https://api.anthropic.com/v1",
        "notes": "Claude 3 Sonnet - 平衡性能",
    },
    {
        "name": "claude-3-haiku",
        "provider": "anthropic",
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "code_score": 8.0,
        "reasoning_score": 8.0,
        "speed_score": 9.5,
        "vscode_friendly": True,
        "api_url": "https://api.anthropic.com/v1",
        "notes": "Claude 3 Haiku - 最快响应",
    },
    # DeepSeek 系列（可能有深度思考污染）
    {
        "name": "deepseek-chat",
        "provider": "deepseek",
        "max_input_tokens": 32768,
        "max_output_tokens": 4096,
        "code_score": 8.5,
        "reasoning_score": 8.5,
        "speed_score": 8.0,
        "vscode_friendly": False,  # 可能返回 <think> 标签污染
        "api_url": "https://api.deepseek.com/v1",
        "notes": "DeepSeek Chat - 可能有深度思考污染，需清理",
    },
    {
        "name": "deepseek-coder",
        "provider": "deepseek",
        "max_input_tokens": 32768,
        "max_output_tokens": 4096,
        "code_score": 9.0,
        "reasoning_score": 8.0,
        "speed_score": 8.5,
        "vscode_friendly": False,  # 可能返回 <think> 标签
        "api_url": "https://api.deepseek.com/v1",
        "notes": "DeepSeek Coder - 代码专用，但可能有思考污染",
    },
    # 其他模型（未测试，默认标记为 False）
    {
        "name": "qwen-max",
        "provider": "qwen",
        "max_input_tokens": 8192,
        "max_output_tokens": 2048,
        "code_score": 8.0,
        "reasoning_score": 8.5,
        "speed_score": 8.0,
        "vscode_friendly": False,  # 未验证
        "api_url": "https://dashscope.aliyuncs.com/api/v1",
        "notes": "Qwen Max - 需测试格式支持",
    },
    {
        "name": "qwen-plus",
        "provider": "qwen",
        "max_input_tokens": 32768,
        "max_output_tokens": 2048,
        "code_score": 7.5,
        "reasoning_score": 8.0,
        "speed_score": 8.5,
        "vscode_friendly": False,
        "api_url": "https://dashscope.aliyuncs.com/api/v1",
        "notes": "Qwen Plus - 需测试格式支持",
    },
    {
        "name": "gemini-pro",
        "provider": "google",
        "max_input_tokens": 32768,
        "max_output_tokens": 2048,
        "code_score": 8.0,
        "reasoning_score": 8.5,
        "speed_score": 8.5,
        "vscode_friendly": False,
        "api_url": "https://generativelanguage.googleapis.com/v1",
        "notes": "Gemini Pro - 需测试格式支持",
    },
    {
        "name": "glm-4",
        "provider": "zhipu",
        "max_input_tokens": 128000,
        "max_output_tokens": 4096,
        "code_score": 7.5,
        "reasoning_score": 8.0,
        "speed_score": 8.0,
        "vscode_friendly": False,
        "api_url": "https://open.bigmodel.cn/api/paas/v4",
        "notes": "GLM-4 - 需测试格式支持",
    },
    {
        "name": "baichuan2-turbo",
        "provider": "baichuan",
        "max_input_tokens": 32768,
        "max_output_tokens": 2048,
        "code_score": 7.0,
        "reasoning_score": 7.5,
        "speed_score": 9.0,
        "vscode_friendly": False,
        "api_url": "https://api.baichuan-ai.com/v1",
        "notes": "Baichuan2 Turbo - 需测试格式支持",
    },
    {
        "name": "mistral-large",
        "provider": "mistral",
        "max_input_tokens": 32768,
        "max_output_tokens": 8192,
        "code_score": 8.5,
        "reasoning_score": 8.5,
        "speed_score": 8.0,
        "vscode_friendly": False,
        "api_url": "https://api.mistral.ai/v1",
        "notes": "Mistral Large - 需测试格式支持",
    },
]


def get_model_by_name(name: str) -> Dict[str, Any]:
    """根据名称获取模型配置"""
    for model in MODEL_SEEDS:
        if model["name"] == name:
            return model
    return None


def get_models_by_provider(provider: str) -> List[Dict[str, Any]]:
    """根据提供商获取模型列表"""
    return [m for m in MODEL_SEEDS if m["provider"] == provider]


def get_thinking_models() -> List[Dict[str, Any]]:
    """获取支持深度思考的模型"""
    return [m for m in MODEL_SEEDS if m.get("supports_thinking", False)]
