# 统一 Agent 系统文档

## 🎯 概述

统一 Agent 系统实现了**代码生成**和**命令执行**的完美融合，支持：

- ✅ **双模式支持**：Function Calling + Prompt Engineering
- ✅ **智能解析**：自动识别 XML、JSON、Function Call 格式
- ✅ **安全执行**：危险命令检测和用户确认机制
- ✅ **多种动作**：代码编辑、命令执行、文件读写
- ✅ **多轮对话**：支持结果反馈和迭代优化

## 📦 架构设计

```
aicode/agent/
├── __init__.py           # 模块导出
├── actions.py            # 动作数据类
├── parser.py             # 混合格式解析器
├── executor.py           # 动作执行器
└── unified_agent.py      # 统一 Agent 主类
```

### 核心组件

#### 1. Action 数据类 (actions.py)

统一的动作抽象层：

```python
from aicode.agent import (
    CodeEditAction,    # 代码编辑
    BashAction,        # 命令执行
    FileReadAction,    # 文件读取
    FileWriteAction,   # 文件写入
)

# 创建动作
action = CodeEditAction(
    file_path="main.py",
    content="print('hello')",
    edit_type="create",
    description="创建主文件"
)
```

#### 2. HybridParser (parser.py)

智能解析器，支持多种格式：

**格式 1: XML 标签（Prompt Engineering）**

```xml
<file_edit path="app.py" type="create" description="创建应用">
```python
print("Hello")
```
</file_edit>

<bash_command description="运行">
python app.py
</bash_command>
```

**格式 2: Function Calling**

```json
{
  "tool_use_id": "1",
  "name": "edit_file",
  "input": {
    "file_path": "app.py",
    "content": "print('Hello')"
  }
}
```

**格式 3: JSON**

```json
{
  "action_type": "code_edit",
  "file_path": "app.py",
  "content": "print('Hello')"
}
```

#### 3. ActionExecutor (executor.py)

安全的动作执行器：

- ✅ 文件操作（创建、修改、删除）
- ✅ 命令执行（超时控制）
- ✅ 路径解析（支持相对路径）
- ✅ 错误处理

#### 4. UnifiedAgent (unified_agent.py)

统一的 AI Agent：

- 自动检测模型能力（FC vs PE）
- 管理对话历史
- 解析和执行动作
- 结果反馈

## 🚀 快速开始

### 基础使用

```python
from aicode.agent import UnifiedAgent

# 创建 Agent
agent = UnifiedAgent(llm_client, working_dir=".")

# 对话并获取动作
response, actions = agent.chat("创建一个 Flask 应用")

# 查看动作
for action in actions:
    print(f"{action.action_type.value}: {action.description}")

# 执行动作
for action in actions:
    if action.requires_confirmation:
        confirm = input("执行? (y/n): ")
        if confirm.lower() == 'y':
            result = agent.execute_action(action)
            print(result['output'])
```

### 解析 AI 响应

```python
from aicode.agent.parser import HybridParser

# 解析 XML 格式
actions = HybridParser.parse_xml(ai_response)

# 解析 Function Calling
actions = HybridParser.parse_function_calling(response_obj)

# 智能解析（自动检测）
actions = HybridParser.parse(response)
```

### 执行动作

```python
from aicode.agent.executor import ActionExecutor

executor = ActionExecutor(working_dir=".")

# 执行单个动作
result = executor.execute(action)

if result['success']:
    print(f"成功: {result['output']}")
else:
    print(f"失败: {result['error']}")
```

## 🔐 安全机制

### 危险命令检测

自动检测以下危险模式：

- `rm -rf /` - 删除根目录
- `sudo rm` - sudo 删除
- `chmod 777` - 危险权限
- `mkfs` - 格式化
- `dd if=` - dd 命令
- Fork bomb 等

```python
from aicode.agent.parser import HybridParser

# 检测命令
is_dangerous = HybridParser._is_dangerous_command("rm -rf /")
# True

is_safe = HybridParser._is_dangerous_command("ls -la")
# False
```

### 用户确认机制

```python
# 危险动作自动标记为需要确认
action = BashAction(
    command="rm -rf /tmp/*",
    description="清理临时文件"
)

if action.requires_confirmation:
    # 需要用户确认
    confirm = input("确认执行? (y/n): ")
```

## 📊 支持的动作类型

| 动作类型 | 类名 | 用途 | 需确认 |
|---------|------|------|--------|
| **代码编辑** | CodeEditAction | 创建/修改/删除文件 | ✅ |
| **命令执行** | BashAction | 执行 shell 命令 | 视情况 |
| **文件读取** | FileReadAction | 读取文件内容 | ❌ |
| **文件写入** | FileWriteAction | 写入文件 | ✅ |

## 🎨 使用场景

### 场景 1: 创建项目

```python
agent.chat("""
创建一个 Python 项目，包含：
1. 主文件 main.py
2. 配置文件 config.yaml
3. 依赖文件 requirements.txt
4. 测试文件 tests/test_main.py
""")

# AI 会返回多个 CodeEditAction
```

### 场景 2: 重构代码

```python
agent.chat("""
重构 src/utils.py 中的 process_data 函数，
使其更加模块化，并添加类型注解
""")

# AI 会返回 CodeEditAction + BashAction（运行测试）
```

### 场景 3: Bug 修复

```python
agent.chat("""
检查代码中的类型错误并修复
""")

# AI 可能会：
# 1. BashAction: mypy src/
# 2. CodeEditAction: 修复错误
# 3. BashAction: mypy src/ (验证)
```

### 场景 4: 自动化任务

```python
agent.chat("""
1. 更新依赖版本
2. 运行所有测试
3. 生成测试覆盖率报告
4. 提交到 Git
""")

# AI 会返回一系列 BashAction
```

## 🔄 工作流程

```
用户输入
    ↓
UnifiedAgent.chat()
    ↓
检测模型能力
    ├─→ 支持 FC: 使用 Function Calling
    └─→ 不支持: 使用 Prompt Engineering (XML)
    ↓
调用 LLM
    ↓
HybridParser.parse()
    ├─→ 解析 Function Call
    ├─→ 解析 XML 标签
    └─→ 解析 JSON
    ↓
返回 Action 列表
    ↓
用户确认
    ↓
ActionExecutor.execute()
    ├─→ 代码编辑
    ├─→ 命令执行
    ├─→ 文件读写
    └─→ 返回结果
    ↓
（可选）结果反馈给 LLM
    ↓
继续下一轮
```

## 🧪 测试

运行测试：

```bash
# 完整测试
python test_unified_agent.py

# 使用示例
python example_agent_usage.py
```

测试覆盖：

- ✅ Action 数据类
- ✅ XML 格式解析
- ✅ 危险命令检测
- ✅ 动作执行
- ✅ 多格式解析
- ✅ UnifiedAgent 集成
- ✅ 端到端工作流

## 📝 最佳实践

### 1. 提示词设计

为不支持 FC 的模型提供清晰的格式说明：

```python
system_prompt = """
请使用以下格式返回动作：

代码编辑：
<file_edit path="file.py" type="modify" description="说明">
```python
代码内容
```
</file_edit>

命令执行：
<bash_command description="说明">
命令内容
</bash_command>
"""
```

### 2. 错误处理

```python
try:
    response, actions = agent.chat(user_input)

    for action in actions:
        result = agent.execute_action(action)

        if not result['success']:
            # 将错误反馈给 AI
            agent.chat(f"执行失败: {result['error']}，请修正")

except Exception as e:
    print(f"错误: {e}")
```

### 3. 安全第一

```python
# 始终检查危险命令
if action.action_type == ActionType.BASH:
    if action.requires_confirmation:
        print(f"⚠️  危险命令: {action.command}")
        confirm = input("确认执行? (y/n): ")
        if confirm.lower() != 'y':
            continue
```

### 4. 日志记录

```python
from aicode.utils.logger import get_logger

logger = get_logger(__name__)

# 所有操作都会自动记录
logger.info("Executing action...")
```

## 🔮 未来扩展

计划中的功能：

- [ ] 搜索代码（SearchAction）
- [ ] Git 操作（GitAction）
- [ ] 数据库操作（DBAction）
- [ ] API 调用（APIAction）
- [ ] 流式执行
- [ ] 并发执行多个动作
- [ ] 撤销/重做机制
- [ ] 动作执行历史

## 🤝 集成到 CLI

```python
# aicode/cli/commands/assist.py

from aicode.agent import UnifiedAgent

def assist_command(args):
    """AI 助手命令"""

    client = create_llm_client(args.model)
    agent = UnifiedAgent(client)

    while True:
        user_input = input("👤 You: ")

        response, actions = agent.chat(user_input)

        # 显示动作
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action.description}")

        # 用户选择执行
        choice = input("执行哪些? (all/1,2,3/skip): ")

        if choice == 'all':
            agent.execute_actions(actions)
```

## 📚 参考资料

- [Anthropic Tool Use 文档](https://docs.anthropic.com/claude/docs/tool-use)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [code_edit.py](../aicode/llm/code_edit.py) - 原始代码编辑实现
- [test_unified_agent.py](../test_unified_agent.py) - 测试代码
- [example_agent_usage.py](../example_agent_usage.py) - 使用示例

---

**版本**: 1.0.0
**更新**: 2025-11-07
