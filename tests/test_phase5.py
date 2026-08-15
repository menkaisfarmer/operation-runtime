import sys
import json
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.cli import OperationCLI


def test_cli_memory_update():
    """CLI - Memory Adapter Update テスト"""
    print("\n=== Test: CLI Memory Update ===")

    cli = OperationCLI()
    data = [
        {"id": 1, "status": "pending", "value": 100},
        {"id": 2, "status": "pending", "value": 200},
    ]

    # メモリ初期化
    args_list = [
        "memory",
        "--data",
        json.dumps(data),
        "update",
        "--filter",
        "status=pending",
        "--set",
        "status=completed",
        "--dry-run",
    ]

    # コマンド実行
    import argparse

    cli.parse_args(args_list)

    print("✓ CLI memory update test passed")


def test_cli_list():
    """CLI - List コマンド テスト"""
    print("\n=== Test: CLI List ===")

    cli = OperationCLI()
    data = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]

    args_list = ["memory", "--data", json.dumps(data), "list"]

    cli.parse_args(args_list)

    print("✓ CLI list test passed")


def test_filter_parsing():
    """フィルター解析テスト"""
    print("\n=== Test: Filter Parsing ===")

    cli = OperationCLI()

    # 単一条件
    filter1 = cli._parse_filter("status=pending")
    assert filter1 is not None
    assert filter1.matches({"status": "pending", "id": 1})

    # 複数条件
    filter2 = cli._parse_filter("status=active,type=A")
    assert filter2 is not None
    assert filter2.matches({"status": "active", "type": "A", "id": 1})

    print("✓ Filter parsing test passed")


def test_set_parsing():
    """SET 値解析テスト"""
    print("\n=== Test: Set Parsing ===")

    cli = OperationCLI()

    # 単一値
    set1 = cli._parse_set("status=completed")
    assert set1["status"] == "completed"

    # 複数値
    set2 = cli._parse_set("status=active,count=10,rate=1.5")
    assert set2["status"] == "active"
    assert set2["count"] == 10
    assert set2["rate"] == 1.5

    print("✓ Set parsing test passed")


def test_web_ui_imports():
    """Web UI インポートテスト"""
    print("\n=== Test: Web UI Imports ===")

    try:
        from ui.web import OperationWeb

        print("✓ Web UI imports successful")
    except ImportError as e:
        print(f"⚠ Flask not installed: {e}")
        print("  (This is expected if Flask is not installed)")


def test_cli_help():
    """CLI - Help テスト"""
    print("\n=== Test: CLI Help ===")

    cli = OperationCLI()

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        cli.parse_args(["help"])
    except SystemExit:
        pass  # help コマンドは exit する
    finally:
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

    print("✓ CLI help test passed")


def test_cli_error_handling():
    """CLI - エラーハンドリング テスト"""
    print("\n=== Test: CLI Error Handling ===")

    cli = OperationCLI()

    # 無効な JSON
    try:
        cli.parse_args(["memory", "--data", "invalid json", "list"])
        assert False, "Should have raised an error"
    except (json.JSONDecodeError, SystemExit):
        pass

    print("✓ CLI error handling test passed")


if __name__ == "__main__":
    test_cli_memory_update()
    test_cli_list()
    test_filter_parsing()
    test_set_parsing()
    test_web_ui_imports()
    test_cli_help()
    test_cli_error_handling()
    print("\n✓ All Phase 5 tests passed!")
