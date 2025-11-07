"""
Action 数据类 - 统一的动作抽象
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ActionType(Enum):
    """动作类型枚举"""
    CODE_EDIT = "code_edit"
    BASH = "bash"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    SEARCH = "search"


@dataclass
class Action:
    """动作基类"""
    description: str
    action_type: Optional[ActionType] = None
    requires_confirmation: bool = True

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'action_type': self.action_type.value if self.action_type else None,
            'description': self.description,
            'requires_confirmation': self.requires_confirmation
        }


@dataclass
class CodeEditAction(Action):
    """代码编辑动作"""
    file_path: str = ""
    content: str = ""
    edit_type: str = "modify"  # modify, create, delete

    def __post_init__(self):
        if self.action_type is None:
            self.action_type = ActionType.CODE_EDIT

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'file_path': self.file_path,
            'content': self.content,
            'edit_type': self.edit_type
        })
        return base


@dataclass
class BashAction(Action):
    """Bash 命令动作"""
    command: str = ""
    timeout: int = 30
    working_dir: str = "."

    def __post_init__(self):
        if self.action_type is None:
            self.action_type = ActionType.BASH

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'command': self.command,
            'timeout': self.timeout,
            'working_dir': self.working_dir
        })
        return base


@dataclass
class FileReadAction(Action):
    """文件读取动作"""
    file_path: str = ""

    def __post_init__(self):
        if self.action_type is None:
            self.action_type = ActionType.FILE_READ
        self.requires_confirmation = False  # 读取是安全的

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'file_path': self.file_path
        })
        return base


@dataclass
class FileWriteAction(Action):
    """文件写入动作"""
    file_path: str = ""
    content: str = ""

    def __post_init__(self):
        if self.action_type is None:
            self.action_type = ActionType.FILE_WRITE

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'file_path': self.file_path,
            'content': self.content
        })
        return base
