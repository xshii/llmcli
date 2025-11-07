"""
probe 命令 - 探测模型格式支持并更新数据库
"""
import argparse
from aicode.database.db_manager import DatabaseManager
from aicode.config.config_manager import ConfigManager
from aicode.utils.paths import get_db_path
from aicode.llm.model_probe import probe_model_full
from aicode.cli.utils.output import Output
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


def setup_parser(subparsers) -> argparse.ArgumentParser:
    """
    设置 probe 命令的参数解析器

    Args:
        subparsers: 子命令解析器

    Returns:
        ArgumentParser: probe 命令的解析器
    """
    parser = subparsers.add_parser(
        'probe',
        help='Probe model format support',
        description='Test model format support and update database'
    )

    parser.add_argument(
        'model',
        type=str,
        help='Model name to probe'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='API key (overrides config)'
    )

    parser.add_argument(
        '--api-url',
        type=str,
        help='API URL (overrides config)'
    )

    parser.add_argument(
        '--no-update',
        action='store_true',
        help='Do not update database (dry run)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )

    parser.set_defaults(func=execute)
    return parser


def execute(args: argparse.Namespace) -> int:
    """
    执行 probe 命令

    Args:
        args: 命令行参数

    Returns:
        int: 退出码
    """
    try:
        # 加载配置
        config_manager = ConfigManager()
        if not config_manager.config_exists():
            Output.print_error("Config not found. Run 'aicode config init' first.")
            return 1

        config_manager.load()

        # 加载模型
        db_path = get_db_path(config_manager)
        db_manager = DatabaseManager(db_path)
        model = db_manager.get_model(args.model)

        # 获取 API 配置
        api_key = args.api_key or config_manager.get('global.api_key') or model.api_key
        api_url = args.api_url or config_manager.get('global.api_url') or model.api_url

        if not api_key:
            Output.print_error("API key not configured")
            return 1

        # 显示探测信息
        Output.print_header(f"Probing Model: {model.name}")
        print(f"Provider: {model.provider}")
        print(f"Current vscode_friendly: {model.vscode_friendly}")
        print(f"API URL: {api_url or 'default'}")
        print()

        # 执行完整探测
        Output.print_info("Testing model capabilities...")
        result = probe_model_full(model, api_key, api_url)

        # 显示结果
        Output.print_separator()
        Output.print_bold("Probe Results")
        Output.print_separator()

        if not result['success']:
            Output.print_error(f"Probe failed: {result.get('error', 'Unknown error')}")
            return 1

        # Function Calling 支持
        if result.get('supports_function_calling'):
            Output.print_success("✓ Function Calling: YES")
        else:
            print("✗ Function Calling: NO")

        # XML 格式支持
        if result.get('supports_xml_format'):
            Output.print_success(f"✓ XML Format: YES (edits: {result.get('edits_count', 0)})")

            # 污染检测
            if result.get('has_pollution'):
                Output.print_warning(f"  └─ Pollution: {', '.join(result.get('pollution_types', []))} (auto-cleaning enabled)")
        else:
            print("✗ XML Format: NO")

        # JSON Mode 支持
        if result.get('supports_json_mode'):
            Output.print_success("✓ JSON Mode: YES")
        else:
            print("✗ JSON Mode: NO")

        print()

        # VSCode 友好度
        if result.get('vscode_friendly'):
            Output.print_success("Overall: VSCode Friendly ✓")
        else:
            Output.print_warning("Overall: May not be VSCode friendly")

        # 详细输出
        if args.verbose:
            Output.print_separator()
            Output.print_bold("Raw Response (first 500 chars)")
            Output.print_separator()
            raw = result['raw_response']
            print(raw[:500] + ('...' if len(raw) > 500 else ''))

        # 建议
        Output.print_separator()
        Output.print_bold("Recommendations")
        Output.print_separator()

        if result.get('supports_function_calling'):
            Output.print_success("Recommended: Use UnifiedAgent with Function Calling mode")
            print("This model has native FC support, providing the best experience")
        elif result.get('supports_xml_format'):
            Output.print_info("Recommended: Use UnifiedAgent with Prompt Engineering mode")
            print("This model supports XML format for code editing")
            if result.get('has_pollution'):
                print("Note: Auto-cleaning is enabled for pollution tags")
        else:
            Output.print_warning("This model may not be suitable for code editing")
            print("Consider using a different model or adjusting prompts")

        # 更新数据库
        if not args.no_update:
            Output.print_separator()
            Output.print_bold("Updating Database")
            Output.print_separator()

            try:
                updates = {
                    'vscode_friendly': result.get('vscode_friendly', False),
                    'supports_function_calling': result.get('supports_function_calling', False),
                    'supports_xml_format': result.get('supports_xml_format', False),
                    'supports_json_mode': result.get('supports_json_mode', False)
                }

                db_manager.update_model(model.name, updates)
                Output.print_success(f"Updated {model.name}:")
                print(f"  vscode_friendly: {model.vscode_friendly} → {updates['vscode_friendly']}")
                print(f"  supports_function_calling: → {updates['supports_function_calling']}")
                print(f"  supports_xml_format: → {updates['supports_xml_format']}")
                print(f"  supports_json_mode: → {updates['supports_json_mode']}")
            except Exception as e:
                Output.print_error(f"Failed to update database: {e}")
                logger.exception("Error updating database")
                return 1
        else:
            Output.print_separator()
            Output.print_info("Skipping database update (--no-update flag)")
            print(f"  Would update:")
            print(f"    vscode_friendly = {result.get('vscode_friendly', False)}")
            print(f"    supports_function_calling = {result.get('supports_function_calling', False)}")
            print(f"    supports_xml_format = {result.get('supports_xml_format', False)}")
            print(f"    supports_json_mode = {result.get('supports_json_mode', False)}")

        print()
        return 0

    except Exception as e:
        Output.print_error(f"Probe failed: {e}")
        logger.exception("Error in probe command")
        return 1
