"""
session 命令 - 管理对话会话
"""
import argparse
from aicode.llm.session import SessionManager
from aicode.cli.utils.output import Output
from aicode.llm.exceptions import ConfigError
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


def setup_parser(subparsers) -> argparse.ArgumentParser:
    """
    设置session命令的参数解析器

    Args:
        subparsers: 子命令解析器

    Returns:
        ArgumentParser: session命令的解析器
    """
    parser = subparsers.add_parser(
        'session',
        help='Manage chat sessions',
        description='List, show, or delete conversation sessions'
    )

    session_subparsers = parser.add_subparsers(dest='session_command', help='Session commands')

    # list 子命令
    list_parser = session_subparsers.add_parser('list', help='List all sessions')
    list_parser.set_defaults(func=execute_list)

    # show 子命令
    show_parser = session_subparsers.add_parser('show', help='Show session details')
    show_parser.add_argument('session_id', type=str, help='Session ID')
    show_parser.add_argument('-n', '--num-messages', type=int, help='Number of messages to show')
    show_parser.set_defaults(func=execute_show)

    # delete 子命令
    delete_parser = session_subparsers.add_parser('delete', help='Delete a session')
    delete_parser.add_argument('session_id', type=str, help='Session ID')
    delete_parser.set_defaults(func=execute_delete)

    # clear 子命令
    clear_parser = session_subparsers.add_parser('clear', help='Clear all sessions')
    clear_parser.set_defaults(func=execute_clear)

    parser.set_defaults(func=lambda args: parser.print_help())
    return parser


def execute_list(args: argparse.Namespace) -> int:
    """列出所有会话"""
    try:
        sm = SessionManager()
        sessions = sm.list_sessions()

        if not sessions:
            Output.print_warning("No sessions found.")
            Output.print_info("Start a chat to create a session: aicode chat --new")
            return 0

        # 准备表格数据
        headers = ['ID', 'Title', 'Model', 'Messages', 'Updated']
        rows = []

        for session in sessions:
            # 格式化时间（只显示日期和时间）
            updated = session.updated_at[:19].replace('T', ' ')

            rows.append([
                session.session_id,
                session.title[:30] + '...' if len(session.title) > 30 else session.title,
                session.model,
                str(session.get_message_count()),
                updated
            ])

        Output.print_table(headers, rows)
        Output.print_info(f"Total: {len(sessions)} session(s)")
        Output.print_info("Use 'aicode session show <id>' to view details")
        return 0

    except Exception as e:
        Output.print_error(f"Failed to list sessions: {e}")
        logger.exception("Error in session list command")
        return 1


def execute_show(args: argparse.Namespace) -> int:
    """显示会话详情"""
    try:
        sm = SessionManager()
        session = sm.load_session(args.session_id)

        Output.print_header(f"Session: {session.session_id}")
        print(f"Title: {session.title}")
        print(f"Model: {session.model}")
        print(f"Messages: {session.get_message_count()}")
        print(f"Created: {session.created_at[:19].replace('T', ' ')}")
        print(f"Updated: {session.updated_at[:19].replace('T', ' ')}")

        # 显示消息
        Output.print_separator()
        Output.print_bold("Conversation:")
        print()

        # 确定显示多少条消息
        if args.num_messages:
            messages = session.messages[-args.num_messages:]
            if len(session.messages) > args.num_messages:
                Output.print_info(f"Showing last {args.num_messages} messages")
        else:
            messages = session.messages

        # 显示每条消息
        for i, msg in enumerate(messages, 1):
            role = msg['role'].upper()
            content = msg['content']

            if role == 'USER':
                Output.print_info(f"\n[{role}]")
            elif role == 'ASSISTANT':
                Output.print_success(f"\n[{role}]")
            else:
                Output.print_warning(f"\n[{role}]")

            print(content)

        Output.print_separator()
        Output.print_info("Use 'aicode chat --session <id>' to continue this conversation")
        return 0

    except ConfigError as e:
        Output.print_error(str(e))
        return 1
    except Exception as e:
        Output.print_error(f"Failed to show session: {e}")
        logger.exception("Error in session show command")
        return 1


def execute_delete(args: argparse.Namespace) -> int:
    """删除会话"""
    try:
        sm = SessionManager()

        # 确认删除
        if not Output.confirm(f"Delete session '{args.session_id}'?"):
            Output.print_info("Cancelled.")
            return 0

        sm.delete_session(args.session_id)
        Output.print_success(f"Deleted session: {args.session_id}")
        return 0

    except ConfigError as e:
        Output.print_error(str(e))
        return 1
    except Exception as e:
        Output.print_error(f"Failed to delete session: {e}")
        logger.exception("Error in session delete command")
        return 1


def execute_clear(args: argparse.Namespace) -> int:
    """清除所有会话"""
    try:
        sm = SessionManager()

        # 确认清除
        if not Output.confirm("Delete ALL sessions?", default=False):
            Output.print_info("Cancelled.")
            return 0

        count = sm.clear_all_sessions()
        Output.print_success(f"Cleared {count} session(s)")
        return 0

    except Exception as e:
        Output.print_error(f"Failed to clear sessions: {e}")
        logger.exception("Error in session clear command")
        return 1


def execute(args: argparse.Namespace) -> int:
    """
    执行session命令（路由到子命令）

    Args:
        args: 命令行参数

    Returns:
        int: 退出码
    """
    if hasattr(args, 'func') and args.func != execute:
        return args.func(args)
    else:
        Output.print_error("Please specify a subcommand: list, show, delete, or clear")
        return 1
