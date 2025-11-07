#!/usr/bin/env python3
"""
测试污染清理功能
"""
from aicode.llm.code_edit import CodeEditParser


def test_pollution_cleaning():
    """测试清理污染标签"""
    print("TEST: Pollution Cleaning")
    print("=" * 60)

    # 模拟 DeepSeek 返回的响应（带有 <think> 标签）
    polluted_response = '''
<think>
让我思考一下如何修改这个函数...
需要添加错误处理
检查除零情况
</think>

好的，这是修改建议：

<file_edit path="main.py" type="modify" description="添加除零检查">
```python
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```
</file_edit>
'''

    print("原始响应（带污染）:")
    print("-" * 60)
    print(polluted_response[:200] + "...")
    print()

    # 测试自动清理
    print("测试自动清理（auto_clean=True）:")
    print("-" * 60)
    edits = CodeEditParser.parse(polluted_response, auto_clean=True)
    print(f"✓ 解析出 {len(edits)} 个编辑")
    if edits:
        print(f"  文件: {edits[0].file_path}")
        print(f"  类型: {edits[0].edit_type}")
        print(f"  描述: {edits[0].description}")
    print()

    # 测试手动清理
    print("手动清理污染:")
    print("-" * 60)
    cleaned = CodeEditParser.clean_pollution(polluted_response)
    print("清理后的文本:")
    print(cleaned[:300])
    print()

    # 验证 <think> 标签被移除
    assert '<think>' not in cleaned, "污染标签未被清除"
    assert '</think>' not in cleaned, "污染标签未被清除"
    print("✓ <think> 标签已清除")
    print()

    # 测试其他污染模式
    print("测试其他污染模式:")
    print("-" * 60)

    test_cases = [
        ('<thinking>内部思考</thinking>', 'thinking'),
        ('<reflection>反思内容</reflection>', 'reflection'),
        ('<内部思考>中文思考</内部思考>', '内部思考'),
    ]

    for polluted, tag_name in test_cases:
        test_text = f"{polluted}\n<file_edit path=\"test.py\">```\ncode\n```</file_edit>"
        cleaned = CodeEditParser.clean_pollution(test_text)
        if tag_name in cleaned:
            print(f"✗ {tag_name} 标签未被清除")
        else:
            print(f"✓ {tag_name} 标签已清除")

    print()
    print("=" * 60)
    print("POLLUTION CLEANING TESTS PASSED! ✓")
    print("=" * 60)


if __name__ == '__main__':
    test_pollution_cleaning()
