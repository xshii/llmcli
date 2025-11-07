#!/usr/bin/env python3
"""
统一 Agent 使用示例
"""
from aicode.agent import UnifiedAgent
from aicode.agent.parser import HybridParser


def example_mock_llm_usage():
    """示例 1: 使用模拟 LLM 客户端"""
    print("\n" + "=" * 60)
    print("示例 1: 模拟 LLM 客户端")
    print("=" * 60)

    # 创建模拟客户端
    class MockLLMClient:
        class MockModel:
            name = "mock-gpt-4"
            supports_function_calling = False

        def __init__(self):
            self.model = self.MockModel()

        def chat(self, messages):
            # 模拟 AI 返回结构化的响应
            user_query = messages[-1]['content']

            if "Flask" in user_query or "web" in user_query:
                return """
我来帮你创建一个简单的 Flask Web 应用：

<file_edit path="app.py" type="create" description="创建 Flask 应用">
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Hello, World!",
        "status": "success"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```
</file_edit>

<file_edit path="requirements.txt" type="create" description="依赖文件">
```
flask==3.0.0
```
</file_edit>

<bash_command description="安装依赖">
pip install -r requirements.txt
</bash_command>

现在你可以运行 `python app.py` 来启动服务器。
"""
            else:
                return """
让我帮你分析一下项目：

<read_file path="README.md" />

<bash_command description="查看 Python 版本">
python --version
</bash_command>

<bash_command description="查看已安装的包">
pip list
</bash_command>
"""

    # 创建 agent
    client = MockLLMClient()
    agent = UnifiedAgent(client, working_dir=".")

    print(f"Agent 模式: {'Function Calling' if agent.supports_fc else 'Prompt Engineering'}")

    # 场景 1: 创建 Flask 应用
    print("\n用户: 帮我创建一个简单的 Flask Web 应用")
    response_text, actions = agent.chat("帮我创建一个简单的 Flask Web 应用")

    print(f"\n📋 AI 提出了 {len(actions)} 个动作：")
    for i, action in enumerate(actions, 1):
        print(f"{i}. [{action.action_type.value}] {action.description}")
        if hasattr(action, 'file_path'):
            print(f"   📄 文件: {action.file_path}")
        if hasattr(action, 'command'):
            print(f"   💻 命令: {action.command}")

    # 用户确认并执行
    print("\n用户选择: 执行前两个动作（创建文件）")
    for i, action in enumerate(actions[:2]):
        if action.requires_confirmation:
            print(f"\n执行动作 {i+1}...")
            result = agent.execute_action(action)
            if result['success']:
                print(f"✓ 成功: {result['output']}")
            else:
                print(f"✗ 失败: {result['error']}")

    print()


def example_parse_formats():
    """示例 2: 解析不同格式"""
    print("\n" + "=" * 60)
    print("示例 2: 解析不同格式的 AI 响应")
    print("=" * 60)

    # 格式 1: 混合 XML
    response1 = """
好的，我会帮你做以下操作：

1. 首先创建配置文件：

<file_edit path="config.yaml" type="create" description="创建配置文件">
```yaml
server:
  host: 0.0.0.0
  port: 8000

database:
  url: sqlite:///data.db
```
</file_edit>

2. 然后读取当前项目结构：

<bash_command description="列出项目文件">
tree -L 2 -I '__pycache__|*.pyc'
</bash_command>

3. 检查依赖：

<bash_command description="检查 Python 包">
pip list | grep -i flask
</bash_command>

完成！
"""

    print("\n格式 1: XML 混合文本")
    actions1 = HybridParser.parse_xml(response1)
    print(f"解析出 {len(actions1)} 个动作：")
    for action in actions1:
        print(f"  - {action.action_type.value}: {action.description}")

    # 格式 2: 纯代码块
    response2 = """
让我重构这个函数：

<file_edit path="utils.py" type="modify" description="重构 process_data 函数">
```python
def process_data(data: list) -> dict:
    \"\"\"处理数据并返回统计信息\"\"\"
    if not data:
        return {"count": 0, "sum": 0, "avg": 0}

    total = sum(data)
    count = len(data)
    avg = total / count

    return {
        "count": count,
        "sum": total,
        "avg": avg,
        "min": min(data),
        "max": max(data)
    }
```
</file_edit>

<bash_command description="运行测试">
pytest tests/test_utils.py -v
</bash_command>
"""

    print("\n格式 2: 代码重构")
    actions2 = HybridParser.parse_xml(response2)
    print(f"解析出 {len(actions2)} 个动作：")
    for action in actions2:
        print(f"  - {action.action_type.value}: {action.description}")

    print()


def example_safety_check():
    """示例 3: 安全检查"""
    print("\n" + "=" * 60)
    print("示例 3: 危险命令检测")
    print("=" * 60)

    dangerous_responses = [
        ("删除临时文件", "rm -rf /tmp/myapp/*"),
        ("清理日志", "rm -rf *.log"),
        ("格式化", "mkfs.ext4 /dev/sdb1"),
        ("递归修改权限", "chmod -R 777 /var/www"),
    ]

    safe_responses = [
        ("列出文件", "ls -la"),
        ("查看日志", "tail -f app.log"),
        ("运行测试", "pytest tests/"),
        ("Git 状态", "git status"),
    ]

    print("\n❌ 危险命令（需要确认）：")
    for desc, cmd in dangerous_responses:
        is_dangerous = HybridParser._is_dangerous_command(cmd)
        status = "⚠️  需要确认" if is_dangerous else "✓ 安全"
        print(f"  {status} - {desc}: {cmd}")

    print("\n✅ 安全命令（可自动执行）：")
    for desc, cmd in safe_responses:
        is_dangerous = HybridParser._is_dangerous_command(cmd)
        status = "⚠️  需要确认" if is_dangerous else "✓ 安全"
        print(f"  {status} - {desc}: {cmd}")

    print()


def example_workflow():
    """示例 4: 完整工作流"""
    print("\n" + "=" * 60)
    print("示例 4: 完整开发工作流")
    print("=" * 60)

    # 模拟多轮对话
    workflow = """
用户: 帮我创建一个简单的 Python 包

AI:
<file_edit path="mypackage/__init__.py" type="create" description="包初始化">
```python
\"\"\"My Package\"\"\"
__version__ = "0.1.0"
```
</file_edit>

<file_edit path="mypackage/core.py" type="create" description="核心模块">
```python
def hello(name: str) -> str:
    return f"Hello, {name}!"
```
</file_edit>

<file_edit path="setup.py" type="create" description="安装配置">
```python
from setuptools import setup, find_packages

setup(
    name="mypackage",
    version="0.1.0",
    packages=find_packages(),
)
```
</file_edit>

---

用户: 添加测试

AI:
<file_edit path="tests/test_core.py" type="create" description="创建测试">
```python
import pytest
from mypackage.core import hello

def test_hello():
    assert hello("World") == "Hello, World!"
    assert hello("Python") == "Hello, Python!"
```
</file_edit>

<bash_command description="运行测试">
pytest tests/ -v
</bash_command>

---

用户: 添加类型检查

AI:
<bash_command description="安装 mypy">
pip install mypy
</bash_command>

<bash_command description="运行类型检查">
mypy mypackage/
</bash_command>
"""

    print("\n完整的开发流程示例：")
    print(workflow)

    # 解析所有步骤
    all_actions = HybridParser.parse_xml(workflow)

    print(f"\n总共 {len(all_actions)} 个动作：")

    code_edits = [a for a in all_actions if a.action_type.value == 'code_edit']
    bash_cmds = [a for a in all_actions if a.action_type.value == 'bash']

    print(f"  - {len(code_edits)} 个文件操作")
    print(f"  - {len(bash_cmds)} 个命令执行")

    print("\n文件操作：")
    for action in code_edits:
        print(f"  📄 {action.file_path} - {action.description}")

    print("\n命令执行：")
    for action in bash_cmds:
        print(f"  💻 {action.command} - {action.description}")

    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("统一 Agent 系统使用示例")
    print("=" * 60)

    try:
        example_mock_llm_usage()
        example_parse_formats()
        example_safety_check()
        example_workflow()

        print("=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        print()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
