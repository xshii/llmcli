"""
Function Calling 完整使用示例

演示：
1. 如何定义和注册工具
2. 客户端如何自动获取可用工具
3. 工具的执行流程
"""
from aicode.llm.tools import tool, get_registry, ToolDefinition
from aicode.llm.client import LLMClient
from aicode.models.schema import ModelSchema


# ========================================
# 第一步：定义工具（使用装饰器自动注册）
# ========================================

@tool(name="get_weather", description="获取指定城市的天气信息", tags=["weather", "basic"])
def get_weather(location: str, unit: str = "celsius") -> str:
    """
    获取天气信息

    Args:
        location: 城市名称，如：北京、上海
        unit: 温度单位，celsius 或 fahrenheit

    Returns:
        天气描述
    """
    # 实际应该调用天气 API，这里模拟返回
    temp = 15 if unit == "celsius" else 59
    return f"{location}：晴天，温度 {temp}°{'C' if unit == 'celsius' else 'F'}"


@tool(name="search_web", description="搜索网络信息", tags=["search", "basic"])
def search_web(query: str, max_results: int = 5) -> str:
    """
    搜索网络

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        搜索结果摘要
    """
    # 实际应该调用搜索 API
    return f"找到 {max_results} 条关于 '{query}' 的结果"


@tool(name="calculate", description="执行数学计算", tags=["math", "basic"])
def calculate(expression: str) -> str:
    """
    计算数学表达式

    Args:
        expression: 数学表达式，如：2+2, 10*5

    Returns:
        计算结果
    """
    try:
        # 注意：实际使用时应该用更安全的计算方式
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


@tool(name="get_stock_price", description="获取股票价格", tags=["finance", "advanced"])
def get_stock_price(symbol: str) -> str:
    """
    获取股票实时价格

    Args:
        symbol: 股票代码，如：AAPL, TSLA

    Returns:
        股票价格信息
    """
    # 实际应该调用股票 API
    return f"{symbol} 当前价格: $150.25 (+2.5%)"


# ========================================
# 第二步：客户端使用工具
# ========================================

class ChatWithTools:
    """带工具的对话客户端"""

    def __init__(self, model: ModelSchema, api_key: str):
        """
        初始化客户端

        Args:
            model: 模型配置
            api_key: API 密钥
        """
        self.client = LLMClient(model, api_key=api_key)
        self.registry = get_registry()
        self.conversation_history = []

    def chat(
        self,
        user_message: str,
        tool_filter_tags: list = None,
        tool_filter_names: list = None
    ) -> str:
        """
        发送对话（自动处理工具调用）

        Args:
            user_message: 用户消息
            tool_filter_tags: 可用工具的标签筛选（如 ['weather', 'search']）
            tool_filter_names: 可用工具的名称列表（如 ['get_weather']）

        Returns:
            助手回复
        """
        # 1. 添加用户消息到历史
        self.conversation_history.append({
            'role': 'user',
            'content': user_message
        })

        # 2. 获取可用工具（这里就是关键：根据需求筛选工具）
        available_tools = self._get_available_tools(
            tags=tool_filter_tags,
            names=tool_filter_names
        )

        print(f"\n🔧 可用工具 ({len(available_tools)} 个):")
        for t in available_tools:
            print(f"  - {t.name}: {t.description}")

        # 3. 发送请求到 LLM（带工具列表）
        # 注意：这里需要根据模型能力选择适配器
        # 简化示例，假设我们直接构建工具提示
        system_prompt = self._build_tools_prompt(available_tools)
        messages = [
            {'role': 'system', 'content': system_prompt},
            *self.conversation_history
        ]

        response = self.client.chat(messages)

        # 4. 解析响应（检查是否有工具调用）
        tool_call = self._parse_tool_call(response)

        if tool_call:
            # 5. 执行工具
            print(f"\n⚡ 调用工具: {tool_call['tool']}")
            print(f"   参数: {tool_call['arguments']}")

            tool_def = self.registry.get_tool(tool_call['tool'])
            if tool_def:
                try:
                    result = tool_def.execute(tool_call['arguments'])
                    print(f"   结果: {result}")

                    # 6. 将工具结果返回给 LLM
                    self.conversation_history.append({
                        'role': 'assistant',
                        'content': f"[调用工具 {tool_call['tool']}]"
                    })
                    self.conversation_history.append({
                        'role': 'user',
                        'content': f"工具执行结果: {result}"
                    })

                    # 7. 获取最终回复
                    final_response = self.client.chat([
                        {'role': 'system', 'content': '根据工具结果回复用户'},
                        *self.conversation_history
                    ])

                    self.conversation_history.append({
                        'role': 'assistant',
                        'content': final_response
                    })

                    return final_response

                except Exception as e:
                    return f"工具执行失败: {e}"
            else:
                return f"未找到工具: {tool_call['tool']}"
        else:
            # 普通文本回复
            self.conversation_history.append({
                'role': 'assistant',
                'content': response
            })
            return response

    def _get_available_tools(
        self,
        tags: list = None,
        names: list = None
    ) -> list:
        """
        获取可用工具列表

        这是关键方法：根据不同场景筛选工具

        策略：
        1. 如果指定了 names，只使用这些工具
        2. 如果指定了 tags，使用带这些标签的工具
        3. 否则使用所有基础工具（'basic' 标签）

        Args:
            tags: 标签筛选
            names: 名称筛选

        Returns:
            ToolDefinition 列表
        """
        if names:
            # 使用指定工具
            return self.registry.get_tools(names=names)
        elif tags:
            # 使用带指定标签的工具
            return self.registry.get_tools(tags=tags)
        else:
            # 默认：只使用基础工具
            return self.registry.get_tools(tags=['basic'])

    def _build_tools_prompt(self, tools: list) -> str:
        """构建工具说明的 system prompt"""
        if not tools:
            return "你是一个有帮助的助手。"

        lines = ["你是一个有帮助的助手，可以使用以下工具：\n"]

        for tool in tools:
            lines.append(f"### {tool.name}")
            lines.append(f"描述: {tool.description}")
            lines.append("参数:")

            props = tool.parameters.get('properties', {})
            required = tool.parameters.get('required', [])

            for param_name, param_info in props.items():
                req_mark = " (必需)" if param_name in required else ""
                lines.append(f"  - {param_name}: {param_info.get('type')}{req_mark}")
                lines.append(f"    {param_info.get('description', '')}")
            lines.append("")

        lines.append("要使用工具，请返回 JSON 格式：")
        lines.append("```json")
        lines.append('{"tool": "工具名", "arguments": {"参数名": "值"}}')
        lines.append("```")

        return "\n".join(lines)

    def _parse_tool_call(self, response: str) -> dict:
        """解析工具调用（简化版）"""
        import re
        import json

        # 提取 JSON 代码块
        pattern = r'```(?:json)?\s*\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)

        if match:
            try:
                data = json.loads(match.group(1).strip())
                if 'tool' in data and 'arguments' in data:
                    return data
            except:
                pass

        return None


# ========================================
# 第三步：使用示例
# ========================================

def main():
    """主函数：演示完整流程"""

    # 1. 查看已注册的工具
    print("=" * 60)
    print("已注册的工具:")
    print("=" * 60)
    registry = get_registry()
    for tool_name in registry.list_tools():
        tool_def = registry.get_tool(tool_name)
        print(f"✓ {tool_name}: {tool_def.description}")

    print("\n" + "=" * 60)
    print("按标签分类:")
    print("=" * 60)
    for tag in registry.list_tags():
        tools = registry.get_tools(tags=[tag])
        print(f"\n[{tag}] 标签的工具:")
        for t in tools:
            print(f"  - {t.name}")

    # 2. 模拟客户端对话
    print("\n" + "=" * 60)
    print("对话示例:")
    print("=" * 60)

    # 创建模型配置（示例）
    model = ModelSchema(
        name="deepseek-chat",
        provider="deepseek",
        api_key="sk-xxx",
        api_url="https://api.deepseek.com/v1/chat/completions"
    )

    # 创建客户端
    chat = ChatWithTools(model, api_key="sk-xxx")

    # 场景 1：只使用天气工具
    print("\n[场景 1] 用户问天气，只提供天气工具")
    print("-" * 60)
    # response = chat.chat(
    #     "北京今天天气怎么样？",
    #     tool_filter_names=['get_weather']  # 只给天气工具
    # )
    # print(f"回复: {response}")

    # 场景 2：使用所有基础工具
    print("\n[场景 2] 复杂问题，提供所有基础工具")
    print("-" * 60)
    # response = chat.chat(
    #     "帮我搜索一下 Python 教程，并计算 25*4",
    #     tool_filter_tags=['basic']  # 所有基础工具
    # )
    # print(f"回复: {response}")

    # 场景 3：高级工具（金融）
    print("\n[场景 3] 金融查询，提供金融工具")
    print("-" * 60)
    # response = chat.chat(
    #     "AAPL 股票现在多少钱？",
    #     tool_filter_tags=['finance']  # 金融工具
    # )
    # print(f"回复: {response}")

    print("\n" + "=" * 60)
    print("工具注册表的优势:")
    print("=" * 60)
    print("""
    ✅ 工具定义和实现分离
    ✅ 装饰器自动注册，无需手动管理
    ✅ 按标签灵活筛选工具
    ✅ 客户端无需知道所有工具细节
    ✅ 易于扩展和维护
    """)


if __name__ == '__main__':
    main()
