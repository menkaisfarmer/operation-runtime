from typing import List, Dict, Any, Optional
from uuid import uuid4
from core.plan import Plan, ExecutionStatus
from core.result import Result, ExecutionResult
from core.action import Delete, Update
from .transaction import Transaction, CompensatingAction


class Executor:
    """Plan を実行する"""

    def execute(
        self,
        plan: Plan,
        data: List[Dict[str, Any]],
        dry_run: bool = False,
        use_transaction: bool = True,
    ) -> ExecutionResult:
        """計画を実行"""
        result = ExecutionResult(plan.operation.op_id)
        transaction = None

        if use_transaction and not dry_run:
            transaction = Transaction(str(uuid4()), plan.operation.op_id)
            transaction.begin()

        completed_ops = set()
        should_rollback = False

        try:
            for node_id in plan.execution_order:
                node = plan.nodes[node_id]

                if not node.is_ready(completed_ops):
                    node.status = ExecutionStatus.SKIPPED
                    continue

                node.status = ExecutionStatus.RUNNING

                try:
                    node_result = self._execute_node(
                        node, data, dry_run, transaction
                    )
                    result.add_result(node_result)
                    node.status = ExecutionStatus.COMPLETED

                    # ノード内でエラーがあればロールバック対象に
                    if node_result.failure_count > 0:
                        should_rollback = True
                        if transaction:
                            for error in node_result.errors:
                                transaction.add_error(error)

                    # Undo用ログを記録
                    if not dry_run and transaction:
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
                    should_rollback = True
                    node.status = ExecutionStatus.FAILED
                    node_result = Result(node_id)
                    node_result.add_failure(str(e))
                    result.add_result(node_result)

                    if transaction:
                        transaction.add_error(str(e))

            # トランザクション終了処理
            if transaction:
                if should_rollback:
                    if not transaction.rollback(data):
                        transaction.abort()
                else:
                    transaction.commit()
                result.transaction_log = transaction.get_log()

        except Exception as e:
            if transaction:
                transaction.abort()

        return result

    def _execute_node(
        self,
        node,
        data: List[Dict[str, Any]],
        dry_run: bool = False,
        transaction: Optional[Transaction] = None,
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

                    # トランザクションログに記録
                    if transaction:
                        result_change = {
                            "before": before,
                            "after": record,
                        }
                        transaction.add_change(result_change)

                        # 補償操作を追加（ロールバック時に実行）
                        if record is None:
                            # Delete の場合は復元操作
                            restored_record = before.copy()

                            def restore_record(ctx, rec=restored_record):
                                ctx["data"].append(rec)

                            action = CompensatingAction(
                                name=f"restore_{before.get('id', 'unknown')}",
                                executor=restore_record,
                            )
                        else:
                            # Update の場合は元の値に戻す
                            original_before = before.copy()
                            current_record = record

                            def revert_update(ctx, rec=current_record, orig=original_before):
                                data_list = ctx["data"]
                                for idx, item in enumerate(data_list):
                                    if (
                                        isinstance(item, dict)
                                        and isinstance(rec, dict)
                                        and item.get("id") == rec.get("id")
                                    ):
                                        data_list[idx] = orig
                                        break

                            action = CompensatingAction(
                                name=f"revert_{before.get('id', 'unknown')}",
                                executor=revert_update,
                            )

                        transaction.add_compensating_action(action)

            except Exception as e:
                result.add_failure(f"Error processing record {before}: {str(e)}")

        node.changes = result.changes
        node.errors = result.errors

        return result
