"""
会话管理 - 对话历史管理
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from aicode.config.constants import DEFAULT_CONFIG_DIR
from aicode.llm.exceptions import ConfigError
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class Session:
    """对话会话"""

    def __init__(
        self,
        session_id: str,
        model: str,
        messages: Optional[List[Dict[str, str]]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        title: Optional[str] = None
    ):
        """
        初始化会话

        Args:
            session_id: 会话ID
            model: 使用的模型名称
            messages: 对话消息列表
            created_at: 创建时间
            updated_at: 更新时间
            title: 会话标题
        """
        self.session_id = session_id
        self.model = model
        self.messages = messages or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.title = title or f"Chat with {model}"

    def add_message(self, role: str, content: str) -> None:
        """
        添加消息

        Args:
            role: 角色（user/assistant/system）
            content: 消息内容
        """
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self.updated_at = datetime.now().isoformat()
        logger.debug(f"Added {role} message to session {self.session_id}")

    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """
        获取用于API调用的消息列表（移除timestamp）

        Returns:
            List[Dict]: 消息列表
        """
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in self.messages
        ]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'model': self.model,
            'messages': self.messages,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'title': self.title
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建会话"""
        return cls(
            session_id=data['session_id'],
            model=data['model'],
            messages=data.get('messages', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            title=data.get('title')
        )

    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self.messages)

    def get_last_message(self) -> Optional[Dict[str, str]]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None


class SessionManager:
    """会话管理器"""

    def __init__(self, sessions_dir: Optional[str] = None):
        """
        初始化会话管理器

        Args:
            sessions_dir: 会话存储目录
        """
        if sessions_dir is None:
            config_dir = Path(DEFAULT_CONFIG_DIR).expanduser()
            sessions_dir = config_dir / 'sessions'

        self.sessions_dir = Path(sessions_dir).expanduser()
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"SessionManager initialized at {self.sessions_dir}")

    def create_session(self, model: str, title: Optional[str] = None) -> Session:
        """
        创建新会话

        Args:
            model: 模型名称
            title: 会话标题

        Returns:
            Session: 新会话
        """
        # 生成会话ID（时间戳）
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        session = Session(session_id, model, title=title)
        self.save_session(session)
        logger.info(f"Created session: {session_id}")
        return session

    def save_session(self, session: Session) -> None:
        """
        保存会话

        Args:
            session: 会话对象
        """
        session_file = self.sessions_dir / f"{session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved session: {session.session_id}")

    def load_session(self, session_id: str) -> Session:
        """
        加载会话

        Args:
            session_id: 会话ID

        Returns:
            Session: 会话对象

        Raises:
            ConfigError: 会话不存在
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            raise ConfigError(f"Session '{session_id}' not found")

        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.debug(f"Loaded session: {session_id}")
        return Session.from_dict(data)

    def list_sessions(self) -> List[Session]:
        """
        列出所有会话

        Returns:
            List[Session]: 会话列表（按更新时间倒序）
        """
        sessions = []
        for session_file in self.sessions_dir.glob('*.json'):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append(Session.from_dict(data))
            except Exception as e:
                logger.warning(f"Failed to load session {session_file}: {e}")

        # 按更新时间倒序排序
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        logger.debug(f"Listed {len(sessions)} sessions")
        return sessions

    def delete_session(self, session_id: str) -> None:
        """
        删除会话

        Args:
            session_id: 会话ID

        Raises:
            ConfigError: 会话不存在
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            raise ConfigError(f"Session '{session_id}' not found")

        session_file.unlink()
        logger.info(f"Deleted session: {session_id}")

    def get_latest_session(self) -> Optional[Session]:
        """
        获取最新的会话

        Returns:
            Session: 最新会话，如果没有则返回None
        """
        sessions = self.list_sessions()
        return sessions[0] if sessions else None

    def session_exists(self, session_id: str) -> bool:
        """
        检查会话是否存在

        Args:
            session_id: 会话ID

        Returns:
            bool: 存在返回True
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        return session_file.exists()

    def clear_all_sessions(self) -> int:
        """
        清除所有会话

        Returns:
            int: 删除的会话数量
        """
        count = 0
        for session_file in self.sessions_dir.glob('*.json'):
            session_file.unlink()
            count += 1

        logger.info(f"Cleared {count} sessions")
        return count
