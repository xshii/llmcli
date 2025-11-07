# Ollama 本地部署指南

本指南介绍如何在 Apple M4（或其他 Apple Silicon）上设置 Ollama 作为 AICode 的本地 LLM 后端。

## 一、安装 Ollama

### 方法 1: 使用 Homebrew（推荐）

```bash
brew install ollama
```

### 方法 2: 下载安装包

访问 [https://ollama.com/download](https://ollama.com/download) 下载 macOS 版本。

## 二、启动 Ollama 服务

```bash
# 启动 Ollama 服务（默认端口 11434）
ollama serve
```

服务启动后会监听 `http://localhost:11434`

### 后台运行（可选）

```bash
# 使用 nohup 后台运行
nohup ollama serve > ollama.log 2>&1 &

# 或者使用 brew services（如果通过 Homebrew 安装）
brew services start ollama
```

## 三、下载模型

根据你的 M4 Mac 内存大小选择合适的模型：

### 轻量级模型（推荐用于开发测试）

```bash
# Llama 3.2 3B - 约 2GB，快速响应
ollama pull llama3.2:3b

# Qwen2.5 Coder 7B - 约 4GB，专注代码
ollama pull qwen2.5-coder:7b

# DeepSeek Coder 6.7B - 约 3.8GB，代码专用
ollama pull deepseek-coder:6.7b
```

### 中等模型（16GB+ 内存）

```bash
# Llama 3.2 7B - 约 4GB
ollama pull llama3.2:7b

# Mixtral 8x7B - 约 26GB
ollama pull mixtral:8x7b
```

### 大模型（32GB+ 内存）

```bash
# Llama 3.1 70B - 约 40GB
ollama pull llama3.1:70b
```

### 查看已下载的模型

```bash
ollama list
```

## 四、测试 Ollama

### 命令行测试

```bash
# 交互式对话
ollama run llama3.2:3b

# 单次查询
ollama run llama3.2:3b "什么是 Python 装饰器？"
```

### API 测试

```bash
# 测试 API 端点
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Hello, what are you?",
  "stream": false
}'

# 测试聊天 API
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2:3b",
  "messages": [
    {
      "role": "user",
      "content": "解释一下 Python 的列表推导式"
    }
  ],
  "stream": false
}'
```

## 五、配置 AICode 使用 Ollama

### 1. 初始化配置

```bash
python -m aicode.cli.main config init
```

### 2. 添加 Ollama 模型

```bash
# 添加 Llama 3.2 3B 模型
python -m aicode.cli.main model add llama3.2:3b ollama \
  --api-url http://localhost:11434 \
  --max-input 2048 \
  --max-output 1024 \
  --code-score 7.0

# 添加 Qwen2.5 Coder（代码专用）
python -m aicode.cli.main model add qwen2.5-coder:7b ollama \
  --api-url http://localhost:11434 \
  --max-input 4096 \
  --max-output 2048 \
  --code-score 9.0

# 添加 DeepSeek Coder
python -m aicode.cli.main model add deepseek-coder:6.7b ollama \
  --api-url http://localhost:11434 \
  --max-input 4096 \
  --max-output 2048 \
  --code-score 9.5
```

**注意**：
- Ollama 本地服务不需要 API Key，可以省略 `--api-key` 参数
- `--api-url` 必须指定为 `http://localhost:11434`
- 模型名称必须与 Ollama 中的模型名称完全一致

### 3. 查看已配置的模型

```bash
python -m aicode.cli.main model list
python -m aicode.cli.main model show llama3.2:3b
```

## 六、使用 Ollama 进行对话

### 基本对话

```bash
# 使用 Llama 3.2 3B
python -m aicode.cli.main chat "解释一下 Python 装饰器" --model llama3.2:3b

# 使用代码专用模型
python -m aicode.cli.main chat "写一个二分查找算法" --model qwen2.5-coder:7b
```

### 带文件上下文

```bash
# 让 AI 分析代码文件
python -m aicode.cli.main chat "解释这个文件的功能" \
  --file aicode/llm/client.py \
  --model deepseek-coder:6.7b

# 代码审查
python -m aicode.cli.main chat "审查这段代码并给出改进建议" \
  --file mycode.py \
  --model qwen2.5-coder:7b
```

## 七、性能优化建议

### 针对 Apple M4 的优化

1. **选择合适的模型大小**
   - 16GB 内存：推荐 3B-7B 模型
   - 24GB 内存：可以运行 7B-13B 模型
   - 32GB+ 内存：可以运行更大的模型

2. **使用量化版本**
   ```bash
   # 4-bit 量化版本（更快，占用更少内存）
   ollama pull llama3.2:3b-q4_0
   ```

3. **调整并发数**
   ```bash
   # 设置最大并发请求数
   OLLAMA_MAX_LOADED_MODELS=1 ollama serve
   ```

### 模型推荐

| 用途 | 推荐模型 | 内存需求 | 特点 |
|------|---------|---------|------|
| 快速原型开发 | llama3.2:3b | ~4GB | 响应快，轻量级 |
| 代码生成 | qwen2.5-coder:7b | ~6GB | 专注代码，准确度高 |
| 代码审查 | deepseek-coder:6.7b | ~6GB | 代码理解能力强 |
| 通用对话 | llama3.2:7b | ~6GB | 平衡性能和质量 |

## 八、故障排查

### 问题 1: 连接失败

```bash
# 检查 Ollama 服务是否运行
ps aux | grep ollama

# 检查端口是否监听
lsof -i :11434

# 重启服务
pkill ollama
ollama serve
```

### 问题 2: 模型未找到

```bash
# 确认模型已下载
ollama list

# 重新下载
ollama pull llama3.2:3b
```

### 问题 3: 内存不足

```bash
# 使用更小的模型
ollama pull llama3.2:3b

# 或使用量化版本
ollama pull llama3.2:3b-q4_0
```

### 问题 4: 响应速度慢

- 关闭其他占用内存的应用
- 使用更小的模型
- 使用量化版本
- 减少 `max_tokens` 参数

## 九、进阶配置

### 自定义模型参数

创建 Modelfile：

```dockerfile
FROM llama3.2:3b

# 设置温度（创造性）
PARAMETER temperature 0.7

# 设置 top_p（多样性）
PARAMETER top_p 0.9

# 设置系统提示词
SYSTEM """
你是一个专业的 Python 编程助手，擅长代码分析和优化建议。
"""
```

创建自定义模型：

```bash
ollama create my-python-assistant -f Modelfile
```

### 环境变量配置

```bash
# 设置模型存储路径
export OLLAMA_MODELS=/path/to/models

# 设置主机和端口
export OLLAMA_HOST=0.0.0.0:11434

# 设置日志级别
export OLLAMA_DEBUG=1
```

## 十、与云端 API 对比

| 特性 | Ollama 本地 | OpenAI API |
|------|------------|-----------|
| 成本 | 免费 | 按使用付费 |
| 隐私 | 完全私密 | 数据发送到云端 |
| 速度 | 取决于硬件 | 通常更快 |
| 模型质量 | 开源模型 | GPT-4 等闭源模型 |
| 网络依赖 | 无需网络 | 需要网络 |
| 设置复杂度 | 需要本地安装 | 只需 API Key |

## 参考资源

- Ollama 官方文档：https://ollama.com/docs
- Ollama 模型库：https://ollama.com/library
- AICode 项目：查看 README.md 和 CLI_GUIDE.md
