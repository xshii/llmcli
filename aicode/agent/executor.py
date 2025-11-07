"""
动作执行器 - 执行各种 Action
"""
import subprocess
import os
from pathlib import Path
from typing import Dict, Any
from aicode.agent.actions import (
    Action, ActionType, CodeEditAction, BashAction,
    FileReadAction, FileWriteAction
)
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class ActionExecutor:
    """动作执行器"""

    def __init__(self, working_dir: str = "."):
        """
        初始化执行器

        Args:
            working_dir: 工作目录
        """
        self.working_dir = working_dir

    def execute(self, action: Action) -> Dict[str, Any]:
        """
        执行动作

        Args:
            action: 要执行的动作

        Returns:
            Dict: 执行结果
                - success: bool, 是否成功
                - output: str, 输出内容
                - error: str, 错误信息（如果有）
        """
        logger.info(f"Executing {action.action_type.value}: {action.description}")

        try:
            if action.action_type == ActionType.CODE_EDIT:
                return self._execute_code_edit(action)
            elif action.action_type == ActionType.BASH:
                return self._execute_bash(action)
            elif action.action_type == ActionType.FILE_READ:
                return self._execute_file_read(action)
            elif action.action_type == ActionType.FILE_WRITE:
                return self._execute_file_write(action)
            else:
                return {
                    'success': False,
                    'output': '',
                    'error': f'Unknown action type: {action.action_type}'
                }

        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }

    def _execute_code_edit(self, action: CodeEditAction) -> Dict[str, Any]:
        """执行代码编辑"""
        file_path = self._resolve_path(action.file_path)

        if action.edit_type == "delete":
            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)
                return {
                    'success': True,
                    'output': f'Deleted {file_path}',
                    'error': ''
                }
            else:
                return {
                    'success': False,
                    'output': '',
                    'error': f'File not found: {file_path}'
                }

        elif action.edit_type in ["create", "modify"]:
            # 创建或修改文件
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)

            # 写入内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(action.content)

            verb = "Created" if action.edit_type == "create" else "Modified"
            return {
                'success': True,
                'output': f'{verb} {file_path} ({len(action.content)} bytes)',
                'error': ''
            }

        else:
            return {
                'success': False,
                'output': '',
                'error': f'Unknown edit type: {action.edit_type}'
            }

    def _execute_bash(self, action: BashAction) -> Dict[str, Any]:
        """执行 bash 命令"""
        try:
            result = subprocess.run(
                action.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=action.timeout,
                cwd=self._resolve_path(action.working_dir)
            )

            success = result.returncode == 0
            output = result.stdout if result.stdout else result.stderr

            return {
                'success': success,
                'output': output,
                'error': '' if success else result.stderr,
                'exit_code': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f'Command timed out after {action.timeout} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }

    def _execute_file_read(self, action: FileReadAction) -> Dict[str, Any]:
        """执行文件读取"""
        file_path = self._resolve_path(action.file_path)

        if not os.path.exists(file_path):
            return {
                'success': False,
                'output': '',
                'error': f'File not found: {file_path}'
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'success': True,
                'output': content,
                'error': ''
            }

        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'Failed to read file: {e}'
            }

    def _execute_file_write(self, action: FileWriteAction) -> Dict[str, Any]:
        """执行文件写入"""
        file_path = self._resolve_path(action.file_path)

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)

            # 写入内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(action.content)

            return {
                'success': True,
                'output': f'Wrote {len(action.content)} bytes to {file_path}',
                'error': ''
            }

        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'Failed to write file: {e}'
            }

    def _resolve_path(self, path: str) -> str:
        """解析路径（支持相对路径）"""
        if os.path.isabs(path):
            return path
        return os.path.join(self.working_dir, path)
