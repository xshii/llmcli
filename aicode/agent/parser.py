"""
混合格式解析器 - 支持 XML 和 Function Calling 格式
"""
import re
import json
from typing import List, Union
from aicode.agent.actions import (
    Action, CodeEditAction, BashAction,
    FileReadAction, FileWriteAction
)
from aicode.llm.code_edit import CodeEditParser
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class HybridParser:
    """混合格式解析器，支持多种响应格式"""

    # Bash 命令的 XML 模式
    BASH_PATTERN = re.compile(
        r'<bash_command(?:\s+description="([^"]*)")?\s*>\s*([^<]+)\s*</bash_command>',
        re.DOTALL
    )

    # 文件读取模式
    READ_FILE_PATTERN = re.compile(
        r'<read_file\s+path="([^"]+)"\s*/>'
    )

    # 文件写入模式
    WRITE_FILE_PATTERN = re.compile(
        r'<write_file\s+path="([^"]+)"(?:\s+description="([^"]*)")?\s*>\s*'
        r'```(?:\w+)?\s*\n(.*?)\n```\s*'
        r'</write_file>',
        re.DOTALL
    )

    @classmethod
    def parse_xml(cls, text: str) -> List[Action]:
        """
        解析 XML 格式的响应

        Args:
            text: AI 响应文本

        Returns:
            List[Action]: 动作列表
        """
        actions = []

        # 1. 解析代码编辑
        code_edits = CodeEditParser.parse(text)
        for edit in code_edits:
            actions.append(CodeEditAction(
                file_path=edit.file_path,
                content=edit.new_content,
                edit_type=edit.edit_type,
                description=edit.description,
                requires_confirmation=True
            ))
            logger.debug(f"Parsed CodeEditAction: {edit.file_path}")

        # 2. 解析 bash 命令
        for match in cls.BASH_PATTERN.finditer(text):
            description = match.group(1) or ""
            command = match.group(2).strip()

            is_dangerous = cls._is_dangerous_command(command)

            actions.append(BashAction(
                command=command,
                description=description,
                requires_confirmation=is_dangerous
            ))
            logger.debug(f"Parsed BashAction: {command[:50]}")

        # 3. 解析文件读取
        for match in cls.READ_FILE_PATTERN.finditer(text):
            file_path = match.group(1)
            actions.append(FileReadAction(
                file_path=file_path,
                description=f"Read {file_path}",
                requires_confirmation=False
            ))
            logger.debug(f"Parsed FileReadAction: {file_path}")

        # 4. 解析文件写入
        for match in cls.WRITE_FILE_PATTERN.finditer(text):
            file_path = match.group(1)
            description = match.group(2) or ""
            content = match.group(3)

            actions.append(FileWriteAction(
                file_path=file_path,
                content=content,
                description=description,
                requires_confirmation=True
            ))
            logger.debug(f"Parsed FileWriteAction: {file_path}")

        return actions

    @classmethod
    def parse_function_calling(cls, response) -> List[Action]:
        """
        解析 Function Calling 格式的响应（Anthropic 风格）

        Args:
            response: API 响应对象

        Returns:
            List[Action]: 动作列表
        """
        actions = []

        # 检查是否有 content 属性
        if not hasattr(response, 'content'):
            return actions

        for block in response.content:
            if hasattr(block, 'type') and block.type == 'tool_use':
                action = cls._convert_tool_to_action(block)
                if action:
                    actions.append(action)
                    logger.debug(f"Parsed {action.action_type.value}: {action.description}")

        return actions

    @classmethod
    def parse_json(cls, data: Union[str, dict]) -> List[Action]:
        """
        解析 JSON 格式的响应

        Args:
            data: JSON 字符串或字典

        Returns:
            List[Action]: 动作列表
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response")
                return []

        actions = []

        if isinstance(data, dict):
            # 单个动作
            action = cls._dict_to_action(data)
            if action:
                actions.append(action)
        elif isinstance(data, list):
            # 多个动作
            for item in data:
                action = cls._dict_to_action(item)
                if action:
                    actions.append(action)

        return actions

    @classmethod
    def parse(cls, response: Union[str, object]) -> List[Action]:
        """
        智能解析响应，自动检测格式

        Args:
            response: 响应对象或文本

        Returns:
            List[Action]: 动作列表
        """
        actions = []

        # 1. 检查 Function Calling 格式（Anthropic）
        if hasattr(response, 'content'):
            fc_actions = cls.parse_function_calling(response)
            actions.extend(fc_actions)

            # 同时检查文本内容中的 XML
            for block in response.content:
                if hasattr(block, 'text'):
                    xml_actions = cls.parse_xml(block.text)
                    actions.extend(xml_actions)

            return actions

        # 2. 纯文本响应
        if isinstance(response, str):
            # 尝试 JSON
            if response.strip().startswith('{') or response.strip().startswith('['):
                try:
                    json_actions = cls.parse_json(response)
                    if json_actions:
                        return json_actions
                except:
                    pass

            # 尝试 XML
            xml_actions = cls.parse_xml(response)
            return xml_actions

        return actions

    @classmethod
    def _convert_tool_to_action(cls, tool_call) -> Action:
        """将 Function Call 转换为 Action"""
        tool_name = tool_call.name
        tool_input = tool_call.input

        if tool_name == "edit_file" or tool_name == "code_edit":
            return CodeEditAction(
                file_path=tool_input.get("file_path", ""),
                content=tool_input.get("content", ""),
                edit_type=tool_input.get("edit_type", "modify"),
                description=tool_input.get("description", ""),
                requires_confirmation=True
            )

        elif tool_name == "bash" or tool_name == "execute_command":
            command = tool_input.get("command", "")
            return BashAction(
                command=command,
                description=tool_input.get("description", ""),
                timeout=tool_input.get("timeout", 30),
                requires_confirmation=cls._is_dangerous_command(command)
            )

        elif tool_name == "read_file":
            return FileReadAction(
                file_path=tool_input.get("file_path", ""),
                description=tool_input.get("description", ""),
                requires_confirmation=False
            )

        elif tool_name == "write_file":
            return FileWriteAction(
                file_path=tool_input.get("file_path", ""),
                content=tool_input.get("content", ""),
                description=tool_input.get("description", ""),
                requires_confirmation=True
            )

        logger.warning(f"Unknown tool: {tool_name}")
        return None

    @classmethod
    def _dict_to_action(cls, data: dict) -> Action:
        """将字典转换为 Action"""
        action_type = data.get('action_type') or data.get('type')

        if action_type in ['code_edit', 'edit_file']:
            return CodeEditAction(
                file_path=data.get('file_path', ''),
                content=data.get('content', ''),
                edit_type=data.get('edit_type', 'modify'),
                description=data.get('description', ''),
                requires_confirmation=True
            )

        elif action_type == 'bash':
            command = data.get('command', '')
            return BashAction(
                command=command,
                description=data.get('description', ''),
                requires_confirmation=cls._is_dangerous_command(command)
            )

        elif action_type == 'read_file':
            return FileReadAction(
                file_path=data.get('file_path', ''),
                description=data.get('description', ''),
                requires_confirmation=False
            )

        elif action_type == 'write_file':
            return FileWriteAction(
                file_path=data.get('file_path', ''),
                content=data.get('content', ''),
                description=data.get('description', ''),
                requires_confirmation=True
            )

        return None

    @classmethod
    def _is_dangerous_command(cls, command: str) -> bool:
        """判断命令是否危险"""
        dangerous_patterns = [
            r'rm\s+-rf\s+/',     # 删除根目录
            r'rm\s+-rf\s+\*',    # 删除所有文件
            r'sudo\s+rm',        # sudo 删除
            r'>(>)?\s*/dev/',    # 写入设备
            r'dd\s+if=',         # dd 命令
            r'mkfs',             # 格式化
            r'fdisk',            # 分区
            r':\(\)\{.*\|\:',    # Fork bomb
            r'chmod\s+-R\s+777', # 危险权限
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        return False
