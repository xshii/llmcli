"""
工具注册表演示 - 回答"客户端如何知道有哪些工具"

核心思路：
1. 工具通过装饰器自动注册到全局注册表
2. 客户端根据场景从注册表获取所需工具
3. 支持按标签、名称筛选工具
"""
import sys
import os
sys.path.insert(0, '/home/user/llmcli')

from aicode.llm.tools import tool, get_registry


# ========================================
# 第一步：开发者定义工具（自动注册）
# ========================================

print("=" * 70)
print("第一步：开发者定义工具（使用 @tool 装饰器）")
print("=" * 70)

@tool(name="get_weather", description="获取城市天气", tags=["weather", "basic"])
def get_weather(location: str, unit: str = "celsius") -> str:
    """获取指定城市的天气信息"""
    return f"{location}：晴天，15°C"

print("✓ 定义了 get_weather 工具")


@tool(name="search_web", description="搜索网络", tags=["search", "basic"])
def search_web(query: str, max_results: int = 5) -> str:
    """搜索网络信息"""
    return f"找到 {max_results} 条关于 '{query}' 的结果"

print("✓ 定义了 search_web 工具")


@tool(name="calculate", description="数学计算", tags=["math", "basic"])
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

print("✓ 定义了 calculate 工具")


@tool(name="get_stock_price", description="查询股票价格", tags=["finance", "advanced"])
def get_stock_price(symbol: str) -> str:
    """获取股票实时价格"""
    return f"{symbol} 当前价格: $150.25 (+2.5%)"

print("✓ 定义了 get_stock_price 工具")


@tool(name="send_email", description="发送邮件", tags=["email", "advanced"])
def send_email(to: str, subject: str, body: str) -> str:
    """发送电子邮件"""
    return f"邮件已发送至 {to}"

print("✓ 定义了 send_email 工具")


# ========================================
# 第二步：客户端从注册表获取工具
# ========================================

print("\n" + "=" * 70)
print("第二步：客户端从注册表获取工具（无需手动指定）")
print("=" * 70)

# 获取全局注册表
registry = get_registry()

print(f"\n📦 注册表中共有 {len(registry.list_tools())} 个工具")
print(f"🏷️  共有 {len(registry.list_tags())} 个标签: {registry.list_tags()}")


# ========================================
# 场景 1：获取所有工具
# ========================================

print("\n" + "-" * 70)
print("场景 1：获取所有工具")
print("-" * 70)

all_tools = registry.get_tools()
print(f"\n客户端调用: registry.get_tools()")
print(f"返回 {len(all_tools)} 个工具:\n")

for tool_def in all_tools:
    print(f"  • {tool_def.name}: {tool_def.description}")


# ========================================
# 场景 2：按标签筛选（只要基础工具）
# ========================================

print("\n" + "-" * 70)
print("场景 2：用户问天气，只需要基础工具")
print("-" * 70)

basic_tools = registry.get_tools(tags=['basic'])
print(f"\n客户端调用: registry.get_tools(tags=['basic'])")
print(f"返回 {len(basic_tools)} 个工具:\n")

for tool_def in basic_tools:
    print(f"  • {tool_def.name}: {tool_def.description}")

print("\n➡️  这些工具会被发送给 LLM，LLM 从中选择使用")


# ========================================
# 场景 3：按标签筛选（金融工具）
# ========================================

print("\n" + "-" * 70)
print("场景 3：用户问股票，需要金融工具")
print("-" * 70)

finance_tools = registry.get_tools(tags=['finance'])
print(f"\n客户端调用: registry.get_tools(tags=['finance'])")
print(f"返回 {len(finance_tools)} 个工具:\n")

for tool_def in finance_tools:
    print(f"  • {tool_def.name}: {tool_def.description}")


# ========================================
# 场景 4：指定工具名称
# ========================================

print("\n" + "-" * 70)
print("场景 4：只需要特定工具")
print("-" * 70)

specific_tools = registry.get_tools(names=['get_weather', 'search_web'])
print(f"\n客户端调用: registry.get_tools(names=['get_weather', 'search_web'])")
print(f"返回 {len(specific_tools)} 个工具:\n")

for tool_def in specific_tools:
    print(f"  • {tool_def.name}: {tool_def.description}")


# ========================================
# 场景 5：查看工具详细信息
# ========================================

print("\n" + "-" * 70)
print("场景 5：查看工具的详细参数（用于构建 prompt）")
print("-" * 70)

weather_tool = registry.get_tool('get_weather')
print(f"\n工具名: {weather_tool.name}")
print(f"描述: {weather_tool.description}")
print(f"参数:\n")

for param_name, param_info in weather_tool.parameters['properties'].items():
    required = param_name in weather_tool.parameters.get('required', [])
    req_mark = " (必需)" if required else " (可选)"
    print(f"  • {param_name}: {param_info['type']}{req_mark}")
    print(f"    说明: {param_info['description']}")


# ========================================
# 场景 6：执行工具
# ========================================

print("\n" + "-" * 70)
print("场景 6：执行工具")
print("-" * 70)

tool_def = registry.get_tool('get_weather')
print(f"\n调用工具: {tool_def.name}")
print(f"参数: {{'location': '北京', 'unit': 'celsius'}}")

result = tool_def.execute(arguments={'location': '北京', 'unit': 'celsius'})
print(f"结果: {result}")


# ========================================
# 总结
# ========================================

print("\n" + "=" * 70)
print("💡 核心原理总结")
print("=" * 70)

print("""
1️⃣  工具定义和注册（开发者）
   - 使用 @tool 装饰器定义工具
   - 工具自动注册到全局注册表
   - 可添加标签分类

2️⃣  工具获取（客户端）
   - 从注册表按需获取工具
   - 支持按标签、名称筛选
   - 无需硬编码工具列表

3️⃣  发送给 LLM
   - 将工具列表转换为 prompt 或 API 参数
   - LLM 根据用户问题选择合适的工具
   - 客户端解析并执行工具调用

✅ 优势：
   • 工具定义集中管理
   • 客户端代码简洁
   • 易于扩展新工具
   • 支持灵活筛选
""")


# ========================================
# 完整对话流程示例（伪代码）
# ========================================

print("\n" + "=" * 70)
print("🔄 完整对话流程（伪代码）")
print("=" * 70)

print("""
def chat_with_tools(user_message: str):
    # 1. 根据场景获取工具
    tools = registry.get_tools(tags=['basic'])  # 客户端决定给哪些工具

    # 2. 构建发送给 LLM 的内容
    if model.supports_native_tools:
        # Claude、GPT-4 等原生支持
        response = llm_api.call(
            messages=[{"role": "user", "content": user_message}],
            tools=[t.to_dict() for t in tools]  # 工具列表
        )
    else:
        # DeepSeek 等不支持，用 prompt 引导
        system_prompt = build_tools_prompt(tools)  # 将工具列表转为文本说明
        response = llm_api.call(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )

    # 3. 解析响应
    if has_tool_call(response):
        tool_name = extract_tool_name(response)
        arguments = extract_arguments(response)

        # 4. 执行工具
        tool = registry.get_tool(tool_name)
        result = tool.execute(arguments)

        # 5. 返回结果给 LLM 生成最终回复
        return llm_api.call([
            {"role": "user", "content": f"工具结果: {result}"}
        ])
    else:
        return response
""")

print("\n✨ 关键点：客户端通过 registry.get_tools() 动态获取工具，")
print("   无需在代码中硬编码工具列表！")
print("=" * 70)
