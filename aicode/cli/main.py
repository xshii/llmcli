"""
AICode CLI - 主入口
"""
import sys
import argparse
from typing import List, Optional
from aicode.config.constants import VERSION, PROJECT_NAME
from aicode.cli.commands import chat, model, config, session, server, probe
from aicode.cli.interactive import start_interactive
from aicode.cli.utils.output import Output
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """
    创建主参数解析器

    Returns:
        ArgumentParser: 主解析器
    """
    parser = argparse.ArgumentParser(
        prog='aicode',
        description='AICode - AI-powered coding assistant',
        epilog=f'Version {VERSION}'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'{PROJECT_NAME} {VERSION}'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    # 创建子命令
    subparsers = parser.add_subparsers(
        title='commands',
        description='Available commands',
        dest='command',
        help='Command to execute'
    )

    # 注册各个命令
    chat.setup_parser(subparsers)
    model.setup_parser(subparsers)
    config.setup_parser(subparsers)
    session.setup_parser(subparsers)
    server.setup_parser(subparsers)
    probe.setup_parser(subparsers)

    # interactive 命令
    interactive_parser = subparsers.add_parser(
        'interactive',
        help='Start interactive session',
        description='Start an interactive chat session (default if no command specified)'
    )
    interactive_parser.set_defaults(func=lambda args: start_interactive())

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """
    CLI主入口

    Args:
        argv: 命令行参数（用于测试）

    Returns:
        int: 退出码
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # 设置日志级别
    if args.debug:
        import logging
        logging.getLogger('aicode').setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # 如果没有指定命令，进入交互模式
    if not args.command:
        return start_interactive()

    # 执行命令
    try:
        if hasattr(args, 'func'):
            return args.func(args)
        else:
            parser.print_help()
            return 0
    except KeyboardInterrupt:
        Output.print_info("\nInterrupted by user.")
        return 130
    except Exception as e:
        Output.print_error(f"Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        return 1


def cli_entry():
    """
    CLI入口点（供setup.py使用）
    """
    sys.exit(main())


if __name__ == '__main__':
    sys.exit(main())
