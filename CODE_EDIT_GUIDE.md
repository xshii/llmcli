# AICode - 代码编辑功能使用指南

## 功能概述

AICode 现在支持类似 Claude Code 的**代码差异对比和交互式应用**功能：

1. **AI 返回结构化的代码修改建议**
2. **自动展示 Diff 视图**（左右对比）
3. **交互式应用修改**（通过选择或输入数字）

---

## 工作流程

### 1. 请求代码修改

在聊天中向 AI 提出代码修改请求，例如：

```
请帮我修改 src/main.py，添加错误处理
```

### 2. AI 返回结构化建议

AI 会使用特殊的 XML 格式返回代码修改：

```xml
<file_edit path="src/main.py" type="modify" description="添加错误处理">
```python
def main():
    try:
        result = process_data()
        print(result)
    except Exception as e:
        logger.error(f"Error: {e}")
```
</file_edit>
```

### 3. 查看差异

VSCode 会自动：
1. 解析代码编辑建议
2. 显示通知：`N code change(s) proposed`
3. 点击 "Review Changes" 查看详细列表

### 4. 审查和应用

**选项 A: 通过 Quick Pick 菜单**

VSCode 会显示编辑列表：

```
1. src/main.py
   └─ 添加错误处理
   └─ Type: modify

2. tests/test_main.py
   └─ 添加单元测试
   └─ Type: create

[Apply All]  Apply all changes
[Skip]       Do not apply any changes
```

- 选择单个编辑 → 打开 Diff 视图查看详细差异
- 选择 "Apply All" → 应用所有修改
- 选择 "Skip" → 跳过所有修改

**选项 B: Diff 视图**

选择单个编辑后会打开 Diff 视图：
- **左侧**: 原始文件内容
- **右侧**: 修改后的内容
- **高亮**: 具体的改动行

然后选择操作：
- **Apply**: 应用这个修改
- **Skip**: 跳过这个修改
- **View Others**: 查看其他待处理的修改

---

## AI 返回格式规范

### 基本格式

```xml
<file_edit path="相对路径" type="操作类型" description="简短描述">
```语言
代码内容
```
</file_edit>
```

### 属性说明

| 属性 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `path` | ✓ | 文件相对路径 | `src/main.py` |
| `type` | - | 操作类型 | `modify`, `create`, `delete` |
| `description` | - | 修改描述 | `修复bug`, `添加功能` |

### 操作类型

- **`modify`** (默认): 修改现有文件
- **`create`**: 创建新文件
- **delete**: 删除文件（谨慎使用）

### 示例

#### 修改现有文件

```xml
<file_edit path="src/utils.py" type="modify" description="优化性能">
```python
def calculate(data):
    # 使用生成器优化内存
    return sum(x for x in data if x > 0)
```
</file_edit>
```

#### 创建新文件

```xml
<file_edit path="tests/test_utils.py" type="create" description="添加单元测试">
```python
import unittest
from src.utils import calculate

class TestCalculate(unittest.TestCase):
    def test_positive_numbers(self):
        result = calculate([1, 2, 3])
        self.assertEqual(result, 6)
```
</file_edit>
```

#### 多个文件修改

```xml
<file_edit path="src/main.py" type="modify" description="添加日志">
```python
import logging

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting...")
```
</file_edit>

<file_edit path="src/config.py" type="create" description="添加配置文件">
```python
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(message)s"
```
</file_edit>
```

---

## 系统提示词（System Prompt）

AICode 自动在每个会话的第一条消息时注入以下系统提示：

```
When suggesting code changes, use this XML format:

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
```

这确保 AI 始终以正确的格式返回代码修改建议。

---

## 使用技巧

### 1. 明确指定文件路径

❌ **不好**:
```
帮我修改 main 函数
```

✅ **更好**:
```
帮我修改 src/main.py 中的 main 函数，添加错误处理
```

### 2. 提供当前文件上下文

VSCode 扩展会自动发送当前打开的文件作为上下文，但你也可以明确提及：

```
当前文件是 src/api.py，请帮我：
1. 添加参数验证
2. 优化错误处理
3. 添加类型注解
```

### 3. 批量修改

```
请帮我重构以下文件：
- src/main.py: 使用 async/await
- src/utils.py: 添加类型注解
- tests/test_main.py: 更新测试用例
```

### 4. 查看修改摘要

AI 返回的响应中会包含修改摘要：

```
📝 Proposed Code Changes:

1. src/main.py
   └─ 添加错误处理
   └─ Type: modify

2. tests/test_main.py
   └─ 添加单元测试
   └─ Type: create

To apply changes:
  - Type the number to apply that change
  - Type 'all' to apply all changes
  - Type 'skip' to skip
```

---

## 故障排查

### AI 没有返回结构化格式

**可能原因**:
- 对话不是新会话（系统提示只在第一条消息注入）
- AI 模型不遵循指令

**解决方案**:
1. 开启新会话：`AICode: Clear History`
2. 明确要求：`请使用 <file_edit> 格式返回代码修改`

### Diff 视图没有显示

**可能原因**:
- 文件路径不正确
- 工作区未打开

**解决方案**:
1. 确保在 VSCode 中打开了项目文件夹
2. 检查文件路径是否相对于工作区根目录

### 应用修改失败

**可能原因**:
- 文件权限问题
- 路径不存在

**解决方案**:
1. 检查文件权限
2. 对于新文件，确保父目录存在
3. 查看 Output 面板的 "AICode" 日志

---

## 完整示例

### 场景：修复 Bug

**用户请求**:
```
src/calculator.py 中的 divide 函数有 bug，
除以零时会崩溃。请修复并添加测试。
```

**AI 返回**:
```xml
<file_edit path="src/calculator.py" type="modify" description="修复除以零bug">
```python
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```
</file_edit>

<file_edit path="tests/test_calculator.py" type="modify" description="添加除零测试">
```python
import unittest
from src.calculator import divide

class TestDivide(unittest.TestCase):
    def test_normal_division(self):
        self.assertEqual(divide(10, 2), 5)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            divide(10, 0)
```
</file_edit>
```

**VSCode 显示**:
1. 通知：`2 code change(s) proposed`
2. Quick Pick 列表显示两个修改
3. 选择第一个 → 打开 Diff 视图查看修复
4. 点击 "Apply" → 文件更新完成
5. 选择第二个 → 查看测试用例
6. 点击 "Apply" → 测试文件更新

---

## 与 Claude Code 对比

| 功能 | AICode | Claude Code |
|------|--------|-------------|
| 代码差异视图 | ✓ | ✓ |
| 左右分栏对比 | ✓ | ✓ |
| 交互式应用 | ✓ | ✓ |
| 批量修改 | ✓ | ✓ |
| 数字快捷应用 | ✓ | ✓ |
| 自动检测修改 | ✓ | ✓ |
| 流式响应 | - | ✓ |
| 内联差异 | - | ✓ |

---

## 后续优化方向

- [ ] 支持流式返回（边生成边显示）
- [ ] 内联差异视图（直接在编辑器中显示修改）
- [ ] 部分应用（只应用某些行的修改）
- [ ] 撤销/重做功能
- [ ] 修改历史记录
- [ ] Git 集成（自动创建 commit）

---

## 总结

AICode 的代码编辑功能提供了：
1. **结构化格式**: 清晰的 XML 标记
2. **可视化对比**: VSCode 原生 Diff 视图
3. **交互式确认**: 选择性应用修改
4. **批量操作**: 一次处理多个文件

这让 AI 辅助编程变得更加安全和可控！
