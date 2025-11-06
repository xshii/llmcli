"""
文件操作工具
"""
import os
from typing import List, Optional
from pathlib import Path
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class FileOperations:
    """文件操作工具类"""

    @staticmethod
    def read_file(file_path: str) -> str:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            str: 文件内容

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 无读取权限
        """
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Read file: {file_path} ({len(content)} chars)")
            return content
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(path, 'r', encoding='latin-1') as f:
                content = f.read()
            logger.warning(f"Read file with latin-1 encoding: {file_path}")
            return content

    @staticmethod
    def write_file(file_path: str, content: str) -> None:
        """
        写入文件

        Args:
            file_path: 文件路径
            content: 文件内容

        Raises:
            PermissionError: 无写入权限
        """
        path = Path(file_path).expanduser().resolve()

        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Wrote file: {file_path} ({len(content)} chars)")

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            file_path: 文件路径

        Returns:
            bool: 存在返回True
        """
        path = Path(file_path).expanduser().resolve()
        return path.exists() and path.is_file()

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        获取文件扩展名

        Args:
            file_path: 文件路径

        Returns:
            str: 扩展名（不含点号）
        """
        return Path(file_path).suffix.lstrip('.')

    @staticmethod
    def list_files(
        directory: str,
        pattern: Optional[str] = None,
        recursive: bool = False
    ) -> List[str]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件名模式（glob），如 "*.py"
            recursive: 是否递归搜索

        Returns:
            List[str]: 文件路径列表
        """
        path = Path(directory).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        if pattern:
            if recursive:
                files = path.rglob(pattern)
            else:
                files = path.glob(pattern)
        else:
            if recursive:
                files = path.rglob('*')
            else:
                files = path.glob('*')

        # 只返回文件，过滤目录
        result = [str(f) for f in files if f.is_file()]
        logger.debug(f"Listed {len(result)} files in {directory}")
        return sorted(result)

    @staticmethod
    def get_relative_path(file_path: str, base_dir: Optional[str] = None) -> str:
        """
        获取相对路径

        Args:
            file_path: 文件路径
            base_dir: 基准目录（默认为当前目录）

        Returns:
            str: 相对路径
        """
        file_path = Path(file_path).expanduser().resolve()

        if base_dir is None:
            base_dir = Path.cwd()
        else:
            base_dir = Path(base_dir).expanduser().resolve()

        try:
            return str(file_path.relative_to(base_dir))
        except ValueError:
            # 无法计算相对路径，返回绝对路径
            return str(file_path)

    @staticmethod
    def read_file_lines(
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> str:
        """
        读取文件的指定行

        Args:
            file_path: 文件路径
            start_line: 起始行号（从1开始，包含）
            end_line: 结束行号（包含）

        Returns:
            str: 指定行的内容
        """
        content = FileOperations.read_file(file_path)
        lines = content.splitlines()

        if start_line is not None:
            start_idx = max(0, start_line - 1)
        else:
            start_idx = 0

        if end_line is not None:
            end_idx = min(len(lines), end_line)
        else:
            end_idx = len(lines)

        selected_lines = lines[start_idx:end_idx]
        return '\n'.join(selected_lines)
