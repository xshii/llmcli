"""
Ollama 命令 - 管理本地模型
"""

from aicode.cli.utils.output import Output
from aicode.llm import ollama_utils


def handle_list(args):
    """列出本地已安装的模型"""
    try:
        models = ollama_utils.list_local_models()

        if not models:
            Output.print_warning("No models found")
            Output.print_info("Pull a model: aicode ollama pull llama2:13b")
            return 0

        # 打印表格
        headers = ["Name", "Size", "Modified"]
        rows = []
        for model in models:
            name = model.get("name", "")
            size = model.get("size", "")
            # 格式化大小
            if isinstance(size, int):
                size = _format_size(size)
            modified = model.get("modified_at", "")
            if modified:
                # 简化时间格式
                modified = modified.split("T")[0] if "T" in modified else modified
            rows.append([name, size, modified])

        Output.print_table(headers, rows)
        return 0

    except Exception as e:
        Output.print_error(f"Failed to list models: {e}")
        Output.print_info("Make sure Ollama is running: ollama serve")
        return 1


def handle_pull(args):
    """下载模型"""
    try:
        Output.print_info(f"Pulling model: {args.model_name}")
        ollama_utils.pull_model(args.model_name)
        Output.print_success(f"Model {args.model_name} downloaded successfully")

        # 提示用户添加到 aicode
        Output.print_info(f"\nTo use this model in aicode, add it to the database:")
        print(
            f"  aicode model add {args.model_name} ollama "
            f"--api-url http://localhost:11434/v1 --local"
        )

        return 0

    except Exception as e:
        Output.print_error(f"Failed to pull model: {e}")
        return 1


def handle_search(args):
    """搜索远端可用的模型"""
    try:
        keyword = getattr(args, "keyword", None)

        if keyword:
            Output.print_info(f"Searching for: {keyword}")
        else:
            Output.print_info("Listing popular models...")

        models = ollama_utils.list_remote_models(search=keyword)

        if not models:
            Output.print_warning("No models found")
            return 0

        # 打印表格（限制显示数量）
        headers = ["Name", "Size", "Description"]
        rows = []
        for model in models[:20]:  # 只显示前 20 个
            name = model.get("name", "")
            size = model.get("size", "N/A")
            description = model.get("description", "")
            # 截断描述
            if len(description) > 50:
                description = description[:47] + "..."
            rows.append([name, size, description])

        Output.print_table(headers, rows)

        if len(models) > 20:
            Output.print_info(f"\n... and {len(models) - 20} more models")

        Output.print_info("\nTo pull a model: aicode ollama pull <model_name>")
        return 0

    except Exception as e:
        Output.print_error(f"Failed to search models: {e}")
        return 1


def handle_remove(args):
    """删除本地模型"""
    try:
        # 确认删除
        if not args.yes:
            Output.print_warning(f"About to delete model: {args.model_name}")
            confirm = input("Continue? (y/N): ").strip().lower()
            if confirm != "y":
                Output.print_info("Cancelled")
                return 0

        ollama_utils.delete_model(args.model_name)
        Output.print_success(f"Model {args.model_name} deleted successfully")
        return 0

    except Exception as e:
        Output.print_error(f"Failed to delete model: {e}")
        return 1


def handle_status(args):
    """检查 Ollama 服务状态"""
    try:
        is_available = ollama_utils.is_ollama_available()

        if is_available:
            Output.print_success("Ollama is running")
            Output.print_info("Service URL: http://localhost:11434")

            # 显示已安装的模型数量
            models = ollama_utils.list_local_models()
            Output.print_info(f"Installed models: {len(models)}")

            return 0
        else:
            Output.print_error("Ollama is not running")
            Output.print_info("\nStart Ollama:")
            print("  ollama serve")
            Output.print_info("\nOr install Ollama:")
            print("  macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh")
            print("  Windows: https://ollama.com/download/windows")
            return 1

    except Exception as e:
        Output.print_error(f"Failed to check status: {e}")
        return 1


def handle_info(args):
    """显示模型详细信息"""
    try:
        info = ollama_utils.show_model_info(args.model_name)

        Output.print_header(f"Model: {args.model_name}")

        # 显示模型信息
        if "modelfile" in info:
            print("\nModelfile:")
            print(info["modelfile"])

        if "parameters" in info:
            print("\nParameters:")
            print(info["parameters"])

        if "template" in info:
            print("\nTemplate:")
            print(info["template"][:200])  # 截断显示

        return 0

    except Exception as e:
        Output.print_error(f"Failed to get model info: {e}")
        return 1


def _format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化后的大小（如 "4.7GB"）
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


def setup_parser(subparsers):
    """
    设置 ollama 命令解析器

    Args:
        subparsers: 子命令解析器
    """
    ollama_parser = subparsers.add_parser(
        "ollama", help="Manage Ollama models", description="Manage local Ollama models"
    )

    ollama_subparsers = ollama_parser.add_subparsers(
        dest="ollama_command", help="Ollama subcommands"
    )

    # list 子命令
    list_parser = ollama_subparsers.add_parser(
        "list", help="List installed models", aliases=["ls"]
    )
    list_parser.set_defaults(func=handle_list)

    # pull 子命令
    pull_parser = ollama_subparsers.add_parser(
        "pull", help="Download a model from Ollama library"
    )
    pull_parser.add_argument("model_name", help="Model name (e.g., llama2:13b)")
    pull_parser.set_defaults(func=handle_pull)

    # search 子命令
    search_parser = ollama_subparsers.add_parser(
        "search", help="Search available models"
    )
    search_parser.add_argument(
        "keyword", nargs="?", help="Search keyword (optional)", default=None
    )
    search_parser.set_defaults(func=handle_search)

    # remove 子命令
    remove_parser = ollama_subparsers.add_parser(
        "remove", help="Delete a local model", aliases=["rm"]
    )
    remove_parser.add_argument("model_name", help="Model name to delete")
    remove_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation"
    )
    remove_parser.set_defaults(func=handle_remove)

    # status 子命令
    status_parser = ollama_subparsers.add_parser(
        "status", help="Check Ollama service status"
    )
    status_parser.set_defaults(func=handle_status)

    # info 子命令
    info_parser = ollama_subparsers.add_parser(
        "info", help="Show detailed model information"
    )
    info_parser.add_argument("model_name", help="Model name")
    info_parser.set_defaults(func=handle_info)
