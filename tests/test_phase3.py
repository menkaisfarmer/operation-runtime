import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.action import Update, Delete
from core.target import Where, AllRecords
from core.operation import SimpleOperation, Sequence
from engine.runtime import OperationRuntime
from engine.transaction import TransactionState


def test_transaction_commit():
    """トランザクションコミットテスト"""
    data = [
        {"id": 1, "status": "pending", "value": 100},
        {"id": 2, "status": "pending", "value": 200},
    ]

    runtime = OperationRuntime()

    operation = SimpleOperation(
        target=Where({"status": "pending"}),
        actions=[Update({"status": "completed"})],
    )

    result = runtime.execute(operation, data, use_transaction=True)

    print("\n=== Test: Transaction Commit ===")
    print(f"Result: {result}")
    print(f"Transaction state: {result.transaction_log.state.value}")
    print(f"Data after: {data}")

    assert result.transaction_log.state == TransactionState.COMMITTED
    assert result.total_success == 2
    assert data[0]["status"] == "completed"
    print("✓ Transaction committed successfully")


def test_transaction_with_compensating_actions():
    """補償操作テスト"""
    data = [
        {"id": 1, "status": "active", "value": 100},
        {"id": 2, "status": "active", "value": 200},
    ]

    runtime = OperationRuntime()

    operation = SimpleOperation(
        target=Where({"status": "active"}),
        actions=[Update({"value": 999})],
    )

    result = runtime.execute(operation, data, use_transaction=True)

    print("\n=== Test: Compensating Actions ===")
    print(f"Changes: {result.transaction_log.changes}")
    print(f"Compensating actions: {result.transaction_log.compensating_actions}")

    assert len(result.transaction_log.compensating_actions) == 2
    assert data[0]["value"] == 999
    print("✓ Compensating actions recorded")


def test_rollback_on_error():
    """エラー時のロールバック"""
    data = [
        {"id": 1, "status": "pending"},
        {"id": 2, "status": "pending"},
    ]

    runtime = OperationRuntime()

    # わざとエラーを発生させるカスタムアクション
    from core.action import Transform

    def failing_transform(record):
        if record["id"] == 2:
            raise ValueError("Intentional error on record 2")
        return {**record, "status": "completed"}

    operation = SimpleOperation(
        target=AllRecords(),
        actions=[Transform(failing_transform)],
    )

    result = runtime.execute(operation, data, use_transaction=True)

    print("\n=== Test: Rollback on Error ===")
    print(f"Result: {result}")
    print(f"Transaction state: {result.transaction_log.state.value}")
    print(f"Total failures: {result.total_failure}")

    # ロールバックされたはず
    assert result.transaction_log.state == TransactionState.ABORTED
    assert result.total_failure > 0
    print("✓ Rollback executed on error")


def test_undo_operation():
    """Undo 操作テスト"""
    data = [
        {"id": 1, "name": "A", "count": 10},
        {"id": 2, "name": "B", "count": 20},
    ]

    runtime = OperationRuntime()

    operation = SimpleOperation(
        target=AllRecords(),
        actions=[Update({"count": 999})],
    )

    result = runtime.execute(operation, data, use_transaction=True)

    print("\n=== Test: Undo Operation ===")
    print(f"Data before undo: {data}")
    print(f"Transaction log state: {result.transaction_log.state.value}")
    print(f"Compensating actions: {len(result.transaction_log.compensating_actions)}")

    # Undo を実行
    undo_success = runtime.undo(result, data)

    print(f"Undo success: {undo_success}")
    print(f"Transaction log state after undo: {result.transaction_log.state.value}")
    print(f"Data after undo: {data}")

    # ロールバック後、データが元に戻るはず
    assert undo_success
    assert data[0]["count"] == 10
    assert data[1]["count"] == 20
    print("✓ Undo executed successfully")


def test_savepoint():
    """セーブポイント機能テスト"""
    data = [
        {"id": 1, "value": 100},
        {"id": 2, "value": 200},
    ]

    from engine.transaction import Transaction

    transaction = Transaction("tx-001", "op-001")
    transaction.begin()

    # セーブポイントを作成
    transaction.log.create_savepoint("sp1", data)

    # データを変更
    data[0]["value"] = 500

    print("\n=== Test: Savepoint ===")
    print(f"Data before rollback: {data}")

    # セーブポイントまでロールバック
    rollback_success = transaction.log.rollback_to_savepoint("sp1", data)

    print(f"Rollback success: {rollback_success}")
    print(f"Data after rollback: {data}")

    assert rollback_success
    assert data[0]["value"] == 100
    print("✓ Savepoint rollback successful")


def test_transaction_log_summary():
    """トランザクションログの概要取得"""
    data = [
        {"id": 1, "status": "pending"},
    ]

    runtime = OperationRuntime()

    operation = SimpleOperation(
        target=AllRecords(),
        actions=[Update({"status": "completed"})],
    )

    result = runtime.execute(operation, data, use_transaction=True)

    print("\n=== Test: Transaction Log Summary ===")
    summary = result.transaction_log.get_summary()
    print(f"Summary: {summary}")

    assert summary["state"] == "committed"
    assert summary["changes_count"] == 1
    assert summary["committed_at"] is not None
    print("✓ Transaction log summary retrieved")


def test_dry_run_no_transaction():
    """Dry Run ではトランザクション不要"""
    data = [
        {"id": 1, "status": "pending"},
    ]

    runtime = OperationRuntime()

    operation = SimpleOperation(
        target=AllRecords(),
        actions=[Update({"status": "completed"})],
    )

    result = runtime.execute(operation, data, dry_run=True)

    print("\n=== Test: Dry Run No Transaction ===")
    print(f"Transaction log: {result.transaction_log}")
    print(f"Data unchanged: {data}")

    # Dry Run はトランザクション使用しない
    assert result.transaction_log is None
    assert data[0]["status"] == "pending"
    print("✓ Dry run executed without transaction")


if __name__ == "__main__":
    test_transaction_commit()
    test_transaction_with_compensating_actions()
    test_rollback_on_error()
    test_undo_operation()
    test_savepoint()
    test_transaction_log_summary()
    test_dry_run_no_transaction()
    print("\n✓ All Phase 3 tests passed!")
