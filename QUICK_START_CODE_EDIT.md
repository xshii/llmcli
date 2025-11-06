# AICode 代码编辑功能 - 快速入门

## 5分钟上手指南

### 前提条件

✅ AICode Python 包已安装并配置
✅ VSCode 扩展已构建并加载
✅ 工作区已打开

---

## 步骤 1: 测试后端解析

```bash
cd /Users/gakki/dev/llmcli
source venv/bin/activate
python test_code_edit.py
```

应该看到：
```
==================================================
ALL TESTS PASSED! ✓
==================================================
```

---

## 步骤 2: 启动 VSCode 扩展

### 开发模式

```bash
cd vscode-extension
npm install  # 首次运行
npm run compile
```

在 VSCode 中：
1. 打开 `vscode-extension` 文件夹
2. 按 `F5` 启动调试
3. 新窗口打开一个项目

### 或打包安装

```bash
cd vscode-extension
npm install -g vsce
vsce package
# 安装生成的 .vsix 文件
```

---

## 步骤 3: 测试代码编辑功能

### 3.1 创建测试项目

在新窗口创建一个简单的项目：

```bash
mkdir test-project
cd test-project

# 创建一个简单的 Python 文件
cat > main.py << 'EOF'
def calculate(a, b):
    return a / b

if __name__ == "__main__":
    print(calculate(10, 2))
EOF
```

### 3.2 打开 AICode 聊天

- 按 `Ctrl+Shift+A` (Mac: `Cmd+Shift+A`)
- 或点击状态栏的 "AICode"

### 3.3 请求代码修改

在聊天中输入：

```
请修改 main.py，添加除以零的错误处理，并创建一个测试文件
```

### 3.4 查看 AI 响应

AI 应该返回类似这样的响应（包含 XML 标记）：

```xml
<file_edit path="main.py" type="modify" description="添加除零检查">
```python
def calculate(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    try:
        print(calculate(10, 2))
        print(calculate(10, 0))  # 测试除零
    except ValueError as e:
        print(f"Error: {e}")
```
</file_edit>

<file_edit path="test_main.py" type="create" description="添加单元测试">
```python
import unittest
from main import calculate

class TestCalculate(unittest.TestCase):
    def test_normal_division(self):
        self.assertEqual(calculate(10, 2), 5)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            calculate(10, 0)

if __name__ == '__main__':
    unittest.main()
```
</file_edit>
```

### 3.5 查看通知

VSCode 右下角会显示通知：

```
2 code change(s) proposed   [Review Changes]
```

点击 **Review Changes**

### 3.6 查看编辑列表

Quick Pick 菜单会显示：

```
1. main.py
   └─ 添加除零检查
   └─ Type: modify

2. test_main.py
   └─ 添加单元测试
   └─ Type: create

[Apply All]  Apply all changes
[Skip]       Do not apply any changes
```

### 3.7 审查单个修改

选择 `1. main.py` → 打开 **Diff 视图**：

- **左侧**: 原始的 main.py
- **右侧**: 修改后的版本
- **高亮**: 具体的改动

底部会显示提示：

```
Apply this change to main.py?
[Apply]  [Skip]  [View Others]
```

### 3.8 应用修改

点击 **Apply** → 文件更新完成！

验证：

```bash
cat main.py  # 查看修改后的内容
python test_main.py  # 运行测试
```

---

## 预期输出

### 修改后的 main.py

```python
def calculate(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    try:
        print(calculate(10, 2))
        print(calculate(10, 0))
    except ValueError as e:
        print(f"Error: {e}")
```

### 新创建的 test_main.py

```python
import unittest
from main import calculate

class TestCalculate(unittest.TestCase):
    def test_normal_division(self):
        self.assertEqual(calculate(10, 2), 5)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            calculate(10, 0)

if __name__ == '__main__':
    unittest.main()
```

### 运行测试

```bash
$ python test_main.py
..
----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK
```

---

## 故障排查

### 问题 1: AI 没有返回 XML 格式

**检查**:
```bash
# 在 Python 环境中测试
python -c "from aicode.llm.code_edit import create_inline_edit_prompt; print(create_inline_edit_prompt())"
```

应该看到系统提示内容。

### 问题 2: Diff 视图没有打开

**检查**:
1. 工作区是否打开？
2. 文件路径是否正确？
3. 查看 Output → AICode 日志

### 问题 3: 应用修改失败

**检查**:
1. 文件权限
2. 对于新文件，父目录是否存在

---

## 高级测试

### 测试多文件修改

```
请帮我重构项目：
1. main.py: 将 calculate 函数移到 utils.py
2. utils.py: 新建文件，放置工具函数
3. main.py: 导入 utils
4. test_utils.py: 创建测试文件
```

AI 应该返回 4 个 `<file_edit>` 标签。

### 测试批量应用

选择 **[Apply All]** → 一次性应用所有修改

---

## 调试技巧

### 查看 RPC 通信

```bash
# 启动 RPC server (手动模式)
source venv/bin/activate
python -m aicode.cli.main server --mode stdio

# 在另一个终端
python test_rpc_server.py
```

### 查看编辑解析

```bash
python test_code_edit.py
```

### VSCode 扩展日志

- View → Output → Select "AICode"

---

## 总结

✓ **Python 后端**: 解析 XML 格式的代码编辑
✓ **VSCode 扩展**: Diff 视图和交互式应用
✓ **工作流程**: 请求 → 审查 → 应用

现在你可以像使用 Claude Code 一样，让 AI 直接修改代码并查看差异！
