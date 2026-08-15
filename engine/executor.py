from typing import List, Dict, Any, Optional
from core.plan import Plan, ExecutionStatus
from core.result import Result, ExecutionResult
from core.action import Delete


class Executor:
    """Plan を実行する"""

    def execute(
        self, plan: Plan, data: List[Dict[str, Any]], dry_run: bool = False
    ) -> ExecutionResult:
        """計画を実行"""
        result = ExecutionResult(plan.operation.op_id)
        completed_ops = set()

        for node_id in plan.execution_order:
            node = plan.nodes[node_id]

            if not node.is_ready(completed_ops):
                node.status = ExecutionStatus.SKIPPED
                continue

            node.status = ExecutionStatus.RUNNING

            try:
                node_result = self._execute_node(node, data, dry_run)
                result.add_result(node_result)
                node.status = ExecutionStatus.COMPLETED

                # Undo用ログを記録
                if not dry_run:
                    for change in node_result.changes:
                        result.add_undo_log(
                            {
                                "operation_id": node_id,
                                "before": change.get("before"),
                                "after": change.get("after"),
                            }
                        )

                completed_ops.add(node_id)
            except Exception as e:
                node.status = ExecutionStatus.FAILED
                node_result = Result(node_id)
                node_result.add_failure(str(e))
                result.add_result(node_result)

        return result

    def _execute_node(
        self, node, data: List[Dict[str, Any]], dry_run: bool = False
    ) -> Result:
        """単一ノードを実行"""
        result = Result(node.operation_id)

        # ターゲットに該当するレコードを取得
        if node.target:
            target_records = node.target.filter(data)
        else:
            target_records = data

        # アクションを順序付けで適用
        for record in target_records:
            try:
                before = record.copy()

                # 削除操作以外のアクションを適用
                for action in node.actions:
                    if isinstance(action, Delete):
                        record = None
                        break
                    record = action.apply(record)

                # Dry Run の場合は変更を記録するだけ
                if dry_run:
                    result.add_success(
                        {
                            "before": before,
                            "after": record,
                            "dry_run": True,
                        }
                    )
                else:
                    # 実際のデータに変更を反映
                    if record is not None:
                        data_index = data.index(before)
                        data[data_index] = record
                    else:
                        data.remove(before)

                    result.add_success(
                        {
                            "before": before,
                            "after": record,
                        }
                    )

            except Exception as e:
                result.add_failure(f"Error processing record {before}: {str(e)}")

        node.changes = result.changes
        node.errors = result.errors

        return result
