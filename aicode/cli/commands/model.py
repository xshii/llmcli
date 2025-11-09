"""
model 命令 - 管理LLM模型
重构后使用依赖注入，遵循依赖倒置原则
"""

import argparse

from aicode.cli.utils.output import Output
from aicode.infrastructure.di_container import get_container
from aicode.llm.exceptions import ModelAlreadyExistsError, ModelNotFoundError
from aicode.models.schema import ModelSchema
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


def setup_parser(subparsers) -> argparse.ArgumentParser:
    """
    设置model命令的参数解析器

    Args:
        subparsers: 子命令解析器

    Returns:
        ArgumentParser: model命令的解析器
    """
    parser = subparsers.add_parser(
        "model",
        help="Manage LLM models",
        description="Add, list, update, or remove models",
    )

    model_subparsers = parser.add_subparsers(
        dest="model_command", help="Model commands"
    )

    # list 子命令
    list_parser = model_subparsers.add_parser("list", help="List all models")
    list_parser.add_argument("--provider", type=str, help="Filter by provider")
    list_parser.set_defaults(func=execute_list)

    # add 子命令
    add_parser = model_subparsers.add_parser("add", help="Add a new model")
    add_parser.add_argument("name", type=str, help="Model name")
    add_parser.add_argument(
        "provider", type=str, help="Provider (openai, anthropic, etc.)"
    )
    add_parser.add_argument("--max-input", type=int, help="Max input tokens")
    add_parser.add_argument("--max-output", type=int, help="Max output tokens")
    add_parser.add_argument("--context-window", type=int, help="Context window size")
    add_parser.add_argument(
        "--code-score", type=float, help="Code capability score (0-10)"
    )
    add_parser.add_argument("--api-key", type=str, help="API key for this model")
    add_parser.add_argument("--api-url", type=str, help="API URL for this model")
    add_parser.set_defaults(func=execute_add)

    # remove 子命令
    remove_parser = model_subparsers.add_parser("remove", help="Remove a model")
    remove_parser.add_argument("name", type=str, help="Model name")
    remove_parser.set_defaults(func=execute_remove)

    # show 子命令
    show_parser = model_subparsers.add_parser("show", help="Show model details")
    show_parser.add_argument("name", type=str, help="Model name")
    show_parser.set_defaults(func=execute_show)

    parser.set_defaults(func=lambda args: parser.print_help())
    return parser


def execute_list(args: argparse.Namespace) -> int:
    """列出所有模型"""
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        model_repo = container.get_model_repository()

        # 构建筛选条件
        filters = {}
        if args.provider:
            filters["provider"] = args.provider

        models = model_repo.query_models(filters if filters else None)

        if not models:
            Output.print_warning("No models found.")
            Output.print_info("Add a model with: aicode model add")
            return 0

        # 准备表格数据
        headers = ["Name", "Provider", "Max Input", "Max Output", "Code Score"]
        rows = []

        for model in models:
            rows.append(
                [
                    model.name,
                    model.provider,
                    model.max_input_tokens or "-",
                    model.max_output_tokens or "-",
                    f"{model.code_score:.1f}" if model.code_score is not None else "-",
                ]
            )

        Output.print_table(headers, rows)
        Output.print_info(f"Total: {len(models)} model(s)")
        return 0

    except Exception as e:
        Output.print_error(f"Failed to list models: {e}")
        logger.exception("Error in model list command")
        return 1


def execute_add(args: argparse.Namespace) -> int:
    """添加新模型"""
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        model_repo = container.get_model_repository()

        # 创建模型
        model = ModelSchema(
            name=args.name,
            provider=args.provider,
            max_input_tokens=args.max_input,
            max_output_tokens=args.max_output,
            context_window=args.context_window,
            code_score=args.code_score,
            api_key=args.api_key,
            api_url=args.api_url,
        )

        model_repo.insert_model(model)
        Output.print_success(f"Added model: {args.name}")
        return 0

    except ModelAlreadyExistsError:
        Output.print_error(f"Model '{args.name}' already exists.")
        return 1
    except Exception as e:
        Output.print_error(f"Failed to add model: {e}")
        logger.exception("Error in model add command")
        return 1


def execute_remove(args: argparse.Namespace) -> int:
    """删除模型"""
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        model_repo = container.get_model_repository()

        # 确认删除
        if not Output.confirm(f"Remove model '{args.name}'?"):
            Output.print_info("Cancelled.")
            return 0

        model_repo.delete_model(args.name)
        Output.print_success(f"Removed model: {args.name}")
        return 0

    except ModelNotFoundError:
        Output.print_error(f"Model '{args.name}' not found.")
        return 1
    except Exception as e:
        Output.print_error(f"Failed to remove model: {e}")
        logger.exception("Error in model remove command")
        return 1


def execute_show(args: argparse.Namespace) -> int:
    """显示模型详情"""
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        model_repo = container.get_model_repository()
        model = model_repo.get_model(args.name)

        Output.print_header(f"Model: {model.name}")

        # 构建信息字典
        info = {
            "Provider": model.provider,
            "Max Input Tokens": model.max_input_tokens or "Not set",
            "Max Output Tokens": model.max_output_tokens or "Not set",
            "Context Window": model.context_window or "Not set",
            "Effective Context Limit": model.get_context_limit() or "Not set",
            "Code Score": (
                f"{model.code_score:.1f}" if model.code_score is not None else "Not set"
            ),
            "Reasoning Score": (
                f"{model.reasoning_score:.1f}"
                if model.reasoning_score is not None
                else "Not set"
            ),
            "Speed Score": (
                f"{model.speed_score:.1f}"
                if model.speed_score is not None
                else "Not set"
            ),
            "Specialties": (
                ", ".join(model.specialties) if model.specialties else "Not set"
            ),
            "API Key": "***" if model.api_key else "Not set",
            "API URL": model.api_url or "Not set",
            "Notes": model.notes or "Not set",
        }

        Output.print_dict(info)
        return 0

    except ModelNotFoundError:
        Output.print_error(f"Model '{args.name}' not found.")
        return 1
    except Exception as e:
        Output.print_error(f"Failed to show model: {e}")
        logger.exception("Error in model show command")
        return 1


def execute(args: argparse.Namespace) -> int:
    """
    执行model命令（路由到子命令）

    Args:
        args: 命令行参数

    Returns:
        int: 退出码
    """
    if hasattr(args, "func") and args.func != execute:
        return args.func(args)
    else:
        # 没有指定子命令，显示帮助
        Output.print_error("Please specify a subcommand: list, add, remove, or show")
        return 1
