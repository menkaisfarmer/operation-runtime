import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.action import Update, Delete
from core.target import Where, AllRecords
from core.operation import SimpleOperation, Sequence
from engine.runtime import OperationRuntime
from engine.scheduler import ConflictType


def test_conflict_detection():
    """競合検出テスト"""
    data = [
        {"id": 1, "status": "active", "value": 100},
        {"id": 2, "status": "active", "value": 200},
    ]

    runtime = OperationRuntime()

    # 同じターゲットへの Write-Write 操作
    op1 = SimpleOperation(
        target=Where({"status": "active"}),
        actions=[Update({"value": 500})],
    )

    op2 = SimpleOperation(
        target=Where({"status": "active"}),
        actions=[Update({"value": 600})],
    )

    sequence = Sequence(op1, op2)
    plan = runtime.plan(sequence, data)

    print("\n=== Test: Conflict Detection ===")
    print(f"Plan: {plan}")
    print(f"Conflicts: {plan.conflicts}")

    # Write-Write 競合が検出されるはず
    write_write_conflicts = [
        c for c in plan.conflicts
        if c.conflict_type == ConflictType.WRITE_WRITE
    ]
    assert len(write_write_conflicts) > 0
    print("✓ Conflict detected correctly")


def test_validation_large_delete():
    """大規模削除の警告テスト"""
    data = [{"id": i, "type": "temp"} for i in range(150)]

    runtime = OperationRuntime()

    operation = SimpleOperation(
        target=Where({"type": "temp"}),
        actions=[Delete()],
    )

    errors = runtime.validate(operation, data)
    warnings = [e for e in errors if e.severity == "warning"]

    print("\n=== Test: Validation - Large Delete ===")
    print(f"Warnings: {warnings}")
    assert any("LARGE_DELETE" in w.code for w in warnings)
    print("✓ Large delete warning detected")


def test_validation_no_target_match():
    """対象なしの警告テスト"""
    data = [
        {"id": 1, "status": "active"},
        {"id": 2, "status": "active"},
    ]

    runtime = OperationRuntime()

    operation = SimpleOperation(
        target=Where({"status": "inactive"}),  # マッチしない条件
        actions=[Update({"status": "processing"})],
    )

    errors = runtime.validate(operation, data)
    warnings = [e for e in errors if e.severity == "warning"]

    print("\n=== Test: Validation - No Target Match ===")
    print(f"Warnings: {warnings}")
    assert any("NO_TARGET_MATCH" in w.code for w in warnings)
    print("✓ No target match warning detected")


def test_field_conflict_detection():
    """フィールド競合検出テスト"""
    data = [
        {"id": 1, "name": "A", "value": 100},
        {"id": 2, "name": "B", "value": 200},
    ]

    runtime = OperationRuntime()

    # 同じターゲットの同じフィールドを更新する操作
    op1 = SimpleOperation(
        target=Where({"id": 1}),
        actions=[Update({"value": 150})],
    )

    op2 = SimpleOperation(
        target=Where({"id": 1}),
        actions=[Update({"value": 200})],
    )

    sequence = Sequence(op1, op2)
    plan = runtime.plan(sequence, data)

    print("\n=== Test: Field Conflict Detection ===")
    print(f"Conflicts: {plan.conflicts}")

    # Write-Write 競合が検出される（同じターゲットへの書き込み）
    write_write_conflicts = [
        c for c in plan.conflicts
        if c.conflict_type == ConflictType.WRITE_WRITE
    ]
    assert len(write_write_conflicts) > 0
    print(f"✓ Conflict detected on same target: {write_write_conflicts}")


def test_execution_order_with_conflicts():
    """競合を考慮した実行順序テスト"""
    data = [{"id": 1, "value": 0}]

    runtime = OperationRuntime()

    # op2 が op1 に依存する順序で実行されるべき
    op1 = SimpleOperation(
        target=AllRecords(),
        actions=[Update({"value": 100})],
    )

    op2 = SimpleOperation(
        target=AllRecords(),
        actions=[Update({"value": 200})],
    )

    sequence = Sequence(op1, op2)
    plan = runtime.plan(sequence, data)

    print("\n=== Test: Execution Order with Conflicts ===")
    print(f"Execution order: {plan.execution_order}")

    # op1 が op2 の前に実行されるべき
    op1_idx = plan.execution_order.index(op1.op_id)
    op2_idx = plan.execution_order.index(op2.op_id)
    assert op1_idx < op2_idx
    print("✓ Execution order respects dependencies")


def test_parallel_operations_no_conflict():
    """競合なしの並列操作テスト"""
    data = [
        {"id": 1, "type": "A", "status": "pending", "timestamp": None},
        {"id": 2, "type": "B", "status": "pending", "timestamp": None},
    ]

    runtime = OperationRuntime()

    # 異なるターゲットへの操作は並列実行可能（異なるフィールド更新）
    op1 = SimpleOperation(
        target=Where({"type": "A"}),
        actions=[Update({"status": "processing"})],
    )

    op2 = SimpleOperation(
        target=Where({"type": "B"}),
        actions=[Update({"timestamp": "2026-08-16"})],
    )

    from core.operation import Parallel

    parallel = Parallel(op1, op2)
    plan = runtime.plan(parallel, data)

    print("\n=== Test: Parallel Operations - No Conflict ===")
    print(f"Conflicts: {plan.conflicts}")

    # 異なるターゲット・異なるフィールドなので競合がないはず
    assert len(plan.conflicts) == 0
    print("✓ No conflicts detected for parallel operations")


if __name__ == "__main__":
    test_conflict_detection()
    test_validation_large_delete()
    test_validation_no_target_match()
    test_field_conflict_detection()
    test_execution_order_with_conflicts()
    test_parallel_operations_no_conflict()
    print("\n✓ All Phase 2 tests passed!")
