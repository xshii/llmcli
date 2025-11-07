# AICode - LLM CLI Tool

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-215%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-90%25+-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> 一个功能强大的智能代码助手命令行工具，让你在终端中轻松使用各种大语言模型（LLM）进行代码分析、问答和开发辅助。

## ✨ 核心特性

- 🤖 **多模型支持**: 集成 OpenAI、Claude、本地模型等多种 LLM 提供商
- 💬 **智能对话**: 命令行中直接与 LLM 进行自然语言交互
- 📁 **文件上下文**: 支持将本地文件内容作为上下文进行分析
- 🎯 **模型管理**: 便捷的模型配置、切换和性能评分系统
- 💾 **配置管理**: YAML/JSON 格式的灵活配置，支持多环境配置
- 📊 **Token 管理**: 自动计算和追踪 Token 使用量，优化成本
- 🗄️ **对话历史**: SQLite 数据库存储对话记录，支持历史查询
- 🧪 **高质量代码**: 215+ 单元测试，90%+ 代码覆盖率

## 🎯 适用场景

- **代码审查**: 快速分析代码质量、发现潜在问题
- **技术学习**: 询问编程问题，获得详细解释
- **代码生成**: 描述需求，生成代码片段
- **文档分析**: 理解复杂的技术文档和代码库
- **DevOps 自动化**: 集成到 CI/CD 流程中

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

## 📋 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: Linux, macOS, Windows (推荐 WSL)
- **依赖**: pip, virtualenv (推荐)
- **存储**: 至少 100MB 可用空间（用于数据库和日志）

## 📦 安装

### 方式一：用户安装（推荐）

```bash
# 从 PyPI 安装（待发布）
pip install aicode

# 验证安装
aicode --version
```

### 方式二：开发安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/aicode.git
cd aicode

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 以开发模式安装
pip install -e .
```

## 🚀 快速开始

### 初次使用

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

📖 **详细使用指南**: 查看 [CLI_GUIDE.md](CLI_GUIDE.md)

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

- **Python 3.9+**
- **CLI框架**: argparse
- **数据库**: SQLite
- **配置**: YAML/JSON
- **Token计数**: tiktoken
- **测试**: pytest
- **依赖**: pyyaml, tiktoken

## 🧪 开发与测试

### 运行测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 查看测试覆盖率
pytest tests/unit/ --cov=aicode --cov-report=term-missing

# 运行特定测试文件
pytest tests/unit/test_schema.py -v

# 生成 HTML 覆盖率报告
pytest tests/unit/ --cov=aicode --cov-report=html
```

### 代码质量

```bash
# 代码格式化
black aicode/

# 代码检查
flake8 aicode/
pylint aicode/

# 类型检查
mypy aicode/
```

## 🗺️ 路线图

### 已完成 ✅
- [x] Phase 0: 基础架构（日志、异常、常量）
- [x] Phase 1: 数据模型和验证
- [x] Phase 2: 数据库和配置管理
- [x] Phase 3A: CLI 核心功能（chat、model、config）

### 进行中 🚧
- [ ] Phase 3B: 集成测试
- [ ] Phase 3C: 性能优化

### 计划中 📅
- [ ] **Phase 4: 高级功能**
  - [ ] 对话上下文管理（多轮对话）
  - [ ] 流式输出支持
  - [ ] 插件系统
  - [ ] 自定义 Prompt 模板

- [ ] **Phase 5: 生态扩展**
  - [ ] VS Code 插件
  - [ ] Web 界面
  - [ ] Docker 镜像
  - [ ] 云端部署支持

## ⚠️ 已知限制

- **模型支持**: 当前主要测试了 OpenAI 模型，其他提供商需要进一步验证
- **并发**: 暂不支持多个实例同时访问同一数据库
- **文件大小**: 单个文件上下文建议不超过 10MB
- **流式输出**: 尚未实现，所有响应需等待完成后返回
- **Windows 支持**: 部分路径处理在 Windows 原生环境可能存在问题，建议使用 WSL

## 📚 文档

- **[CLI 使用指南](CLI_GUIDE.md)** - 详细的命令行使用说明
- **[开发文档](docs/DEVELOPMENT.md)** - 开发者指南和架构说明
- **[API 文档](docs/API.md)** - 核心 API 参考
- **[配置指南](docs/CONFIGURATION.md)** - 配置文件详解
- **[贡献指南](CONTRIBUTING.md)** - 如何参与项目开发
- **[更新日志](CHANGELOG.md)** - 版本更新记录

## ❓ 常见问题 (FAQ)

<details>
<summary><b>如何配置代理？</b></summary>

在配置文件中添加代理设置：
```yaml
global:
  proxy: http://127.0.0.1:7890
  proxy_https: http://127.0.0.1:7890
```
</details>

<details>
<summary><b>支持哪些 LLM 提供商？</b></summary>

目前支持：
- OpenAI (GPT-3.5, GPT-4)
- Anthropic Claude
- 本地模型（通过兼容接口）
- 更多提供商持续添加中
</details>

<details>
<summary><b>如何查看对话历史？</b></summary>

对话记录存储在 SQLite 数据库中，位置：`~/.aicode/data/aicode.db`

使用任何 SQLite 客户端可以查询历史记录。CLI 历史查询功能正在开发中。
</details>

<details>
<summary><b>Token 计数不准确怎么办？</b></summary>

Token 计数使用 `tiktoken` 库，可能与实际 API 计费略有差异。这是正常现象，通常误差在 5% 以内。
</details>

<details>
<summary><b>如何贡献代码？</b></summary>

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 编写代码和测试
4. 确保所有测试通过：`pytest tests/unit/`
5. 提交 Pull Request

详见 [CONTRIBUTING.md](CONTRIBUTING.md)
</details>

## 🤝 贡献

欢迎贡献！无论是报告 Bug、提出新功能建议，还是直接提交代码，我们都非常欢迎。

请查看 [贡献指南](CONTRIBUTING.md) 了解详细信息。

### 贡献者

感谢所有为这个项目做出贡献的开发者！

<!--
在这里添加贡献者列表或使用 GitHub 的贡献者图表
![Contributors](https://contrib.rocks/image?repo=yourusername/aicode)
-->

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供强大的 LLM API
- [Anthropic](https://www.anthropic.com/) - Claude 模型支持
- [tiktoken](https://github.com/openai/tiktoken) - Token 计数工具
- 所有为开源社区做出贡献的开发者

## 📮 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/yourusername/aicode/issues)
- **功能建议**: [GitHub Discussions](https://github.com/yourusername/aicode/discussions)
- **邮件**: your.email@example.com

---

⭐ 如果这个项目对你有帮助，请给我们一个 Star！
