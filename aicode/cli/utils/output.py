"""
CLI输出格式化工具
"""

import sys
from typing import Any, Dict, List, Optional


class Output:
    """CLI输出工具"""

    @staticmethod
    def print_success(message: str) -> None:
        """打印成功消息（绿色）"""
        print(f"\033[32m✓ {message}\033[0m")

    @staticmethod
    def print_error(message: str) -> None:
        """打印错误消息（红色）"""
        print(f"\033[31m✗ {message}\033[0m", file=sys.stderr)

    @staticmethod
    def print_warning(message: str) -> None:
        """打印警告消息（黄色）"""
        print(f"\033[33m⚠ {message}\033[0m")

    @staticmethod
    def print_info(message: str) -> None:
        """打印信息消息（蓝色）"""
        print(f"\033[34mℹ {message}\033[0m")

    @staticmethod
    def print_header(title: str) -> None:
        """打印标题"""
        print(f"\n\033[1m{title}\033[0m")
        print("=" * len(title))

    @staticmethod
    def print_table(headers: List[str], rows: List[List[Any]]) -> None:
        """
        打印表格

        Args:
            headers: 表头
            rows: 数据行
        """
        if not rows:
            Output.print_warning("No data to display")
            return

        # 计算每列的最大宽度
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # 打印表头
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        print(f"\n{header_line}")
        print("-" * len(header_line))

        # 打印数据行
        for row in rows:
            row_line = " | ".join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            )
            print(row_line)

        print()

    @staticmethod
    def print_dict(data: Dict[str, Any], indent: int = 0) -> None:
        """
        打印字典（格式化）

        Args:
            data: 字典数据
            indent: 缩进级别
        """
        prefix = "  " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                Output.print_dict(value, indent + 1)
            elif isinstance(value, list):
                print(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        Output.print_dict(item, indent + 1)
                    else:
                        print(f"{prefix}  - {item}")
            else:
                print(f"{prefix}{key}: {value}")

    @staticmethod
    def print_code(code: str, language: Optional[str] = None) -> None:
        """
        打印代码块

        Args:
            code: 代码内容
            language: 语言标识
        """
        print(f"\n```{language or ''}")
        print(code)
        print("```\n")

    @staticmethod
    def print_separator() -> None:
        """打印分隔线"""
        print("-" * 60)

    @staticmethod
    def print_bold(text: str) -> None:
        """打印粗体文本"""
        print(f"\033[1m{text}\033[0m")

    @staticmethod
    def confirm(prompt: str, default: bool = False) -> bool:
        """
        询问用户确认

        Args:
            prompt: 提示信息
            default: 默认值

        Returns:
            bool: 用户选择
        """
        suffix = " [Y/n]" if default else " [y/N]"
        response = input(prompt + suffix + " ").lower().strip()

        if not response:
            return default

        return response in ("y", "yes")

    @staticmethod
    def prompt(message: str, default: Optional[str] = None) -> str:
        """
        获取用户输入

        Args:
            message: 提示信息
            default: 默认值

        Returns:
            str: 用户输入
        """
        if default:
            message = f"{message} [{default}]"

        response = input(f"{message}: ").strip()
        return response if response else (default or "")
