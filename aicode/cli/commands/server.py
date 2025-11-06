"""
server 命令 - 启动 RPC Server
"""
import argparse
from aicode.server.rpc_server import RPCServer
from aicode.cli.utils.output import Output
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


def setup_parser(subparsers) -> argparse.ArgumentParser:
    """
    设置 server 命令的参数解析器

    Args:
        subparsers: 子命令解析器

    Returns:
        ArgumentParser: server 命令的解析器
    """
    parser = subparsers.add_parser(
        'server',
        help='Start RPC server for VSCode extension',
        description='Start JSON-RPC server for VSCode extension communication'
    )

    parser.add_argument(
        '--mode',
        choices=['stdio', 'tcp'],
        default='stdio',
        help='Server mode (default: stdio)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5555,
        help='TCP port (only for tcp mode, default: 5555)'
    )

    parser.set_defaults(func=execute)
    return parser


def execute(args: argparse.Namespace) -> int:
    """
    执行 server 命令

    Args:
        args: 命令行参数

    Returns:
        int: 退出码
    """
    try:
        if args.mode == 'stdio':
            Output.print_info("Starting RPC server in stdio mode...")
            server = RPCServer()
            server.run()
        else:
            Output.print_error("TCP mode not implemented yet")
            return 1

        return 0

    except KeyboardInterrupt:
        Output.print_info("\nServer stopped")
        return 0
    except Exception as e:
        Output.print_error(f"Failed to start server: {e}")
        logger.exception("Error in server command")
        return 1
