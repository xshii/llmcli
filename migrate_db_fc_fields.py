#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加 FC 能力字段

为现有数据库添加：
- supports_function_calling
- supports_xml_format
- supports_json_mode
"""
import sqlite3
import os
import sys


def migrate_database(db_path: str):
    """
    迁移数据库，添加新字段

    Args:
        db_path: 数据库文件路径
    """
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False

    print(f"开始迁移数据库: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(models)")
        columns = [row[1] for row in cursor.fetchall()]

        fields_to_add = []

        if 'supports_function_calling' not in columns:
            fields_to_add.append(('supports_function_calling', 'INTEGER DEFAULT 0'))

        if 'supports_xml_format' not in columns:
            fields_to_add.append(('supports_xml_format', 'INTEGER DEFAULT 0'))

        if 'supports_json_mode' not in columns:
            fields_to_add.append(('supports_json_mode', 'INTEGER DEFAULT 0'))

        if not fields_to_add:
            print("✓ 所有字段已存在，无需迁移")
            return True

        # 添加字段
        for field_name, field_def in fields_to_add:
            print(f"  添加字段: {field_name}")
            cursor.execute(f"ALTER TABLE models ADD COLUMN {field_name} {field_def}")

        conn.commit()
        print("✓ 数据库迁移成功")

        # 显示字段列表
        cursor.execute("PRAGMA table_info(models)")
        columns = cursor.fetchall()

        print("\n当前数据库字段:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"✗ 数据库迁移失败: {e}")
        return False


def main():
    """主函数"""
    # 默认数据库路径
    default_db_path = os.path.expanduser("~/.aicode/data/aicode.db")

    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = default_db_path

    print("=" * 60)
    print("数据库迁移工具 - 添加 FC 能力字段")
    print("=" * 60)
    print()

    success = migrate_database(db_path)

    print()
    print("=" * 60)

    if success:
        print("迁移完成！")
        print()
        print("现在可以运行 'aicode probe <model_name>' 来检测模型 FC 能力")
    else:
        print("迁移失败，请检查错误信息")
        sys.exit(1)


if __name__ == '__main__':
    main()
