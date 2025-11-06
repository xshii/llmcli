"""
交互式会话 - REPL 模式
"""
import sys
from typing import List, Dict, Optional
from aicode.database.db_manager import DatabaseManager
from aicode.config.config_manager import ConfigManager
from aicode.llm.client import LLMClient
from aicode.llm.session import SessionManager
from aicode.cli.utils.output import Output
from aicode.config.constants import DEFAULT_DB_PATH, VERSION
from aicode.llm.exceptions import ModelNotFoundError, APIError
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class InteractiveSession:
    """交互式会话"""

    def __init__(self):
        """初始化交互式会话"""
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager(DEFAULT_DB_PATH)
        self.session_manager = SessionManager()

        self.current_session = None
        self.current_model = None
        self.client = None
        self.messages: List[Dict[str, str]] = []

        # 加载配置
        if not self.config_manager.config_exists():
            Output.print_error("Config not found. Please run 'aicode config init' first.")
            sys.exit(1)

        self.config_manager.load()
        logger.debug("Interactive session initialized")

    def print_welcome(self):
        """打印欢迎信息"""
        Output.print_header(f"AICode Interactive Session v{VERSION}")
        print("Type your message to chat with AI")
        print("Special commands:")
        print("  /help     - Show help")
        print("  /model    - Show or change model")
        print("  /clear    - Clear conversation history")
        print("  /save     - Save current conversation")
        print("  /exit     - Exit interactive mode")
        print()

    def setup_model(self, model_name: Optional[str] = None):
        """
        设置当前使用的模型

        Args:
            model_name: 模型名称
        """
        if not model_name:
            model_name = self.config_manager.get('global.default_model')

        if not model_name:
            Output.print_error("No model specified.")
            Output.print_info("Available models: /model list")
            return False

        try:
            self.current_model = self.db_manager.get_model(model_name)

            # 获取API配置
            api_key = self.config_manager.get('global.api_key') or self.current_model.api_key
            api_url = self.config_manager.get('global.api_url') or self.current_model.api_url

            if not api_key:
                Output.print_error("API key not configured.")
                return False

            # 创建客户端
            self.client = LLMClient(self.current_model, api_key=api_key, api_url=api_url)

            Output.print_success(f"Using model: {self.current_model.name}")

            # 创建新会话
            self.current_session = self.session_manager.create_session(model_name)
            Output.print_info(f"Session ID: {self.current_session.session_id}")

            return True

        except ModelNotFoundError:
            Output.print_error(f"Model '{model_name}' not found.")
            Output.print_info("List available models with: /model list")
            return False

    def handle_command(self, command: str) -> bool:
        """
        处理特殊命令

        Args:
            command: 命令字符串（以/开头）

        Returns:
            bool: 是否继续会话（False表示退出）
        """
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == '/exit' or cmd == '/quit':
            return False

        elif cmd == '/help':
            self.show_help()

        elif cmd == '/model':
            if len(parts) > 1:
                if parts[1] == 'list':
                    self.list_models()
                else:
                    # 切换模型
                    self.setup_model(parts[1])
            else:
                # 显示当前模型
                if self.current_model:
                    Output.print_info(f"Current model: {self.current_model.name}")
                else:
                    Output.print_warning("No model selected")

        elif cmd == '/clear':
            self.messages.clear()
            if self.current_session:
                self.current_session.messages.clear()
            Output.print_success("Conversation cleared")

        elif cmd == '/save':
            if self.current_session:
                self.session_manager.save_session(self.current_session)
                Output.print_success(f"Session saved: {self.current_session.session_id}")
            else:
                Output.print_warning("No active session")

        elif cmd == '/history':
            self.show_history()

        elif cmd == '/info':
            self.show_info()

        else:
            Output.print_warning(f"Unknown command: {cmd}")
            Output.print_info("Type /help for available commands")

        return True

    def show_help(self):
        """显示帮助信息"""
        Output.print_header("Available Commands")
        print("/help              - Show this help message")
        print("/model [name]      - Show current model or switch to [name]")
        print("/model list        - List available models")
        print("/clear             - Clear conversation history")
        print("/save              - Save current session")
        print("/history           - Show conversation history")
        print("/info              - Show session info")
        print("/exit, /quit       - Exit interactive mode")
        print()

    def list_models(self):
        """列出可用模型"""
        models = self.db_manager.list_models()
        if not models:
            Output.print_warning("No models found")
            return

        headers = ['Name', 'Provider', 'Code Score']
        rows = []
        for model in models:
            rows.append([
                model.name,
                model.provider,
                f"{model.code_score:.1f}" if model.code_score else '-'
            ])

        Output.print_table(headers, rows)

    def show_history(self):
        """显示对话历史"""
        if not self.messages:
            Output.print_warning("No conversation history")
            return

        Output.print_separator()
        for msg in self.messages:
            role = msg['role'].upper()
            content = msg['content']

            if role == 'USER':
                Output.print_info(f"\n[{role}]")
            else:
                Output.print_success(f"\n[{role}]")

            print(content)

        Output.print_separator()

    def show_info(self):
        """显示会话信息"""
        if not self.current_model:
            Output.print_warning("No model selected")
            return

        Output.print_header("Session Info")
        print(f"Model: {self.current_model.name}")
        print(f"Provider: {self.current_model.provider}")
        if self.current_session:
            print(f"Session ID: {self.current_session.session_id}")
        print(f"Messages: {len(self.messages)}")

        if self.messages:
            token_count = self.client.count_message_tokens(self.messages)
            print(f"Tokens: {token_count}")

            cost = self.client.estimate_cost(self.messages)
            if cost:
                print(f"Estimated cost: ${cost:.6f}")

    def chat(self, user_input: str):
        """
        发送对话

        Args:
            user_input: 用户输入
        """
        if not self.client or not self.current_model:
            Output.print_error("No model selected. Use /model <name> to select a model.")
            return

        # 添加用户消息
        self.messages.append({
            'role': 'user',
            'content': user_input
        })

        if self.current_session:
            self.current_session.add_message('user', user_input)

        try:
            # 发送请求
            response = self.client.chat(self.messages, temperature=0.7)

            # 添加助手回复
            self.messages.append({
                'role': 'assistant',
                'content': response
            })

            if self.current_session:
                self.current_session.add_message('assistant', response)
                # 自动保存
                self.session_manager.save_session(self.current_session)

            # 显示回复
            Output.print_separator()
            print(response)
            Output.print_separator()

        except APIError as e:
            Output.print_error(f"API error: {e}")
            # 移除失败的用户消息
            self.messages.pop()
            if self.current_session:
                self.current_session.messages.pop()

    def run(self):
        """运行交互式会话"""
        self.print_welcome()

        # 初始化模型
        if not self.setup_model():
            Output.print_error("Failed to initialize model. Exiting.")
            return 1

        print()
        Output.print_success("Ready! Start chatting or type /help for commands")
        print()

        # 主循环
        try:
            while True:
                try:
                    # 读取用户输入
                    user_input = input("\n> ").strip()

                    if not user_input:
                        continue

                    # 处理特殊命令
                    if user_input.startswith('/'):
                        if not self.handle_command(user_input):
                            # 退出命令
                            break
                    else:
                        # 普通对话
                        self.chat(user_input)

                except EOFError:
                    # Ctrl+D
                    print()
                    break

        except KeyboardInterrupt:
            # Ctrl+C
            print()
            Output.print_info("Interrupted by user")

        # 保存会话
        if self.current_session and self.messages:
            self.session_manager.save_session(self.current_session)
            Output.print_success(f"Session saved: {self.current_session.session_id}")

        Output.print_info("Goodbye!")
        return 0


def start_interactive():
    """启动交互式会话"""
    session = InteractiveSession()
    return session.run()
