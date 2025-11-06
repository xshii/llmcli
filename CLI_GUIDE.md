# AICode CLI 使用指南

## 🚀 快速开始

### 1. 安装

```bash
# 开发模式安装
cd /path/to/llmcli
source venv/bin/activate
pip install -e .

# 或直接运行
python -m aicode.cli.main --help
```

### 2. 初始化配置

```bash
# 创建默认配置
aicode config init

# 设置 API Key
aicode config set global.api_key sk-your-openai-key

# 设置 API URL（可选）
aicode config set global.api_url https://api.openai.com/v1

# 设置默认模型
aicode config set global.default_model gpt-4
```

### 3. 添加模型

```bash
# 添加 OpenAI GPT-4
aicode model add gpt-4 openai \
  --max-input 8192 \
  --max-output 4096 \
  --code-score 9.0 \
  --api-url https://api.openai.com/v1

# 添加 Claude
aicode model add claude-3-opus anthropic \
  --max-input 200000 \
  --max-output 4096 \
  --code-score 9.5 \
  --api-url https://api.anthropic.com/v1
```

---

## 📖 命令详解

### config - 配置管理

```bash
# 初始化配置
aicode config init

# 查看所有配置
aicode config show

# 获取配置值
aicode config get global.api_key

# 设置配置值
aicode config set global.api_key sk-xxx
aicode config set global.default_model gpt-4
```

**配置文件位置**: `~/.aicode/config.yaml`

**配置结构**:
```yaml
global:
  api_key: sk-xxx
  api_url: https://api.openai.com/v1
  default_model: gpt-4

models: []
```

---

### model - 模型管理

```bash
# 列出所有模型
aicode model list

# 按提供商筛选
aicode model list --provider openai

# 添加模型
aicode model add <name> <provider> [options]

# 查看模型详情
aicode model show gpt-4

# 删除模型
aicode model remove gpt-4
```

**添加模型示例**:
```bash
aicode model add gpt-4-turbo openai \
  --max-input 128000 \
  --max-output 4096 \
  --context-window 128000 \
  --code-score 9.0 \
  --api-key sk-xxx \
  --api-url https://api.openai.com/v1
```

**模型列表输出**:
```
Name         | Provider   | Max Input | Max Output | Code Score
-----------------------------------------------------------------
gpt-4        | openai     | 8192      | 4096       | 9.0
claude-3     | anthropic  | 200000    | 4096       | 9.5
```

---

### chat - 与LLM对话

```bash
# 简单对话
aicode chat "你好，介绍一下Python"

# 指定模型
aicode chat "写一个快速排序" --model gpt-4

# 包含文件内容
aicode chat "解释这个文件" --file main.py

# 调整参数
aicode chat "生成代码" \
  --temperature 0.5 \
  --max-tokens 2000

# 交互模式（不提供消息时自动进入）
aicode chat
```

**带文件上下文**:
```bash
# 解释代码
aicode chat "这段代码做什么?" --file app.py

# 添加功能
aicode chat "添加错误处理" --file utils.py

# 查找bug
aicode chat "有什么问题?" --file buggy.py
```

**输出示例**:
```
ℹ Model: gpt-4
ℹ Input tokens: 150
ℹ Estimated cost: $0.004500
------------------------------------------------------------
这是一个简单的Python函数，用于...

[响应内容]
------------------------------------------------------------
✓ Response received
```

---

## 🎯 使用场景

### 场景1: 代码解释

```bash
# 解释文件
aicode chat "详细解释这个模块" --file aicode/models/schema.py

# 解释函数
aicode chat "这个函数的作用是什么?" --file utils.py
```

### 场景2: 代码生成

```bash
# 生成函数
aicode chat "写一个读取JSON文件的函数，包含错误处理"

# 生成测试
aicode chat "为这个函数生成pytest测试" --file utils.py
```

### 场景3: 代码审查

```bash
# 查找bug
aicode chat "检查这段代码有没有问题" --file app.py

# 性能优化
aicode chat "如何优化这段代码的性能?" --file slow_func.py
```

### 场景4: 多模型比较

```bash
# 使用 GPT-4
aicode chat "解释快速排序" --model gpt-4

# 使用 Claude
aicode chat "解释快速排序" --model claude-3
```

---

## 📁 项目结构

```
~/.aicode/
├── config.yaml          # 配置文件
└── aicode.db            # 模型数据库

aicode/
├── cli/                 # CLI相关
│   ├── main.py          # 入口
│   ├── commands/        # 命令目录
│   │   ├── chat.py
│   │   ├── model.py
│   │   └── config.py
│   └── utils/           # CLI工具
│       ├── file_ops.py
│       └── output.py
├── llm/                 # LLM相关
│   ├── client.py        # API客户端
│   ├── token_manager.py
│   └── exceptions.py
├── config/              # 配置管理
│   ├── constants.py
│   └── config_manager.py
├── database/            # 数据库
│   └── db_manager.py
└── models/              # 数据模型
    └── schema.py
```

---

## 🔧 高级用法

### 环境变量

```bash
# 设置 API Key（优先级高于配置文件）
export AICODE_API_KEY=sk-xxx
export AICODE_API_URL=https://api.openai.com/v1
```

### Debug模式

```bash
# 启用调试日志
aicode --debug chat "test"

# 查看详细错误
aicode --debug config show
```

### 批量操作

```bash
# 从配置文件批量导入模型（TODO）
aicode model import models.yaml

# 导出模型配置（TODO）
aicode model export > models.yaml
```

---

## 🐛 故障排查

### 问题1: "Config not found"

```bash
# 解决方案：初始化配置
aicode config init
```

### 问题2: "Model not found"

```bash
# 查看可用模型
aicode model list

# 添加模型
aicode model add gpt-4 openai ...
```

### 问题3: "API key not configured"

```bash
# 设置 API Key
aicode config set global.api_key sk-xxx
```

### 问题4: API调用失败

```bash
# 检查配置
aicode config show

# 检查模型设置
aicode model show gpt-4

# 使用 debug 模式
aicode --debug chat "test"
```

---

## 📝 下一步计划

### Phase 3B - 高级功能

- [ ] 流式响应支持
- [ ] 对话历史管理
- [ ] 代码编辑功能
- [ ] VSCode 扩展集成
- [ ] 批量文件处理

### Phase 4 - VSCode 集成

- [ ] JSON-RPC 服务器
- [ ] VSCode 扩展开发
- [ ] 编辑器集成（侧边栏、命令）
- [ ] 代码 diff 显示

---

**当前版本**: 0.1.0
**状态**: Phase 3A 完成 ✅
