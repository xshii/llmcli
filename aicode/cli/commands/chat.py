"""
chat 命令 - 与LLM对话
重构后使用依赖注入，遵循依赖倒置原则
"""

import argparse
from typing import Optional

from aicode.cli.utils.file_ops import FileOperations
from aicode.cli.utils.output import Output
from aicode.infrastructure.di_container import get_container
from aicode.llm.client import LLMClient
from aicode.llm.exceptions import APIError, ModelNotFoundError
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


def setup_parser(subparsers) -> argparse.ArgumentParser:
    """
    设置chat命令的参数解析器

    Args:
        subparsers: 子命令解析器

    Returns:
        ArgumentParser: chat命令的解析器
    """
    parser = subparsers.add_parser(
        "chat",
        help="Chat with LLM",
        description="Send a message to the LLM and get a response",
    )

    parser.add_argument(
        "message",
        type=str,
        nargs="?",
        help="Message to send (if not provided, enters interactive mode)",
    )

    parser.add_argument(
        "-f", "--file", type=str, help="Include file content in the conversation"
    )

    parser.add_argument(
        "-m", "--model", type=str, help="Model to use (overrides default)"
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for generation (default: 0.7)",
    )

    parser.add_argument("--max-tokens", type=int, help="Maximum tokens to generate")

    parser.set_defaults(func=execute)
    return parser


def execute(args: argparse.Namespace) -> int:
    """
    执行chat命令

    Args:
        args: 命令行参数

    Returns:
        int: 退出码（0表示成功）
    """
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        config_repo = container.get_config_repository()
        model_repo = container.get_model_repository()

        # 加载配置
        if not config_repo.config_exists():
            Output.print_error("Config not found. Please run 'aicode init' first.")
            return 1

        config_repo.load()

        # 确定使用的模型
        model_name = args.model or config_repo.get("global.default_model")
        if not model_name:
            Output.print_error(
                "No model specified. Use --model or set default_model in config."
            )
            return 1

        # 从数据库加载模型
        try:
            model = model_repo.get_model(model_name)
        except ModelNotFoundError:
            Output.print_error(f"Model '{model_name}' not found in database.")
            Output.print_info("Available models: aicode model list")
            return 1

        # 获取API配置
        api_key = config_repo.get("global.api_key") or model.api_key
        api_url = config_repo.get("global.api_url") or model.api_url

        if not api_key:
            Output.print_error("API key not configured.")
            Output.print_info("Set it with: aicode config set global.api_key YOUR_KEY")
            return 1

        # 创建LLM客户端
        client = LLMClient(model, api_key=api_key, api_url=api_url)

        # 构建消息
        messages = []

        # 如果指定了文件，先添加文件内容
        if args.file:
            try:
                file_content = FileOperations.read_file(args.file)
                messages.append(
                    {
                        "role": "user",
                        "content": f"Here is the content of {args.file}:\n\n```\n{file_content}\n```",
                    }
                )
                Output.print_info(f"Included file: {args.file}")
            except FileNotFoundError:
                Output.print_error(f"File not found: {args.file}")
                return 1
            except Exception as e:
                Output.print_error(f"Failed to read file: {e}")
                return 1

        # 添加用户消息
        if args.message:
            messages.append({"role": "user", "content": args.message})
        else:
            # 交互模式
            Output.print_info("No message provided, entering interactive mode...")
            Output.print_info("Type your message (Ctrl+D to send, Ctrl+C to exit)")
            try:
                user_message = []
                while True:
                    line = input()
                    user_message.append(line)
            except EOFError:
                messages.append({"role": "user", "content": "\n".join(user_message)})
            except KeyboardInterrupt:
                Output.print_info("\nCancelled.")
                return 0

        # 显示token和成本信息
        token_count = client.count_message_tokens(messages)
        cost = client.estimate_cost(messages, output_tokens=500)

        Output.print_info(f"Model: {model.name}")
        Output.print_info(f"Input tokens: {token_count}")
        if cost is not None:
            Output.print_info(f"Estimated cost: ${cost:.6f}")

        # 发送请求
        Output.print_separator()
        try:
            response = client.chat(
                messages, temperature=args.temperature, max_tokens=args.max_tokens
            )

            # 显示响应
            print(response)
            Output.print_separator()

            Output.print_success("Response received")
            return 0

        except APIError as e:
            Output.print_error(f"API error: {e}")
            return 1

    except KeyboardInterrupt:
        Output.print_info("\nInterrupted by user.")
        return 130
    except Exception as e:
        Output.print_error(f"Unexpected error: {e}")
        logger.exception("Unexpected error in chat command")
        return 1
