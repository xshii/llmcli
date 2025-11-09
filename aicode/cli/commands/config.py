"""
config 命令 - 管理配置
重构后使用依赖注入，遵循依赖倒置原则
"""

import argparse

from aicode.cli.utils.output import Output
from aicode.infrastructure.di_container import get_container
from aicode.llm.exceptions import ConfigFileNotFoundError
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


def setup_parser(subparsers) -> argparse.ArgumentParser:
    """
    设置config命令的参数解析器

    Args:
        subparsers: 子命令解析器

    Returns:
        ArgumentParser: config命令的解析器
    """
    parser = subparsers.add_parser(
        "config",
        help="Manage configuration",
        description="Get, set, or show configuration",
    )

    config_subparsers = parser.add_subparsers(
        dest="config_command", help="Config commands"
    )

    # get 子命令
    get_parser = config_subparsers.add_parser("get", help="Get a config value")
    get_parser.add_argument("key", type=str, help="Config key (e.g., global.api_key)")
    get_parser.set_defaults(func=execute_get)

    # set 子命令
    set_parser = config_subparsers.add_parser("set", help="Set a config value")
    set_parser.add_argument("key", type=str, help="Config key")
    set_parser.add_argument("value", type=str, help="Config value")
    set_parser.set_defaults(func=execute_set)

    # show 子命令
    show_parser = config_subparsers.add_parser("show", help="Show all configuration")
    show_parser.set_defaults(func=execute_show)

    # init 子命令
    init_parser = config_subparsers.add_parser(
        "init", help="Initialize default configuration"
    )
    init_parser.set_defaults(func=execute_init)

    parser.set_defaults(func=lambda args: parser.print_help())
    return parser


def execute_get(args: argparse.Namespace) -> int:
    """获取配置值"""
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        config_repo = container.get_config_repository()

        if not config_repo.config_exists():
            Output.print_error("Config file not found.")
            Output.print_info("Initialize with: aicode config init")
            return 1

        config_repo.load()
        value = config_repo.get(args.key)

        if value is None:
            Output.print_warning(f"Key '{args.key}' not found.")
            return 1

        # 隐藏敏感信息
        if "key" in args.key.lower() or "secret" in args.key.lower():
            if isinstance(value, str) and len(value) > 8:
                value = value[:4] + "***" + value[-4:]

        print(value)
        return 0

    except Exception as e:
        Output.print_error(f"Failed to get config: {e}")
        logger.exception("Error in config get command")
        return 1


def execute_set(args: argparse.Namespace) -> int:
    """设置配置值"""
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        config_repo = container.get_config_repository()

        if not config_repo.config_exists():
            Output.print_warning("Config file not found, creating default config...")
            # 需要直接访问底层 ConfigManager 来创建默认配置
            from aicode.config.config_manager import ConfigManager

            cm = ConfigManager()
            cm.create_default_config()

        config_repo.load()
        config_repo.set(args.key, args.value)
        config_repo.save()

        Output.print_success(f"Set {args.key} = {args.value}")
        return 0

    except Exception as e:
        Output.print_error(f"Failed to set config: {e}")
        logger.exception("Error in config set command")
        return 1


def execute_show(args: argparse.Namespace) -> int:
    """显示所有配置"""
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        config_repo = container.get_config_repository()

        if not config_repo.config_exists():
            Output.print_error("Config file not found.")
            Output.print_info("Initialize with: aicode config init")
            return 1

        config_repo.load()

        Output.print_header("Configuration")

        # 隐藏敏感信息
        config_copy = _mask_sensitive_values(config_repo.get_all().copy())

        Output.print_dict(config_copy)
        return 0

    except Exception as e:
        Output.print_error(f"Failed to show config: {e}")
        logger.exception("Error in config show command")
        return 1


def execute_init(args: argparse.Namespace) -> int:
    """初始化默认配置"""
    try:
        # 使用依赖注入获取仓储
        container = get_container()
        config_repo = container.get_config_repository()

        if config_repo.config_exists():
            if not Output.confirm("Config file already exists. Overwrite?"):
                Output.print_info("Cancelled.")
                return 0

        # 需要直接访问底层 ConfigManager 来创建默认配置和获取路径
        from aicode.config.config_manager import ConfigManager

        cm = ConfigManager()
        cm.create_default_config()
        Output.print_success(f"Created config file at: {cm.config_path}")
        Output.print_info(
            "Set your API key with: aicode config set global.api_key YOUR_KEY"
        )
        return 0

    except Exception as e:
        Output.print_error(f"Failed to initialize config: {e}")
        logger.exception("Error in config init command")
        return 1


def _mask_sensitive_values(config: dict) -> dict:
    """
    隐藏配置中的敏感值

    Args:
        config: 配置字典

    Returns:
        dict: 处理后的配置
    """
    sensitive_keys = ["api_key", "secret", "password", "token"]

    for key, value in config.items():
        if isinstance(value, dict):
            config[key] = _mask_sensitive_values(value)
        elif isinstance(value, str):
            # 检查键名是否包含敏感关键字
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if len(value) > 8:
                    config[key] = value[:4] + "***" + value[-4:]
                else:
                    config[key] = "***"

    return config


def execute(args: argparse.Namespace) -> int:
    """
    执行config命令（路由到子命令）

    Args:
        args: 命令行参数

    Returns:
        int: 退出码
    """
    if hasattr(args, "func") and args.func != execute:
        return args.func(args)
    else:
        Output.print_error("Please specify a subcommand: get, set, show, or init")
        return 1
