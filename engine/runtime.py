from typing import List, Dict, Any

from core.operation import Operation
from core.plan import Plan
from core.result import ExecutionResult
from .planner import Planner
from .executor import Executor
from .validator import Validator, ValidationError


class OperationRuntime:
    """操作ランタイムのメインクラス"""

    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()
        self.validator = Validator()
        self.execution_history: List[ExecutionResult] = []

    def plan(self, operation: Operation, data: List[Dict[str, Any]]) -> Plan:
        """操作の実行計画を生成"""
        return self.planner.plan(operation, data)

    def execute(
        self,
        operation: Operation,
        data: List[Dict[str, Any]],
        dry_run: bool = False,
        validate: bool = True,
        use_transaction: bool = True,
    ) -> ExecutionResult:
        """操作を実行"""
        plan = self.plan(operation, data)

        if validate:
            errors = self.validator.get_errors(plan, data)
            if errors:
                raise ValueError(
                    f"Validation failed: {', '.join(str(e) for e in errors)}"
                )

        result = self.executor.execute(
            plan, data, dry_run=dry_run, use_transaction=use_transaction
        )
        self.execution_history.append(result)
        return result

    def dry_run(self, operation: Operation, data: List[Dict[str, Any]]) -> Plan:
        """Dry Run: 実行せずに計画を表示"""
        return self.plan(operation, data)

    def undo(self, result: ExecutionResult, data: List[Dict[str, Any]]) -> None:
        """最後の実行をロールバック"""
        # Undo ログをリバースで適用
        for log in reversed(result.undo_log):
            before = log.get("before")
            if before:
                # 実装: before の状態に復元
                pass

    def get_history(self) -> List[ExecutionResult]:
        """実行履歴を取得"""
        return self.execution_history

    def validate(
        self, operation: Operation, data: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """計画を検証"""
        plan = self.plan(operation, data)
        return self.validator.validate(plan, data)

    def undo(self, result: ExecutionResult, data: List[Dict[str, Any]]) -> bool:
        """実行結果をロールバック"""
        if not result.transaction_log:
            return False

        return result.transaction_log.rollback(data) if hasattr(
            result.transaction_log, "rollback"
        ) else False
