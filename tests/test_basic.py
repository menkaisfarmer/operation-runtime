import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.action import Update, Create, Delete
from core.target import Where, AllRecords
from core.operation import SimpleOperation, Sequence, Parallel
from engine.runtime import OperationRuntime


def test_simple_update():
    """単純な更新操作"""
    data = [
        {"name": "A", "value": 100},
        {"name": "B", "value": 200},
        {"name": "C", "value": 300},
    ]

    runtime = OperationRuntime()

    # value >= 200 のレコードを value + 50 で更新
    operation = SimpleOperation(
        target=Where({"value": {"gte": 200}}),
        actions=[Update({"value": 250})],
    )

    result = runtime.execute(operation, data)

    print("\n=== Test: Simple Update ===")
    print(f"Operation: {operation}")
    print(f"Result: {result}")
    print(f"Data after: {data}")
    assert result.total_success == 2  # B, C が更新される
    assert result.total_failure == 0
    print("✓ Test passed")


def test_sequence_operations():
    """順序付き複数操作"""
    data = [
        {"name": "A", "status": "未訪問", "days": 0},
        {"name": "B", "status": "未訪問", "days": 0},
        {"name": "C", "status": "訪問済", "days": 30},
    ]

    runtime = OperationRuntime()

    # Step 1: status = "未訪問" を "訪問予定" に
    op1 = SimpleOperation(
        target=Where({"status": "未訪問"}),
        actions=[Update({"status": "訪問予定"})],
    )

    # Step 2: すべてのレコードを days + 30 で更新
    op2 = SimpleOperation(
        target=AllRecords(),
        actions=[Update({"days": 30})],
    )

    sequence = Sequence(op1, op2)
    result = runtime.execute(sequence, data)

    print("\n=== Test: Sequence Operations ===")
    print(f"Result: {result}")
    print(f"Data after: {data}")
    assert result.total_success == 5  # 2 (step1) + 3 (step2)
    assert result.total_failure == 0
    assert data[0]["status"] == "訪問予定"
    assert data[0]["days"] == 30
    print("✓ Test passed")


def test_dry_run():
    """Dry Run モード"""
    data = [
        {"id": 1, "value": 100},
        {"id": 2, "value": 200},
        {"id": 3, "value": 300},
    ]

    runtime = OperationRuntime()

    operation = SimpleOperation(
        target=Where({"value": {"gte": 200}}),
        actions=[Update({"value": 999})],
    )

    plan = runtime.dry_run(operation, data)

    print("\n=== Test: Dry Run ===")
    print(f"Plan: {plan}")
    print(f"Summary: {plan.get_summary()}")
    assert plan.get_total_target_count() == 2  # id=2, id=3
    assert all(node.status.value == "pending" for node in plan.nodes.values())
    print(f"Data unchanged: {data}")
    assert data[1]["value"] == 200  # データは変更されない
    print("✓ Test passed")


def test_parallel_operations():
    """並列操作"""
    data = [
        {"id": 1, "type": "A", "status": "active"},
        {"id": 2, "type": "B", "status": "active"},
        {"id": 3, "type": "A", "status": "inactive"},
    ]

    runtime = OperationRuntime()

    # type = "A" を update
    op1 = SimpleOperation(
        target=Where({"type": "A"}),
        actions=[Update({"status": "processed"})],
    )

    # type = "B" を update
    op2 = SimpleOperation(
        target=Where({"type": "B"}),
        actions=[Update({"status": "processed"})],
    )

    parallel = Parallel(op1, op2)
    result = runtime.execute(parallel, data)

    print("\n=== Test: Parallel Operations ===")
    print(f"Result: {result}")
    print(f"Data after: {data}")
    assert result.total_success == 3  # すべてのレコードが処理される
    print("✓ Test passed")


if __name__ == "__main__":
    test_simple_update()
    test_sequence_operations()
    test_dry_run()
    test_parallel_operations()
    print("\n✓ All tests passed!")
