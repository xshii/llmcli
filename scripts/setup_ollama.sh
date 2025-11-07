#!/bin/bash

# Ollama 快速设置脚本
# 适用于 macOS（包括 Apple M4）

set -e

echo "====================================="
echo "Ollama 快速设置脚本"
echo "====================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否在 macOS 上运行
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}错误: 此脚本仅支持 macOS${NC}"
    exit 1
fi

# 检查是否安装了 Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}未检测到 Homebrew，正在安装...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo -e "${GREEN}✓ Homebrew 已安装${NC}"
fi

# 检查是否安装了 Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}正在安装 Ollama...${NC}"
    brew install ollama
    echo -e "${GREEN}✓ Ollama 安装完成${NC}"
else
    echo -e "${GREEN}✓ Ollama 已安装${NC}"
    ollama --version
fi

echo ""
echo "====================================="
echo "启动 Ollama 服务"
echo "====================================="
echo ""

# 检查 Ollama 服务是否已运行
if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✓ Ollama 服务已在运行${NC}"
else
    echo -e "${YELLOW}正在启动 Ollama 服务...${NC}"
    # 在后台启动 Ollama
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 2

    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}✓ Ollama 服务启动成功${NC}"
    else
        echo -e "${RED}✗ Ollama 服务启动失败${NC}"
        echo "请手动运行: ollama serve"
        exit 1
    fi
fi

echo ""
echo "====================================="
echo "下载推荐模型"
echo "====================================="
echo ""

# 询问用户想要下载的模型
echo "请选择要下载的模型:"
echo "1) llama3.2:3b (推荐，约 2GB，快速)"
echo "2) qwen2.5-coder:7b (代码专用，约 4GB)"
echo "3) deepseek-coder:6.7b (代码专用，约 3.8GB)"
echo "4) 全部下载"
echo "5) 跳过"
echo ""
read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo -e "${YELLOW}正在下载 llama3.2:3b...${NC}"
        ollama pull llama3.2:3b
        echo -e "${GREEN}✓ llama3.2:3b 下载完成${NC}"
        ;;
    2)
        echo -e "${YELLOW}正在下载 qwen2.5-coder:7b...${NC}"
        ollama pull qwen2.5-coder:7b
        echo -e "${GREEN}✓ qwen2.5-coder:7b 下载完成${NC}"
        ;;
    3)
        echo -e "${YELLOW}正在下载 deepseek-coder:6.7b...${NC}"
        ollama pull deepseek-coder:6.7b
        echo -e "${GREEN}✓ deepseek-coder:6.7b 下载完成${NC}"
        ;;
    4)
        echo -e "${YELLOW}正在下载所有推荐模型...${NC}"
        ollama pull llama3.2:3b
        echo -e "${GREEN}✓ llama3.2:3b 下载完成${NC}"
        ollama pull qwen2.5-coder:7b
        echo -e "${GREEN}✓ qwen2.5-coder:7b 下载完成${NC}"
        ollama pull deepseek-coder:6.7b
        echo -e "${GREEN}✓ deepseek-coder:6.7b 下载完成${NC}"
        ;;
    5)
        echo -e "${YELLOW}跳过模型下载${NC}"
        ;;
    *)
        echo -e "${RED}无效的选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "====================================="
echo "验证安装"
echo "====================================="
echo ""

# 测试 Ollama API
echo "测试 Ollama API..."
response=$(curl -s http://localhost:11434/api/tags)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Ollama API 正常工作${NC}"
    echo ""
    echo "已安装的模型:"
    ollama list
else
    echo -e "${RED}✗ Ollama API 无响应${NC}"
    echo "请检查服务状态: ps aux | grep ollama"
    exit 1
fi

echo ""
echo "====================================="
echo "配置 AICode"
echo "====================================="
echo ""

echo "是否要自动配置 AICode 使用 Ollama? (y/n)"
read -p "> " configure_aicode

if [[ "$configure_aicode" =~ ^[Yy]$ ]]; then
    # 检查 Python 和 aicode 是否可用
    if command -v python3 &> /dev/null; then
        echo -e "${YELLOW}初始化 AICode 配置...${NC}"
        python3 -m aicode.cli.main config init 2>/dev/null || true

        # 添加已下载的模型
        case $choice in
            1|4)
                echo -e "${YELLOW}添加 llama3.2:3b 到 AICode...${NC}"
                python3 -m aicode.cli.main model add llama3.2:3b ollama \
                    --api-url http://localhost:11434 \
                    --max-input 2048 \
                    --max-output 1024 \
                    --code-score 7.0 2>/dev/null || true
                echo -e "${GREEN}✓ 已添加 llama3.2:3b${NC}"
                ;;
        esac

        case $choice in
            2|4)
                echo -e "${YELLOW}添加 qwen2.5-coder:7b 到 AICode...${NC}"
                python3 -m aicode.cli.main model add qwen2.5-coder:7b ollama \
                    --api-url http://localhost:11434 \
                    --max-input 4096 \
                    --max-output 2048 \
                    --code-score 9.0 2>/dev/null || true
                echo -e "${GREEN}✓ 已添加 qwen2.5-coder:7b${NC}"
                ;;
        esac

        case $choice in
            3|4)
                echo -e "${YELLOW}添加 deepseek-coder:6.7b 到 AICode...${NC}"
                python3 -m aicode.cli.main model add deepseek-coder:6.7b ollama \
                    --api-url http://localhost:11434 \
                    --max-input 4096 \
                    --max-output 2048 \
                    --code-score 9.5 2>/dev/null || true
                echo -e "${GREEN}✓ 已添加 deepseek-coder:6.7b${NC}"
                ;;
        esac
    else
        echo -e "${RED}未找到 Python3，请手动配置 AICode${NC}"
    fi
fi

echo ""
echo "====================================="
echo "设置完成！"
echo "====================================="
echo ""
echo -e "${GREEN}Ollama 已成功设置并运行在: http://localhost:11434${NC}"
echo ""
echo "快速测试:"
echo "  ollama run llama3.2:3b '什么是 Python?'"
echo ""
echo "使用 AICode:"
echo "  python -m aicode.cli.main chat '解释 Python 装饰器' --model llama3.2:3b"
echo ""
echo "查看详细文档:"
echo "  cat OLLAMA_SETUP.md"
echo ""
echo "查看示例代码:"
echo "  python examples/ollama_example.py"
echo ""
echo -e "${YELLOW}注意: Ollama 服务正在后台运行${NC}"
echo "停止服务: pkill ollama"
echo "查看日志: tail -f /tmp/ollama.log"
echo ""
