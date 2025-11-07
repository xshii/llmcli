#!/usr/bin/env python3
"""
测试代码编辑解析功能
"""
from aicode.llm.code_edit import CodeEditParser, create_inline_edit_prompt


def test_parse_single_edit():
    """测试解析单个编辑"""
    print("TEST 1: Parse Single Edit")
    print("=" * 50)

    text = '''
Here's the fix:

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

This should handle errors properly.
'''

    edits = CodeEditParser.parse(text)
    assert len(edits) == 1, f"Expected 1 edit, got {len(edits)}"

    edit = edits[0]
    assert edit.file_path == "src/main.py"
    assert edit.edit_type == "modify"
    assert edit.description == "Add error handling"
    assert "try:" in edit.new_content
    assert "except Exception" in edit.new_content

    print(f"✓ Parsed edit: {edit.file_path}")
    print(f"  Type: {edit.edit_type}")
    print(f"  Description: {edit.description}")
    print(f"  Content lines: {len(edit.new_content.split(chr(10)))}")
    print()


def test_parse_multiple_edits():
    """测试解析多个编辑"""
    print("TEST 2: Parse Multiple Edits")
    print("=" * 50)

    text = '''
I'll help you refactor:

<file_edit path="src/main.py" type="modify" description="Add logging">
```python
import logging

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting...")
```
</file_edit>

<file_edit path="src/config.py" type="create" description="Add config file">
```python
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(message)s"
```
</file_edit>

<file_edit path="tests/test_main.py" type="modify" description="Update tests">
```python
import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        main()
```
</file_edit>

Done!
'''

    edits = CodeEditParser.parse(text)
    assert len(edits) == 3, f"Expected 3 edits, got {len(edits)}"

    print(f"✓ Parsed {len(edits)} edits:")
    for i, edit in enumerate(edits, 1):
        print(f"  {i}. {edit.file_path} ({edit.edit_type})")
        print(f"     → {edit.description}")
    print()


def test_format_edits_display():
    """测试编辑显示格式化"""
    print("TEST 3: Format Edits for Display")
    print("=" * 50)

    text = '''
<file_edit path="src/main.py" type="modify" description="Fix bug">
```python
def main():
    pass
```
</file_edit>

<file_edit path="tests/test.py" type="create" description="Add tests">
```python
import unittest
```
</file_edit>
'''

    edits = CodeEditParser.parse(text)
    formatted = CodeEditParser.format_edits_for_display(edits)

    print(formatted)
    print()

    assert "1. src/main.py" in formatted
    assert "2. tests/test.py" in formatted
    assert "To apply changes:" in formatted
    print("✓ Formatting correct")
    print()


def test_system_prompt():
    """测试系统提示生成"""
    print("TEST 4: System Prompt Generation")
    print("=" * 50)

    prompt = create_inline_edit_prompt()

    assert "<file_edit" in prompt
    assert "path=" in prompt
    assert "type=" in prompt
    assert "description=" in prompt

    print("✓ System prompt generated")
    print(f"  Length: {len(prompt)} characters")
    print(f"\nPrompt preview:")
    print("-" * 50)
    print(prompt[:300] + "...")
    print()


def test_edge_cases():
    """测试边界情况"""
    print("TEST 5: Edge Cases")
    print("=" * 50)

    # 没有编辑
    text1 = "Just a normal response without any code edits."
    edits1 = CodeEditParser.parse(text1)
    assert len(edits1) == 0
    print("✓ Empty text handled")

    # 缺少 description
    text2 = '''
<file_edit path="file.py" type="modify">
```python
code
```
</file_edit>
'''
    edits2 = CodeEditParser.parse(text2)
    assert len(edits2) == 1
    assert edits2[0].description == ""
    print("✓ Missing description handled")

    # 缺少 type
    text3 = '''
<file_edit path="file.py" description="test">
```python
code
```
</file_edit>
'''
    edits3 = CodeEditParser.parse(text3)
    assert len(edits3) == 1
    assert edits3[0].edit_type == "modify"  # 默认值
    print("✓ Missing type defaults to 'modify'")

    print()


def test_to_dict():
    """测试转换为字典"""
    print("TEST 6: Convert to Dict")
    print("=" * 50)

    text = '''
<file_edit path="src/main.py" type="modify" description="Test">
```python
print("Hello")
```
</file_edit>
'''

    edits = CodeEditParser.parse(text)
    edit_dict = edits[0].to_dict()

    assert edit_dict['file_path'] == "src/main.py"
    assert edit_dict['edit_type'] == "modify"
    assert edit_dict['description'] == "Test"
    assert edit_dict['new_content'] == 'print("Hello")'

    print("✓ Dict conversion successful")
    print(f"  Keys: {list(edit_dict.keys())}")
    print()


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("CODE EDIT PARSER TESTS")
    print("=" * 50 + "\n")

    try:
        test_parse_single_edit()
        test_parse_multiple_edits()
        test_format_edits_display()
        test_system_prompt()
        test_edge_cases()
        test_to_dict()

        print("=" * 50)
        print("ALL TESTS PASSED! ✓")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
