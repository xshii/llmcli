#!/usr/bin/env python3
"""
Ollama 使用示例

演示如何在 AICode 中使用 Ollama 本地模型
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aicode.models.schema import ModelSchema
from aicode.llm.client import LLMClient
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


def example_1_basic_chat():
    """示例 1: 基本对话"""
    print("\n=== 示例 1: 基本对话 ===\n")

    # 创建 Ollama 模型配置
    model = ModelSchema(
        name="llama3.2:3b",
        provider="ollama",
        api_url="http://localhost:11434",
        api_key="",  # Ollama 不需要 API key
        max_input_tokens=2048,
        max_output_tokens=1024
    )

    # 创建客户端
    client = LLMClient(model=model)

    # 发送对话
    messages = [
        {"role": "user", "content": "用一句话解释什么是 Python 装饰器？"}
    ]

    print(f"用户: {messages[0]['content']}")
    response = client.chat(messages)
    print(f"AI: {response}\n")


def example_2_code_generation():
    """示例 2: 代码生成"""
    print("\n=== 示例 2: 代码生成 ===\n")

    # 使用代码专用模型
    model = ModelSchema(
        name="qwen2.5-coder:7b",
        provider="ollama",
        api_url="http://localhost:11434",
        api_key="",
        max_input_tokens=4096,
        max_output_tokens=2048,
        code_score=9.0
    )

    client = LLMClient(model=model)

    messages = [
        {
            "role": "user",
            "content": "写一个 Python 函数，实现二分查找算法，包含详细注释"
        }
    ]

    print(f"用户: {messages[0]['content']}")
    response = client.chat(messages, temperature=0.3)  # 降低温度以获得更确定的代码
    print(f"AI:\n{response}\n")


def example_3_code_review():
    """示例 3: 代码审查"""
    print("\n=== 示例 3: 代码审查 ===\n")

    model = ModelSchema(
        name="deepseek-coder:6.7b",
        provider="ollama",
        api_url="http://localhost:11434",
        api_key="",
        max_input_tokens=4096,
        max_output_tokens=2048,
        code_score=9.5
    )

    client = LLMClient(model=model)

    # 需要审查的代码
    code_to_review = """
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    return total / len(numbers)
"""

    messages = [
        {
            "role": "user",
            "content": f"审查以下代码并给出改进建议：\n\n```python\n{code_to_review}\n```"
        }
    ]

    print(f"用户: 审查代码")
    print(f"代码:\n{code_to_review}")
    response = client.chat(messages)
    print(f"AI 审查意见:\n{response}\n")


def example_4_multi_turn_conversation():
    """示例 4: 多轮对话"""
    print("\n=== 示例 4: 多轮对话 ===\n")

    model = ModelSchema(
        name="llama3.2:3b",
        provider="ollama",
        api_url="http://localhost:11434",
        api_key="",
        max_input_tokens=2048,
        max_output_tokens=1024
    )

    client = LLMClient(model=model)

    # 对话历史
    messages = []

    # 第一轮
    messages.append({"role": "user", "content": "什么是递归？"})
    print(f"用户: {messages[-1]['content']}")

    response = client.chat(messages)
    print(f"AI: {response}\n")

    messages.append({"role": "assistant", "content": response})

    # 第二轮
    messages.append({"role": "user", "content": "给我一个简单的递归例子"})
    print(f"用户: {messages[-1]['content']}")

    response = client.chat(messages)
    print(f"AI: {response}\n")


def example_5_with_file_context():
    """示例 5: 带文件上下文的对话"""
    print("\n=== 示例 5: 带文件上下文 ===\n")

    model = ModelSchema(
        name="qwen2.5-coder:7b",
        provider="ollama",
        api_url="http://localhost:11434",
        api_key="",
        max_input_tokens=4096,
        max_output_tokens=2048
    )

    client = LLMClient(model=model)

    # 读取文件内容（这里使用示例代码）
    file_content = """
class UserManager:
    def __init__(self):
        self.users = []

    def add_user(self, name, email):
        user = {'name': name, 'email': email}
        self.users.append(user)

    def get_user(self, email):
        for user in self.users:
            if user['email'] == email:
                return user
        return None
"""

    messages = [
        {
            "role": "user",
            "content": f"分析以下代码并解释其功能，然后给出改进建议：\n\n```python\n{file_content}\n```"
        }
    ]

    print("用户: 分析代码并给出改进建议")
    print(f"代码:\n{file_content}")
    response = client.chat(messages)
    print(f"AI:\n{response}\n")


def example_6_model_info_and_tokens():
    """示例 6: 获取模型信息和 Token 统计"""
    print("\n=== 示例 6: 模型信息和 Token 统计 ===\n")

    model = ModelSchema(
        name="llama3.2:3b",
        provider="ollama",
        api_url="http://localhost:11434",
        api_key="",
        max_input_tokens=2048,
        max_output_tokens=1024,
        code_score=7.0,
        reasoning_score=8.0
    )

    client = LLMClient(model=model)

    # 获取模型信息
    info = client.get_model_info()
    print("模型信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # 计算消息的 Token 数
    messages = [
        {"role": "user", "content": "解释一下 Python 的列表推导式"}
    ]

    token_count = client.count_message_tokens(messages)
    print(f"\n消息 Token 数: {token_count}")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("Ollama 使用示例")
    print("=" * 60)
    print("\n确保 Ollama 服务正在运行: ollama serve")
    print("确保已下载所需模型:")
    print("  - ollama pull llama3.2:3b")
    print("  - ollama pull qwen2.5-coder:7b")
    print("  - ollama pull deepseek-coder:6.7b")
    print("=" * 60)

    try:
        # 运行示例（注释掉不需要的示例）
        example_1_basic_chat()
        # example_2_code_generation()
        # example_3_code_review()
        # example_4_multi_turn_conversation()
        # example_5_with_file_context()
        # example_6_model_info_and_tokens()

        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)

    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        print(f"\n错误: {e}")
        print("\n请确保:")
        print("1. Ollama 服务正在运行 (ollama serve)")
        print("2. 已下载所需的模型")
        print("3. 模型名称正确")


if __name__ == "__main__":
    main()
