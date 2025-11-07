#!/bin/bash

# 测试 Ollama 连接的脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "====================================="
echo "Ollama 连接测试"
echo "====================================="
echo ""

# 1. 检查 Ollama 服务是否运行
echo "1. 检查 Ollama 服务..."
if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✓ Ollama 服务正在运行${NC}"
else
    echo -e "${RED}✗ Ollama 服务未运行${NC}"
    echo "请先启动服务: ollama serve"
    exit 1
fi

# 2. 测试端口连接
echo ""
echo "2. 测试端口连接..."
if curl -s http://localhost:11434 > /dev/null; then
    echo -e "${GREEN}✓ 端口 11434 可访问${NC}"
else
    echo -e "${RED}✗ 无法连接到端口 11434${NC}"
    exit 1
fi

# 3. 获取模型列表
echo ""
echo "3. 获取已安装的模型..."
response=$(curl -s http://localhost:11434/api/tags)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API 响应正常${NC}"
    echo ""
    echo "已安装的模型:"
    ollama list
else
    echo -e "${RED}✗ API 无响应${NC}"
    exit 1
fi

# 4. 测试对话 API（如果有模型）
echo ""
echo "4. 测试对话 API..."

# 获取第一个可用的模型
first_model=$(ollama list | tail -n +2 | head -n 1 | awk '{print $1}')

if [ -z "$first_model" ]; then
    echo -e "${YELLOW}⚠ 未找到可用模型${NC}"
    echo "请先下载模型: ollama pull llama3.2:3b"
else
    echo "使用模型: $first_model"
    echo "发送测试消息..."

    response=$(curl -s http://localhost:11434/api/chat -d "{
        \"model\": \"$first_model\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}],
        \"stream\": false
    }")

    if echo "$response" | grep -q "message"; then
        echo -e "${GREEN}✓ 对话 API 工作正常${NC}"
        # 提取响应内容
        content=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['message']['content'][:100])" 2>/dev/null || echo "")
        if [ ! -z "$content" ]; then
            echo "AI 响应: $content..."
        fi
    else
        echo -e "${RED}✗ 对话 API 测试失败${NC}"
        echo "响应: $response"
    fi
fi

# 5. 检查 AICode 配置
echo ""
echo "5. 检查 AICode 配置..."
if [ -f "$HOME/.aicode/config.yaml" ]; then
    echo -e "${GREEN}✓ AICode 配置文件存在${NC}"

    # 检查是否配置了 Ollama 模型
    if python3 -m aicode.cli.main model list 2>/dev/null | grep -q "ollama"; then
        echo -e "${GREEN}✓ 已配置 Ollama 模型${NC}"
        echo ""
        echo "已配置的 Ollama 模型:"
        python3 -m aicode.cli.main model list 2>/dev/null | grep "ollama" || true
    else
        echo -e "${YELLOW}⚠ 未配置 Ollama 模型${NC}"
        echo "运行以下命令添加模型:"
        echo "  python -m aicode.cli.main model add $first_model ollama \\"
        echo "    --api-url http://localhost:11434 \\"
        echo "    --max-input 2048 \\"
        echo "    --max-output 1024 \\"
        echo "    --code-score 7.0"
    fi
else
    echo -e "${YELLOW}⚠ AICode 未初始化${NC}"
    echo "运行以下命令初始化:"
    echo "  python -m aicode.cli.main config init"
fi

echo ""
echo "====================================="
echo "测试完成"
echo "====================================="
echo ""

if [ ! -z "$first_model" ]; then
    echo "你可以使用以下命令测试对话:"
    echo "  python -m aicode.cli.main chat '你好' --model $first_model"
    echo ""
    echo "或者运行示例脚本:"
    echo "  python examples/ollama_example.py"
fi

echo ""
