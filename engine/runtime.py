from typing import List, Dict, Any

from core.operation import Operation
from core.plan import Plan
from core.result import ExecutionResult
from .planner import Planner
from .executor import Executor


class OperationRuntime:
    """操作ランタイムのメインクラス"""

    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()
        self.execution_history: List[ExecutionResult] = []

    def plan(self, operation: Operation, data: List[Dict[str, Any]]) -> Plan:
        """操作の実行計画を生成"""
        return self.planner.plan(operation, data)

    def execute(
        self,
        operation: Operation,
        data: List[Dict[str, Any]],
        dry_run: bool = False,
    ) -> ExecutionResult:
        """操作を実行"""
        plan = self.plan(operation, data)
        result = self.executor.execute(plan, data, dry_run=dry_run)
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
