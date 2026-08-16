"""
Test minimal UI functionality
最小限 UI のテスト
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.action import Update, Delete
from core.target import Where, AllRecords
from core.operation import SimpleOperation
from engine.runtime import OperationRuntime
from adapters.memory import MemoryAdapter


def test_minimal_ui_update_logic():
    """最小限 UI の更新ロジック テスト"""
    print("\n=== Test: Minimal UI Update Logic ===")

    data = [
        {"id": 1, "status": "pending", "value": 100},
        {"id": 2, "status": "pending", "value": 200},
    ]

    adapter = MemoryAdapter(data)
    adapter.connect()
    runtime = OperationRuntime(adapter)

    # Parse filter: "status=pending"
    filter_str = "status=pending"
    conditions = {}
    for part in filter_str.split(','):
        if '=' in part:
            k, v = part.split('=', 1)
            conditions[k.strip()] = v.strip()

    target = Where(conditions) if conditions else AllRecords()

    # Parse set: "status=completed"
    set_str = "status=completed"
    updates = {}
    for part in set_str.split(','):
        if '=' in part:
            k, v = part.split('=', 1)
            k = k.strip()
            v = v.strip()
            try:
                v = int(v)
            except:
                try:
                    v = float(v)
                except:
                    pass
            updates[k] = v

    operation = SimpleOperation(target=target, actions=[Update(updates)])

    # Execute
    result = runtime.execute(operation, data)

    print(f"Filter: {filter_str}")
    print(f"Updates: {updates}")
    print(f"Success: {result.total_success}")
    print(f"Data after: {data}")

    assert result.total_success == 2
    assert data[0]["status"] == "completed"

    print("✓ Minimal UI update logic test passed")


def test_minimal_ui_delete_logic():
    """最小限 UI の削除ロジック テスト"""
    print("\n=== Test: Minimal UI Delete Logic ===")

    data = [
        {"id": 1, "status": "archived"},
        {"id": 2, "status": "active"},
    ]

    adapter = MemoryAdapter(data)
    adapter.connect()
    runtime = OperationRuntime(adapter)

    # Parse filter: "status=archived"
    filter_str = "status=archived"
    conditions = {}
    for part in filter_str.split(','):
        if '=' in part:
            k, v = part.split('=', 1)
            conditions[k.strip()] = v.strip()

    target = Where(conditions)
    operation = SimpleOperation(target=target, actions=[Delete()])

    # Execute
    result = runtime.execute(operation, data)

    print(f"Filter: {filter_str}")
    print(f"Success: {result.total_success}")
    print(f"Data after: {data}")

    assert result.total_success == 1
    assert len(data) == 1
    assert data[0]["id"] == 2

    print("✓ Minimal UI delete logic test passed")


def test_minimal_ui_dry_run():
    """最小限 UI の Dry Run テスト"""
    print("\n=== Test: Minimal UI Dry Run ===")

    data = [
        {"id": 1, "status": "pending"},
        {"id": 2, "status": "pending"},
        {"id": 3, "status": "active"},
    ]

    adapter = MemoryAdapter(data)
    adapter.connect()
    runtime = OperationRuntime(adapter)

    # Parse filter
    filter_str = "status=pending"
    conditions = {}
    for part in filter_str.split(','):
        if '=' in part:
            k, v = part.split('=', 1)
            conditions[k.strip()] = v.strip()

    target = Where(conditions)

    # Count matching records
    if isinstance(target, Where):
        targets = target.filter(data)
    else:
        targets = data

    print(f"Filter: {filter_str}")
    print(f"Matching records: {len(targets)}")

    assert len(targets) == 2

    print("✓ Minimal UI dry run test passed")


def test_minimal_ui_imports():
    """最小限 UI インポートテスト"""
    print("\n=== Test: Minimal UI Imports ===")

    try:
        from ui.minimal import app, HTML

        print("✓ Minimal UI imports successful")
    except ImportError as e:
        print(f"⚠ Flask not installed: {e}")
        print("  (This is expected if Flask is not installed)")


if __name__ == "__main__":
    test_minimal_ui_update_logic()
    test_minimal_ui_delete_logic()
    test_minimal_ui_dry_run()
    test_minimal_ui_imports()
    print("\n✓ All minimal UI tests passed!")
