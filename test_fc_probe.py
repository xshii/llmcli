#!/usr/bin/env python3
"""
测试 FC 检测功能（仅测试 Schema）
"""
import sys
sys.path.insert(0, '.')

from aicode.models.schema import ModelSchema


def test_fc_probe():
    """测试 FC 探测功能（跳过，需要真实 API）"""
    print("\n" + "=" * 60)
    print("测试 FC 探测功能")
    print("=" * 60)

    print("\n⊗ 跳过 - 需要真实 API key 和 tiktoken 模块")
    print("  运行 'pip install tiktoken' 然后使用 'aicode probe <model>' 命令")
    print()


def test_schema_fields():
    """测试 Schema 新字段"""
    print("\n" + "=" * 60)
    print("测试 Schema 新字段")
    print("=" * 60)

    # 创建模型并设置 FC 能力
    model = ModelSchema(
        name="gpt-4",
        provider="openai",
        supports_function_calling=True,
        supports_xml_format=False,
        supports_json_mode=True
    )

    print(f"\n模型: {model.name}")
    print(f"  Function Calling: {model.supports_function_calling}")
    print(f"  XML Format: {model.supports_xml_format}")
    print(f"  JSON Mode: {model.supports_json_mode}")

    # 转换为字典
    data = model.to_dict()
    print(f"\n字典格式:")
    for key in ['supports_function_calling', 'supports_xml_format', 'supports_json_mode']:
        print(f"  {key}: {data.get(key)}")

    # 从字典恢复
    restored = ModelSchema.from_dict(data)
    print(f"\n从字典恢复:")
    print(f"  Function Calling: {restored.supports_function_calling}")
    print(f"  XML Format: {restored.supports_xml_format}")
    print(f"  JSON Mode: {restored.supports_json_mode}")

    print("\n✓ Schema 测试通过")
    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("FC 检测功能测试套件")
    print("=" * 60)

    try:
        test_schema_fields()
        test_fc_probe()

        print("=" * 60)
        print("测试完成")
        print("=" * 60)
        print()

        print("注意:")
        print("- FC 探测需要真实的 API key 才能完全测试")
        print("- 当前 LLMClient 还不支持 tools 和 response_format 参数")
        print("- 建议先运行数据库迁移: python migrate_db_fc_fields.py")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
