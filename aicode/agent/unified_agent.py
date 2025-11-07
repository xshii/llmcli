"""
统一 Agent - 支持代码生成和命令执行
"""
from typing import List, Dict, Any, Optional
from aicode.agent.actions import Action
from aicode.agent.parser import HybridParser
from aicode.agent.executor import ActionExecutor
from aicode.llm.code_edit import CodeEditPrompt
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class UnifiedAgent:
    """
    统一的 AI Agent

    - 自动检测模型能力（FC vs Prompt Engineering）
    - 统一的动作抽象（代码编辑、命令执行等）
    - 支持多轮对话和结果反馈
    """

    def __init__(self, llm_client, working_dir: str = "."):
        """
        初始化 Agent

        Args:
            llm_client: LLM 客户端
            working_dir: 工作目录
        """
        self.client = llm_client
        self.working_dir = working_dir

        # 判断模型能力
        self.supports_fc = getattr(
            llm_client.model,
            'supports_function_calling',
            False
        )

        # 解析器和执行器
        self.parser = HybridParser()
        self.executor = ActionExecutor(working_dir)

        # 对话历史
        self.conversation_history = []

        logger.info(f"UnifiedAgent initialized (FC support: {self.supports_fc})")

    def chat(
        self,
        user_message: str,
        context_files: Optional[List[str]] = None
    ) -> tuple[str, List[Action]]:
        """
        与 AI 对话

        Args:
            user_message: 用户消息
            context_files: 上下文文件列表

        Returns:
            tuple: (AI响应文本, 动作列表)
        """
        # 构建消息
        if self.supports_fc:
            response_text, actions = self._chat_with_fc(user_message, context_files)
        else:
            response_text, actions = self._chat_with_prompt(user_message, context_files)

        logger.info(f"Chat completed: {len(actions)} actions proposed")
        return response_text, actions

    def _chat_with_fc(
        self,
        user_message: str,
        context_files: Optional[List[str]]
    ) -> tuple[str, List[Action]]:
        """使用 Function Calling 模式"""
        # 注意：这里需要实际的 FC API 实现
        # 目前 LLMClient 还没有实现 FC，这里提供接口

        # 定义工具
        tools = self._get_tool_definitions()

        # 构建消息
        messages = self.conversation_history + [
            {"role": "user", "content": user_message}
        ]

        # 调用 LLM（模拟）
        # 实际应该调用 client.chat_with_tools(messages, tools)
        # 这里先返回模拟响应
        logger.warning("Function Calling not fully implemented in LLMClient")

        response_text = f"[FC Mode] Processing: {user_message}"
        actions = []

        return response_text, actions

    def _chat_with_prompt(
        self,
        user_message: str,
        context_files: Optional[List[str]]
    ) -> tuple[str, List[Action]]:
        """使用 Prompt Engineering 模式（XML 标签）"""

        # 构建系统提示
        system_prompt = self._build_system_prompt()

        # 增强用户消息
        enhanced_message = CodeEditPrompt.enhance_user_message(
            user_message,
            context_files
        )

        # 添加 XML 格式说明
        enhanced_message += """

Please respond with actions using these formats:

CODE EDIT:
<file_edit path="file.py" type="modify" description="Description">
```python
code here
```
</file_edit>

BASH COMMAND:
<bash_command description="What this does">
command here
</bash_command>

FILE READ:
<read_file path="file.py" />

You can use multiple actions in one response."""

        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加历史对话
        messages.extend(self.conversation_history)

        # 添加当前用户消息
        messages.append({"role": "user", "content": enhanced_message})

        # 调用 LLM
        try:
            response_text = self.client.chat(messages)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"Error: {e}", []

        # 解析响应
        actions = self.parser.parse_xml(response_text)

        # 更新对话历史
        self.conversation_history.append(
            {"role": "user", "content": user_message}
        )
        self.conversation_history.append(
            {"role": "assistant", "content": response_text}
        )

        return response_text, actions

    def execute_action(self, action: Action) -> Dict[str, Any]:
        """
        执行单个动作

        Args:
            action: 要执行的动作

        Returns:
            Dict: 执行结果
        """
        return self.executor.execute(action)

    def execute_actions(self, actions: List[Action]) -> List[Dict[str, Any]]:
        """
        执行多个动作

        Args:
            actions: 动作列表

        Returns:
            List[Dict]: 执行结果列表
        """
        results = []
        for action in actions:
            result = self.execute_action(action)
            results.append(result)
        return results

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return """You are an intelligent coding assistant that can:
1. Edit and create code files
2. Execute bash commands
3. Read and analyze files
4. Search through codebases

You should suggest actions in a structured format using XML tags.
Be precise and helpful. Always explain what each action does."""

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取工具定义（用于 Function Calling）"""
        return [
            {
                "name": "edit_file",
                "description": "Edit or create a file with new content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "New file content"
                        },
                        "edit_type": {
                            "type": "string",
                            "enum": ["modify", "create", "delete"],
                            "description": "Type of edit"
                        },
                        "description": {
                            "type": "string",
                            "description": "What this edit does"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            },
            {
                "name": "bash",
                "description": "Execute bash commands",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        },
                        "description": {
                            "type": "string",
                            "description": "What this command does"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        ]

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
