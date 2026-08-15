import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.action import Update, Delete
from core.target import Where, AllRecords
from core.operation import SimpleOperation
from engine.runtime import OperationRuntime
from adapters.memory import MemoryAdapter
from adapters.sqlite import SQLiteAdapter


def test_memory_adapter():
    """Memory Adapter テスト"""
    data = [
        {"id": 1, "name": "Alice", "status": "pending"},
        {"id": 2, "name": "Bob", "status": "pending"},
    ]

    adapter = MemoryAdapter(data)
    adapter.connect()

    print("\n=== Test: Memory Adapter ===")
    print(f"Connected: {adapter.is_connected()}")

    # データを読み取る
    records = adapter.read()
    print(f"Read records: {len(records)}")
    assert len(records) == 2
    assert records[0]["name"] == "Alice"

    # Operation を実行
    runtime = OperationRuntime(adapter)
    operation = SimpleOperation(
        target=Where({"status": "pending"}),
        actions=[Update({"status": "completed"})],
    )

    result = runtime.execute_with_adapter(operation)

    # 結果を確認
    print(f"Result: {result}")
    assert result.total_success == 2

    # Adapter のデータを確認
    updated_records = adapter.read()
    assert updated_records[0]["status"] == "completed"

    adapter.disconnect()
    print("✓ Memory Adapter test passed")


def test_sqlite_adapter():
    """SQLite Adapter テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")

        # Adapter を作成
        adapter = SQLiteAdapter(db_path, "users")
        adapter.connect()

        # テーブルを作成
        schema = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "status": "TEXT",
        }
        adapter.create_table(schema)

        # テストデータを挿入
        test_data = [
            {"id": 1, "name": "Charlie", "status": "pending"},
            {"id": 2, "name": "Diana", "status": "pending"},
        ]
        adapter.write(test_data)

        print("\n=== Test: SQLite Adapter ===")
        print(f"Database path: {db_path}")
        print(f"Connected: {adapter.is_connected()}")

        # データを読み取る
        records = adapter.read()
        print(f"Read records: {len(records)}")
        assert len(records) == 2

        # Operation を実行
        runtime = OperationRuntime(adapter)
        operation = SimpleOperation(
            target=AllRecords(),
            actions=[Update({"status": "completed"})],
        )

        result = runtime.execute_with_adapter(operation)

        # 結果を確認
        print(f"Result: {result}")
        assert result.total_success == 2

        # Adapter のデータを確認
        updated_records = adapter.read()
        assert all(r["status"] == "completed" for r in updated_records)

        adapter.disconnect()
        print("✓ SQLite Adapter test passed")


def test_adapter_transaction():
    """Adapter トランザクション テスト"""
    data = [
        {"id": 1, "value": 100},
        {"id": 2, "value": 200},
    ]

    adapter = MemoryAdapter(data)
    adapter.connect()

    print("\n=== Test: Adapter Transaction ===")

    # トランザクション開始
    tx_id = adapter.begin_transaction()
    print(f"Transaction ID: {tx_id}")

    # データを変更
    data[0]["value"] = 999

    # ロールバック
    rollback_success = adapter.rollback_transaction(tx_id)
    print(f"Rollback success: {rollback_success}")

    # データが復元されたか確認
    current_data = adapter.read()
    assert current_data[0]["value"] == 100

    adapter.disconnect()
    print("✓ Adapter Transaction test passed")


def test_adapter_with_filter():
    """フィルター付き読み取りテスト"""
    data = [
        {"id": 1, "type": "A", "value": 100},
        {"id": 2, "type": "B", "value": 200},
        {"id": 3, "type": "A", "value": 300},
    ]

    adapter = MemoryAdapter(data)
    adapter.connect()

    print("\n=== Test: Adapter with Filter ===")

    # フィルター付きで読み取る
    target = Where({"type": "A"})
    records = adapter.read(target)

    print(f"Filtered records: {len(records)}")
    assert len(records) == 2
    assert all(r["type"] == "A" for r in records)

    adapter.disconnect()
    print("✓ Adapter filter test passed")


def test_adapter_multiple_operations():
    """複数操作テスト"""
    data = [
        {"id": 1, "status": "pending"},
        {"id": 2, "status": "pending"},
        {"id": 3, "status": "active"},
    ]

    adapter = MemoryAdapter(data)
    adapter.connect()

    runtime = OperationRuntime(adapter)

    print("\n=== Test: Adapter Multiple Operations ===")

    # 最初の操作
    op1 = SimpleOperation(
        target=Where({"status": "pending"}),
        actions=[Update({"status": "active"})],
    )

    result1 = runtime.execute_with_adapter(op1)
    print(f"Operation 1 result: {result1.total_success} success")
    assert result1.total_success == 2

    # 2 番目の操作
    op2 = SimpleOperation(
        target=AllRecords(),
        actions=[Update({"status": "completed"})],
    )

    result2 = runtime.execute_with_adapter(op2)
    print(f"Operation 2 result: {result2.total_success} success")
    assert result2.total_success == 3

    # 最終確認
    final_records = adapter.read()
    assert all(r["status"] == "completed" for r in final_records)

    adapter.disconnect()
    print("✓ Multiple operations test passed")


if __name__ == "__main__":
    test_memory_adapter()
    test_sqlite_adapter()
    test_adapter_transaction()
    test_adapter_with_filter()
    test_adapter_multiple_operations()
    print("\n✓ All Phase 4 tests passed!")
