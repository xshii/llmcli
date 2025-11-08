# Function Calling 多模型支持设计方案

## 1. 核心架构

### 1.1 模型能力分层

```
├─ 原生支持 Function Calling
│  ├─ Claude 3.x (tool_use 格式)
│  ├─ GPT-4/3.5 (function_call 格式)
│  └─ Gemini Pro (function_calling 格式)
│
└─ 不支持 Function Calling (通过 Prompt 引导)
   ├─ DeepSeek
   ├─ Qwen
   └─ 开源模型 (LLaMA, Mistral 等)
```

### 1.2 统一抽象层

```python
# 统一的工具定义格式（兼容所有模型）
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema

# 统一的工具调用结果
class ToolCall:
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str
```

## 2. Claude 的工具使用格式

### 2.1 请求格式

```json
{
  "model": "claude-3-5-sonnet-20241022",
  "messages": [...],
  "tools": [
    {
      "name": "get_weather",
      "description": "获取天气信息",
      "input_schema": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "城市名"}
        },
        "required": ["location"]
      }
    }
  ],
  "tool_choice": {"type": "auto"}  // auto, any, tool
}
```

### 2.2 响应格式

**工具调用响应：**
```json
{
  "role": "assistant",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01AbC123",
      "name": "get_weather",
      "input": {"location": "北京"}
    }
  ],
  "stop_reason": "tool_use"
}
```

**纯文本响应：**
```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "我可以帮你查询天气..."
    }
  ],
  "stop_reason": "end_turn"
}
```

**混合响应（先说话再调用工具）：**
```json
{
  "content": [
    {"type": "text", "text": "好的，我来帮你查询"},
    {"type": "tool_use", "id": "toolu_01", "name": "get_weather", "input": {...}}
  ]
}
```

### 2.3 工具结果返回

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01AbC123",
      "content": "北京：晴，15°C"
    }
  ]
}
```

## 3. 不支持 Function Calling 的模型处理方案

### 3.1 通过 Prompt 引导生成 JSON

**系统提示模板：**

```python
FUNCTION_CALLING_PROMPT = """You are an AI assistant with access to the following tools:

{tools_description}

To use a tool, respond ONLY with a JSON object in this format:
```json
{
  "tool": "tool_name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

If you don't need to use a tool, respond normally with text.

IMPORTANT RULES:
1. Use ONLY the tools listed above
2. Follow the exact JSON format
3. Do not add explanations inside the JSON block
4. Validate all required parameters

Available tools:
{tools_list}
"""
```

**工具描述格式：**

```python
def format_tools_for_prompt(tools: List[ToolDefinition]) -> str:
    """格式化工具列表为 prompt"""
    lines = []
    for tool in tools:
        lines.append(f"### {tool.name}")
        lines.append(f"Description: {tool.description}")
        lines.append("Parameters:")

        for param_name, param_info in tool.parameters.get("properties", {}).items():
            required = param_name in tool.parameters.get("required", [])
            req_mark = " (REQUIRED)" if required else ""
            lines.append(f"  - {param_name}: {param_info.get('type')}{req_mark}")
            lines.append(f"    {param_info.get('description', '')}")
        lines.append("")

    return "\n".join(lines)

# 示例输出：
"""
### get_weather
Description: 获取指定城市的天气信息
Parameters:
  - location: string (REQUIRED)
    城市名称，如：北京、上海
  - unit: string
    温度单位 (celsius 或 fahrenheit)

### search_web
Description: 搜索网络信息
Parameters:
  - query: string (REQUIRED)
    搜索关键词
"""
```

### 3.2 解析模型输出

```python
import re
import json

class ToolCallParser:
    """解析模型输出的工具调用"""

    # 匹配 JSON 代码块
    JSON_PATTERN = re.compile(
        r'```(?:json)?\s*\n(.*?)\n```',
        re.DOTALL
    )

    @classmethod
    def parse(cls, response: str) -> Optional[ToolCall]:
        """
        解析响应文本，提取工具调用

        Returns:
            ToolCall 或 None（如果是普通文本响应）
        """
        # 1. 尝试提取 JSON 代码块
        match = cls.JSON_PATTERN.search(response)
        if not match:
            return None  # 普通文本响应

        json_str = match.group(1).strip()

        # 2. 解析 JSON
        try:
            data = json.loads(json_str)

            # 3. 验证格式
            if "tool" not in data or "arguments" not in data:
                logger.warning("Invalid tool call format: missing 'tool' or 'arguments'")
                return None

            return ToolCall(
                tool_name=data["tool"],
                arguments=data["arguments"],
                call_id=generate_call_id()
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool call JSON: {e}")
            return None
```

### 3.3 示例：不同模型的响应

**DeepSeek 响应：**
```
好的，我来帮你查询北京的天气。

```json
{
  "tool": "get_weather",
  "arguments": {
    "location": "北京",
    "unit": "celsius"
  }
}
```

根据查询结果...
```

**解析结果：**
```python
ToolCall(
    tool_name="get_weather",
    arguments={"location": "北京", "unit": "celsius"},
    call_id="call_abc123"
)
```

## 4. 统一客户端实现

### 4.1 模型能力检测

```python
@dataclass
class ModelCapabilities:
    """模型能力"""
    supports_native_tools: bool  # 是否原生支持 function calling
    tool_format: str  # 'claude', 'openai', 'gemini', 'prompt'
    supports_streaming: bool
    supports_system_message: bool
```

### 4.2 统一客户端

```python
class UnifiedLLMClient:
    """统一的 LLM 客户端，支持多种模型的 function calling"""

    def __init__(self, model: ModelSchema, capabilities: ModelCapabilities):
        self.model = model
        self.capabilities = capabilities
        self.adapter = self._create_adapter()

    def _create_adapter(self):
        """根据模型能力创建适配器"""
        if self.capabilities.supports_native_tools:
            if self.capabilities.tool_format == 'claude':
                return ClaudeToolAdapter()
            elif self.capabilities.tool_format == 'openai':
                return OpenAIToolAdapter()
            # ... 其他原生支持的模型
        else:
            return PromptBasedToolAdapter()

    def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[ToolDefinition],
        **kwargs
    ) -> Union[str, ToolCall]:
        """
        发送带工具的对话请求

        Returns:
            str: 普通文本响应
            ToolCall: 工具调用
        """
        # 1. 适配器转换请求格式
        adapted_request = self.adapter.prepare_request(
            messages, tools, **kwargs
        )

        # 2. 发送请求
        response = self._make_request(adapted_request)

        # 3. 适配器解析响应
        return self.adapter.parse_response(response)
```

### 4.3 适配器接口

```python
class ToolAdapter(ABC):
    """工具调用适配器基类"""

    @abstractmethod
    def prepare_request(
        self,
        messages: List[Dict],
        tools: List[ToolDefinition],
        **kwargs
    ) -> Dict[str, Any]:
        """准备 API 请求"""
        pass

    @abstractmethod
    def parse_response(self, response: Dict) -> Union[str, ToolCall]:
        """解析 API 响应"""
        pass


class ClaudeToolAdapter(ToolAdapter):
    """Claude 工具调用适配器"""

    def prepare_request(self, messages, tools, **kwargs):
        return {
            "model": kwargs.get("model"),
            "messages": messages,
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters
                }
                for t in tools
            ],
            "tool_choice": kwargs.get("tool_choice", {"type": "auto"})
        }

    def parse_response(self, response):
        content = response.get("content", [])

        # 查找 tool_use
        for block in content:
            if block.get("type") == "tool_use":
                return ToolCall(
                    tool_name=block["name"],
                    arguments=block["input"],
                    call_id=block["id"]
                )

        # 纯文本响应
        text_blocks = [b["text"] for b in content if b.get("type") == "text"]
        return "".join(text_blocks)


class PromptBasedToolAdapter(ToolAdapter):
    """基于 Prompt 的工具调用适配器（不支持原生 function calling 的模型）"""

    def prepare_request(self, messages, tools, **kwargs):
        # 1. 生成工具说明
        tools_prompt = format_tools_for_prompt(tools)
        system_prompt = FUNCTION_CALLING_PROMPT.format(
            tools_description=tools_prompt,
            tools_list=tools_prompt
        )

        # 2. 注入系统消息
        enhanced_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]

        return {
            "model": kwargs.get("model"),
            "messages": enhanced_messages,
            "temperature": kwargs.get("temperature", 0.7)
        }

    def parse_response(self, response):
        text = response.get("content", "")

        # 尝试解析工具调用
        tool_call = ToolCallParser.parse(text)
        if tool_call:
            return tool_call

        # 普通文本响应
        return text
```

## 5. 完整使用示例

### 5.1 定义工具

```python
# 工具定义
weather_tool = ToolDefinition(
    name="get_weather",
    description="获取指定城市的天气信息",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "城市名称"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "温度单位"
            }
        },
        "required": ["location"]
    }
)

# 工具实现
def get_weather(location: str, unit: str = "celsius") -> str:
    """实际的天气查询逻辑"""
    # 调用天气 API
    return f"{location}：晴，15°C"
```

### 5.2 使用客户端

```python
# 创建客户端
client = UnifiedLLMClient(
    model=model_schema,
    capabilities=ModelCapabilities(
        supports_native_tools=False,  # DeepSeek 不支持
        tool_format='prompt',
        supports_streaming=True,
        supports_system_message=True
    )
)

# 对话
messages = [
    {"role": "user", "content": "北京今天天气怎么样？"}
]

tools = [weather_tool]

# 第一次调用：模型决定是否使用工具
result = client.chat_with_tools(messages, tools)

if isinstance(result, ToolCall):
    # 模型决定调用工具
    print(f"调用工具: {result.tool_name}")
    print(f"参数: {result.arguments}")

    # 执行工具
    if result.tool_name == "get_weather":
        tool_result = get_weather(**result.arguments)

    # 将结果返回给模型
    messages.append({
        "role": "assistant",
        "content": f"使用工具 {result.tool_name}"
    })
    messages.append({
        "role": "user",
        "content": f"工具执行结果: {tool_result}"
    })

    # 第二次调用：让模型总结
    final_response = client.chat_with_tools(messages, tools)
    print(f"最终回复: {final_response}")

else:
    # 普通文本响应
    print(f"回复: {result}")
```

## 6. 数据库 Schema 扩展

需要在 `ModelSchema` 中添加字段：

```python
@dataclass
class ModelSchema:
    # ... 现有字段

    # 新增：工具调用能力
    supports_native_tools: bool = False
    tool_format: str = "prompt"  # 'claude', 'openai', 'gemini', 'prompt'

    # 新增：支持的功能
    supports_system_message: bool = True
    supports_streaming_tools: bool = False  # 是否支持流式工具调用
```

## 7. 配置示例

```yaml
# config/models.yaml
models:
  - name: claude-3-5-sonnet-20241022
    provider: anthropic
    supports_native_tools: true
    tool_format: claude
    supports_system_message: true

  - name: gpt-4-turbo
    provider: openai
    supports_native_tools: true
    tool_format: openai
    supports_system_message: true

  - name: deepseek-chat
    provider: deepseek
    supports_native_tools: false
    tool_format: prompt
    supports_system_message: true

  - name: qwen-plus
    provider: qwen
    supports_native_tools: false
    tool_format: prompt
    supports_system_message: true
```

## 8. 优势总结

✅ **统一接口**：上层代码无需关心模型差异
✅ **灵活扩展**：新增模型只需添加适配器
✅ **降级兼容**：不支持原生 function calling 的模型自动使用 prompt 方案
✅ **类型安全**：统一的数据结构
✅ **可测试**：每个适配器独立可测

## 9. 下一步实现计划

1. ✅ 定义统一的工具数据结构
2. ✅ 实现基础适配器接口
3. ⬜ 实现 Claude 适配器
4. ⬜ 实现 OpenAI 适配器
5. ⬜ 实现基于 Prompt 的适配器
6. ⬜ 添加工具注册和管理
7. ⬜ 添加工具调用历史记录
8. ⬜ 添加工具调用的重试和错误处理
