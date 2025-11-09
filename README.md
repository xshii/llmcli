# AICode - LLM CLI Tool

智能代码助手命令行工具

## 开发进度

- ✅ **Phase 0 (基础层)** - 100% 完成
  - 全局常量配置 (constants.py)
  - 日志系统 (logger.py)
  - 异常体系 (exceptions.py)
  - 48个单元测试，100%覆盖率

- ✅ **Phase 1 (数据模型层)** - 100% 完成
  - 数据模型定义 (schema.py)
  - 数据验证工具 (validators.py)
  - 88个单元测试，98%覆盖率

- ✅ **Phase 2 (数据库与配置层)** - 100% 完成
  - SQLite数据库管理 (db_manager.py)
  - YAML/JSON配置管理 (config_manager.py)
  - Token计数管理 (token_manager.py)
  - 79个单元测试，90%覆盖率

- ✅ **Phase 3A (CLI核心)** - 100% 完成
  - LLM API客户端 (llm/client.py)
  - CLI主入口 (cli/main.py)
  - 命令模块化架构 (cli/commands/)
    - chat 命令 - LLM对话
    - model 命令 - 模型管理
    - config 命令 - 配置管理
  - 文件操作工具 (cli/utils/file_ops.py)
  - 输出格式化 (cli/utils/output.py)
  - **总计：215个测试通过，约1200行新代码** ✨

## 快速开始

### 安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 开发者安装（包括测试、linting 等工具）
pip install -e .[dev]

# 或仅安装运行时依赖
pip install -e .
```

### 开发工作流

```bash
# 运行测试
pytest tests/unit/ -v

# 代码格式化
black aicode tests
isort aicode tests

# 代码检查
flake8 aicode
pylint aicode

# 类型检查
mypy aicode --ignore-missing-imports

# 查看覆盖率
pytest tests/unit/ --cov=aicode --cov-report=term-missing
```

### CLI 使用

```bash
# 1. 初始化配置
python -m aicode.cli.main config init

# 2. 设置 API Key
python -m aicode.cli.main config set global.api_key sk-your-key

# 3. 添加模型
python -m aicode.cli.main model add gpt-4 openai \
  --max-input 8192 \
  --max-output 4096 \
  --code-score 9.0

# 4. 对话
python -m aicode.cli.main chat "Hello, explain Python decorators"

# 5. 带文件上下文
python -m aicode.cli.main chat "Explain this file" --file main.py
```

## 项目结构

```
aicode/
├── cli/                  # CLI命令行 ✅
│   ├── main.py               ✅ CLI入口
│   ├── commands/             ✅ 命令模块（每个命令一个文件）
│   │   ├── chat.py           - LLM对话
│   │   ├── model.py          - 模型管理
│   │   └── config.py         - 配置管理
│   └── utils/                ✅ CLI工具
│       ├── file_ops.py       - 文件操作
│       └── output.py         - 输出格式化
├── llm/                  # LLM相关
│   ├── client.py             ✅ LLM API客户端
│   ├── token_manager.py      ✅ Token计数
│   └── exceptions.py         ✅ 异常体系
├── config/               # 配置管理
│   ├── constants.py          ✅ 全局常量
│   └── config_manager.py     ✅ YAML/JSON配置
├── database/             # 数据库操作
│   └── db_manager.py         ✅ SQLite管理
├── models/               # 数据模型
│   └── schema.py             ✅ 模型定义
└── utils/                # 工具函数
    ├── logger.py             ✅ 日志系统
    └── validators.py         ✅ 数据验证

tests/
├── unit/                         ✅ 215个单元测试
│   ├── test_constants.py         (10个测试)
│   ├── test_exceptions.py        (23个测试)
│   ├── test_logger.py            (15个测试)
│   ├── test_schema.py            (22个测试)
│   ├── test_validators.py        (66个测试)
│   ├── test_db_manager.py        (22个测试)
│   ├── test_config_manager.py    (29个测试)
│   └── test_token_manager.py     (28个测试)
└── integration/                  (待开发 - Phase 3B)
```

## CLI 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `config init` | 初始化配置 | `aicode config init` |
| `config set` | 设置配置项 | `aicode config set global.api_key sk-xxx` |
| `config get` | 获取配置项 | `aicode config get global.api_key` |
| `config show` | 显示所有配置 | `aicode config show` |
| `model add` | 添加模型 | `aicode model add gpt-4 openai --max-input 8192` |
| `model list` | 列出模型 | `aicode model list` |
| `model show` | 显示模型详情 | `aicode model show gpt-4` |
| `model remove` | 删除模型 | `aicode model remove gpt-4` |
| `chat` | LLM对话 | `aicode chat "explain Python"` |
| `chat --file` | 带文件上下文 | `aicode chat "explain" --file app.py` |

## 技术栈

- **Python 3.8.1+**
- **CLI框架**: argparse
- **数据库**: SQLite
- **配置**: YAML/JSON
- **Token计数**: tiktoken
- **HTTP客户端**: httpx
- **测试**: pytest
- **依赖**: pyyaml, tiktoken, httpx

## Ollama 本地模型支持 🆕

### 安装 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 下载：https://ollama.com/download/windows
```

### 使用 Ollama

```bash
# 1. 启动 Ollama 服务
ollama serve

# 2. 搜索可用模型
aicode ollama search llama

# 3. 下载模型
aicode ollama pull llama2:13b

# 4. 列出本地模型
aicode ollama list

# 5. 添加到 aicode
aicode model add llama2:13b ollama \
  --api-url http://localhost:11434/v1 \
  --local \
  --code-score 7.5

# 6. 使用本地模型对话
aicode chat "写一个快速排序" --model llama2:13b

# 7. 删除模型
aicode ollama remove llama2:13b
```

### 推荐模型

| 模型 | 大小 | 用途 | 命令 |
|------|------|------|------|
| codellama:7b | 3.8GB | 代码生成 | `aicode ollama pull codellama:7b` |
| llama2:13b | 7.3GB | 通用对话 | `aicode ollama pull llama2:13b` |
| deepseek-r1:7b | 4.1GB | 推理任务 | `aicode ollama pull deepseek-r1:7b` |
| gemma2:9b | 5.4GB | 轻量通用 | `aicode ollama pull gemma2:9b` |
