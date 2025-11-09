# VS Code 开发环境配置

本目录包含 VS Code 开发环境的配置文件，提供一键式代码检查和格式化。

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `tasks.json` | 任务定义（静态检查、格式化、测试） |
| `settings.json` | Python 开发环境配置 |
| `keybindings.json` | 快捷键绑定 |
| `README.md` | 本文档 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -e .[dev]
```

### 2. 使用任务

**方式 1：快捷键**
- `Ctrl+Shift+B` → 运行默认任务（CI: All Static Checks）

**方式 2：命令面板**
- `Ctrl+Shift+P` → `Tasks: Run Task` → 选择任务

**方式 3：终端菜单**
- `Terminal` → `Run Task...`

---

## 📋 可用任务

### 主任务

| 任务 | 说明 | 快捷键 |
|------|------|--------|
| **CI: All Static Checks** ⭐ | 运行所有静态检查（格式 + Lint） | `Ctrl+Shift+B` |

**检查内容**：
- Black 代码格式检查
- Isort 导入排序检查
- Flake8 语法错误检查（E9, F63, F7, F82）
- Pylint 未使用变量/参数检查（W0613, W0612, E0601, E0602...）

### 格式化

| 任务 | 说明 |
|------|------|
| **Format: Check All** | 检查代码格式（black + isort） |
| **Format: Fix All** | 自动修复格式问题 |

### 代码检查

| 任务 | 说明 |
|------|------|
| **Lint: Check All** | flake8 + pylint 检查（语法错误、未使用变量） |

### 测试

| 任务 | 说明 | 快捷键 |
|------|------|--------|
| **Test: Unit Tests** | 运行单元测试 | `Ctrl+Shift+T` |
| **Test: With Coverage** | 运行测试并生成覆盖率报告 | - |

### 类型检查

| 任务 | 说明 |
|------|------|
| **Type Check: Mypy** | 运行 mypy 类型检查 |

---

## 🎯 推荐工作流

### 开发时

1. 编写代码
2. 保存时自动格式化（`settings.json` 配置）
3. 提交前运行 `CI: All Static Checks`

### 提交前

```bash
# VS Code 任务
Ctrl+Shift+B  # 运行所有检查

# 或命令行
pytest tests/unit/ -v
black aicode tests
isort aicode tests
flake8 aicode
```

---

## 🔧 自定义检查项

### 方式 1：修改命令参数

编辑 `.vscode/tasks.json`，找到 `Lint: Check All` 任务：

```json
{
    "label": "Lint: Check All",
    "command": "flake8 aicode --select=E9,F63,F7,F82 && pylint aicode --enable=W0613,W0612"
}
```

### 方式 2：修改配置文件

编辑根目录的 `.pylintrc`：

```ini
[MESSAGES CONTROL]
enable=W0613,W0612,E0601,E0602  # 启用的检查项
disable=C0111,C0103             # 禁用的检查项
```

### 常用检查码

**Pylint**：
- `W0613` - 未使用的参数
- `W0612` - 未使用的变量
- `E0601` - 使用未定义的变量
- `E0602` - 未定义的名称
- `W0611` - 未使用的导入
- `E1101` - 无此成员

**Flake8**：
- `E9` - 语法错误
- `F63` - 断言错误
- `F7` - 语法问题
- `F82` - 未定义名称

---

## 📝 配置说明

### settings.json

```json
{
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,           // 保存时自动格式化
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.testing.pytestEnabled": true
}
```

### keybindings.json

```json
[
    {
        "key": "ctrl+shift+b",
        "command": "workbench.action.tasks.build"  // CI: All Static Checks
    },
    {
        "key": "ctrl+shift+t",
        "command": "workbench.action.tasks.runTask",
        "args": "Test: Unit Tests"
    }
]
```

---

## 🐛 故障排查

### 问题 1: 任务找不到命令

**解决**:
```bash
pip install -e .[dev]
```

### 问题 2: 保存时不自动格式化

**解决**:
1. 安装 Python 扩展
2. 检查 `settings.json` 中 `editor.formatOnSave` 是否为 `true`

### 问题 3: 想要禁用某些检查

**解决**: 编辑 `.pylintrc` 或 `tasks.json` 中的命令参数

---

## 📚 相关文档

- [VS Code Tasks 文档](https://code.visualstudio.com/docs/editor/tasks)
- [Black 文档](https://black.readthedocs.io/)
- [Pylint 文档](https://pylint.pycqa.org/)

---

最后更新：2025-01-09
