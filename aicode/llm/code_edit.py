"""
代码编辑 - 结构化的代码修改建议
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FileEdit:
    """单个文件的编辑操作"""

    file_path: str
    original_content: Optional[str] = None
    new_content: str = ""
    description: str = ""
    edit_type: str = "modify"  # modify, create, delete

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'file_path': self.file_path,
            'original_content': self.original_content,
            'new_content': self.new_content,
            'description': self.description,
            'edit_type': self.edit_type
        }


class CodeEditParser:
    """解析 AI 返回的代码编辑建议"""

    # AI 返回格式：
    # <file_edit path="src/main.py" type="modify" description="修复bug">
    # ```python
    # def hello():
    #     print("Hello, World!")
    # ```
    # </file_edit>

    EDIT_PATTERN = re.compile(
        r'<file_edit\s+path="([^"]+)"(?:\s+type="([^"]+)")?(?:\s+description="([^"]*)")?\s*>\s*'
        r'```(?:\w+)?\s*\n(.*?)\n```\s*'
        r'</file_edit>',
        re.DOTALL
    )

    # 污染标签模式（需要清理的内容）
    POLLUTION_PATTERNS = [
        r'<think>.*?</think>',
        r'<thinking>.*?</thinking>',
        r'<reflection>.*?</reflection>',
        r'<内部思考>.*?</内部思考>',
    ]

    @classmethod
    def parse(cls, text: str, auto_clean: bool = True) -> List[FileEdit]:
        """
        解析文本中的代码编辑建议

        Args:
            text: AI 返回的文本
            auto_clean: 是否自动清理污染标签（默认 True）

        Returns:
            List[FileEdit]: 编辑操作列表
        """
        # 自动清理污染标签
        if auto_clean:
            text = cls.clean_pollution(text)

        edits = []

        for match in cls.EDIT_PATTERN.finditer(text):
            file_path = match.group(1)
            edit_type = match.group(2) or 'modify'
            description = match.group(3) or ''
            new_content = match.group(4)

            edit = FileEdit(
                file_path=file_path,
                new_content=new_content,
                description=description,
                edit_type=edit_type
            )
            edits.append(edit)
            logger.debug(f"Parsed edit for {file_path}: {edit_type}")

        return edits

    @classmethod
    def clean_pollution(cls, text: str) -> str:
        """
        清理文本中的污染标签（如 DeepSeek 的 <think> 标签）

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        cleaned = text
        for pattern in cls.POLLUTION_PATTERNS:
            # 检查是否存在污染
            if re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE):
                logger.debug(f"Cleaning pollution pattern: {pattern}")
                cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        return cleaned

    @classmethod
    def format_edits_for_display(cls, edits: List[FileEdit]) -> str:
        """
        格式化编辑列表用于显示

        Args:
            edits: 编辑列表

        Returns:
            str: 格式化的文本
        """
        if not edits:
            return "No code edits found."

        lines = ["\n📝 Proposed Code Changes:\n"]

        for idx, edit in enumerate(edits, 1):
            lines.append(f"{idx}. {edit.file_path}")
            if edit.description:
                lines.append(f"   └─ {edit.description}")
            lines.append(f"   └─ Type: {edit.edit_type}")

        lines.append("\nTo apply changes:")
        lines.append("  - Type the number to apply that change")
        lines.append("  - Type 'all' to apply all changes")
        lines.append("  - Type 'skip' to skip")

        return "\n".join(lines)


class CodeEditPrompt:
    """生成引导 AI 返回结构化编辑的提示词"""

    SYSTEM_PROMPT = """When suggesting code changes, use this XML format:

<file_edit path="relative/path/to/file.py" type="modify" description="Brief description">
```python
# Complete updated file content or code block
```
</file_edit>

Rules:
1. Use absolute or relative file paths
2. Types: modify (edit existing), create (new file), delete (remove file)
3. Include complete code blocks, not just snippets
4. Add clear descriptions
5. Multiple edits = multiple <file_edit> tags

Example:
<file_edit path="src/main.py" type="modify" description="Add error handling">
```python
def main():
    try:
        result = process_data()
        print(result)
    except Exception as e:
        logger.error(f"Error: {e}")
```
</file_edit>
"""

    @classmethod
    def enhance_user_message(cls, message: str, context_files: List[str] = None) -> str:
        """
        增强用户消息，添加上下文提示

        Args:
            message: 用户原始消息
            context_files: 相关文件列表

        Returns:
            str: 增强后的消息
        """
        enhanced = message

        if context_files:
            files_list = "\n".join([f"- {f}" for f in context_files])
            enhanced += f"\n\nContext files:\n{files_list}"

        enhanced += "\n\nPlease provide code changes using the <file_edit> format."

        return enhanced


def create_inline_edit_prompt() -> str:
    """创建用于代码编辑的系统提示"""
    return CodeEditPrompt.SYSTEM_PROMPT
