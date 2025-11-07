#!/usr/bin/env python3
"""
测试统一 Agent 系统
"""
import os
import tempfile
import shutil
from aicode.agent import (
    Action, ActionType,
    CodeEditAction, BashAction,
    FileReadAction, FileWriteAction,
    UnifiedAgent
)
from aicode.agent.parser import HybridParser
from aicode.agent.executor import ActionExecutor


def test_actions():
    """测试 Action 数据类"""
    print("\n" + "=" * 60)
    print("TEST 1: Action Data Classes")
    print("=" * 60)

    # 测试 CodeEditAction
    action1 = CodeEditAction(
        file_path="test.py",
        content="print('hello')",
        edit_type="create",
        description="Create test file",
        requires_confirmation=True
    )
    assert action1.action_type == ActionType.CODE_EDIT
    assert action1.file_path == "test.py"
    print("✓ CodeEditAction created")

    # 测试 BashAction
    action2 = BashAction(
        command="echo 'test'",
        description="Echo test",
        requires_confirmation=False
    )
    assert action2.action_type == ActionType.BASH
    assert action2.command == "echo 'test'"
    print("✓ BashAction created")

    # 测试 to_dict
    data = action1.to_dict()
    assert data['action_type'] == 'code_edit'
    assert data['file_path'] == 'test.py'
    print("✓ to_dict() works")

    print()


def test_parser_xml():
    """测试 XML 格式解析"""
    print("\n" + "=" * 60)
    print("TEST 2: XML Format Parser")
    print("=" * 60)

    text = """
Here's the solution:

<file_edit path="src/main.py" type="modify" description="Add logging">
```python
import logging

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting...")
```
</file_edit>

<bash_command description="Run tests">
pytest tests/ -v
</bash_command>

<read_file path="config.yaml" />

Done!
"""

    actions = HybridParser.parse_xml(text)

    assert len(actions) >= 2, f"Expected at least 2 actions, got {len(actions)}"

    # 检查代码编辑
    code_actions = [a for a in actions if a.action_type == ActionType.CODE_EDIT]
    assert len(code_actions) >= 1, "Expected at least 1 code edit action"
    assert code_actions[0].file_path == "src/main.py"
    assert "logging" in code_actions[0].content
    print(f"✓ Parsed {len(code_actions)} code edit action(s)")

    # 检查 bash 命令
    bash_actions = [a for a in actions if a.action_type == ActionType.BASH]
    assert len(bash_actions) >= 1, "Expected at least 1 bash action"
    assert "pytest" in bash_actions[0].command
    print(f"✓ Parsed {len(bash_actions)} bash action(s)")

    # 检查文件读取
    read_actions = [a for a in actions if a.action_type == ActionType.FILE_READ]
    if read_actions:
        print(f"✓ Parsed {len(read_actions)} file read action(s)")

    print()


def test_dangerous_command_detection():
    """测试危险命令检测"""
    print("\n" + "=" * 60)
    print("TEST 3: Dangerous Command Detection")
    print("=" * 60)

    dangerous_commands = [
        "rm -rf /",
        "sudo rm -rf *",
        "dd if=/dev/zero of=/dev/sda",
        "chmod -R 777 /",
    ]

    safe_commands = [
        "ls -la",
        "pytest tests/",
        "git status",
        "python main.py",
    ]

    for cmd in dangerous_commands:
        is_dangerous = HybridParser._is_dangerous_command(cmd)
        assert is_dangerous, f"Should detect '{cmd}' as dangerous"
        print(f"✓ Detected dangerous: {cmd[:30]}")

    for cmd in safe_commands:
        is_dangerous = HybridParser._is_dangerous_command(cmd)
        assert not is_dangerous, f"Should detect '{cmd}' as safe"
        print(f"✓ Detected safe: {cmd}")

    print()


def test_executor():
    """测试动作执行器"""
    print("\n" + "=" * 60)
    print("TEST 4: Action Executor")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"Using temp directory: {temp_dir}")

    try:
        executor = ActionExecutor(working_dir=temp_dir)

        # 测试文件写入
        action1 = FileWriteAction(
            file_path="test.txt",
            content="Hello, World!",
            description="Write test file",
            requires_confirmation=False
        )
        result1 = executor.execute(action1)
        assert result1['success'], f"Write failed: {result1['error']}"
        print("✓ FileWriteAction executed")

        # 测试文件读取
        action2 = FileReadAction(
            file_path="test.txt",
            description="Read test file",
            requires_confirmation=False
        )
        result2 = executor.execute(action2)
        assert result2['success'], f"Read failed: {result2['error']}"
        assert result2['output'] == "Hello, World!"
        print("✓ FileReadAction executed")

        # 测试代码编辑（创建）
        action3 = CodeEditAction(
            file_path="src/main.py",
            content="def main():\n    pass\n",
            edit_type="create",
            description="Create main.py",
            requires_confirmation=True
        )
        result3 = executor.execute(action3)
        assert result3['success'], f"Create failed: {result3['error']}"
        print("✓ CodeEditAction (create) executed")

        # 测试 bash 命令
        action4 = BashAction(
            command="echo 'test'",
            description="Echo test",
            requires_confirmation=False
        )
        result4 = executor.execute(action4)
        assert result4['success'], f"Bash failed: {result4['error']}"
        assert 'test' in result4['output']
        print("✓ BashAction executed")

        # 测试文件列表
        action5 = BashAction(
            command="ls -la",
            description="List files",
            requires_confirmation=False
        )
        result5 = executor.execute(action5)
        assert result5['success'], f"Ls failed: {result5['error']}"
        assert 'test.txt' in result5['output']
        print("✓ BashAction (ls) executed")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"Cleaned up temp directory")

    print()


def test_parser_multiple_formats():
    """测试解析多种格式"""
    print("\n" + "=" * 60)
    print("TEST 5: Parse Multiple Formats")
    print("=" * 60)

    # 测试混合格式
    text = """
I'll help you with that.

First, let's create the file:

<file_edit path="app.py" type="create" description="Create Flask app">
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"
```
</file_edit>

Now let's install dependencies:

<bash_command description="Install Flask">
pip install flask
</bash_command>

And run it:

<bash_command description="Start server">
python app.py
</bash_command>

Done!
"""

    actions = HybridParser.parse_xml(text)

    print(f"Parsed {len(actions)} actions:")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action.action_type.value}: {action.description}")

    # 验证
    assert len(actions) == 3, f"Expected 3 actions, got {len(actions)}"

    code_actions = [a for a in actions if a.action_type == ActionType.CODE_EDIT]
    assert len(code_actions) == 1
    assert "Flask" in code_actions[0].content

    bash_actions = [a for a in actions if a.action_type == ActionType.BASH]
    assert len(bash_actions) == 2
    assert "pip install" in bash_actions[0].command
    assert "python app.py" in bash_actions[1].command

    print("✓ All formats parsed correctly")
    print()


def test_unified_agent_mock():
    """测试 UnifiedAgent（模拟 LLM 响应）"""
    print("\n" + "=" * 60)
    print("TEST 6: UnifiedAgent (Mock)")
    print("=" * 60)

    # 创建模拟的 LLM 客户端
    class MockLLMClient:
        class MockModel:
            name = "mock-model"
            supports_function_calling = False

        def __init__(self):
            self.model = self.MockModel()

        def chat(self, messages):
            # 返回包含动作的模拟响应
            return """
Here's what I'll do:

<file_edit path="test.py" type="create" description="Create test file">
```python
def test():
    print("Test")
```
</file_edit>

<bash_command description="Run test">
python test.py
</bash_command>
"""

    # 创建 agent
    client = MockLLMClient()
    agent = UnifiedAgent(client, working_dir=".")

    print(f"Agent created (FC support: {agent.supports_fc})")

    # 测试对话
    response_text, actions = agent.chat("Create a test file")

    print(f"Response: {response_text[:50]}...")
    print(f"Actions: {len(actions)}")

    assert len(actions) >= 1, "Expected at least 1 action"

    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action.action_type.value}: {action.description}")

    print("✓ UnifiedAgent chat works")
    print()


def test_integration():
    """集成测试：解析 + 执行"""
    print("\n" + "=" * 60)
    print("TEST 7: Integration Test (Parse + Execute)")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"Using temp directory: {temp_dir}")

    try:
        # 模拟 AI 响应
        ai_response = f"""
Let me create a simple Python script:

<file_edit path="hello.py" type="create" description="Create hello script">
```python
def greet(name):
    return f"Hello, {{name}}!"

if __name__ == "__main__":
    print(greet("World"))
```
</file_edit>

<bash_command description="Run the script">
python hello.py
</bash_command>
"""

        # 解析
        actions = HybridParser.parse_xml(ai_response)
        print(f"Parsed {len(actions)} actions")

        # 执行
        executor = ActionExecutor(working_dir=temp_dir)

        for i, action in enumerate(actions, 1):
            print(f"\nExecuting action {i}: {action.action_type.value}")
            result = executor.execute(action)

            if result['success']:
                print(f"  ✓ Success")
                if result['output']:
                    output_preview = result['output'][:100].replace('\n', ' ')
                    print(f"  Output: {output_preview}")
            else:
                print(f"  ✗ Failed: {result['error']}")

        # 验证文件创建
        hello_path = os.path.join(temp_dir, "hello.py")
        assert os.path.exists(hello_path), "hello.py should exist"
        print("\n✓ Integration test passed")

    finally:
        shutil.rmtree(temp_dir)
        print(f"Cleaned up temp directory")

    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("UNIFIED AGENT SYSTEM TESTS")
    print("=" * 60)

    try:
        test_actions()
        test_parser_xml()
        test_dangerous_command_detection()
        test_executor()
        test_parser_multiple_formats()
        test_unified_agent_mock()
        test_integration()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print()

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
