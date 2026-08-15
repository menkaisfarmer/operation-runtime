from typing import List, Dict, Any

from core.operation import Operation, SimpleOperation, Sequence, Parallel
from core.plan import Plan, PlanNode, ExecutionStatus
from .scheduler import Scheduler


class Planner:
    """Operation を Plan に変換する"""

    def __init__(self):
        self.scheduler = Scheduler()

    def plan(
        self, operation: Operation, data: List[Dict[str, Any]]
    ) -> Plan:
        """操作を実行可能な計画に変換"""
        plan = Plan(operation)
        self._build_plan_nodes(operation, plan, data)
        self._build_execution_order(plan)
        return plan

    def _build_plan_nodes(
        self, operation: Operation, plan: Plan, data: List[Dict[str, Any]]
    ) -> None:
        """操作からPlanNodeを構築"""
        if isinstance(operation, SimpleOperation):
            self._add_simple_node(operation, plan, data)
        elif isinstance(operation, Sequence):
            for sub_op in operation.operations:
                self._build_plan_nodes(sub_op, plan, data)
        elif isinstance(operation, Parallel):
            for sub_op in operation.operations:
                self._build_plan_nodes(sub_op, plan, data)

    def _add_simple_node(
        self, operation: SimpleOperation, plan: Plan, data: List[Dict[str, Any]]
    ) -> None:
        """SimpleOperationからノードを追加"""
        target = operation.get_target()
        actions = operation.get_actions()

        if target:
            target_records = target.filter(data)
        else:
            target_records = data

        node = PlanNode(
            operation_id=operation.op_id,
            operation=operation,
            target=target,
            actions=actions,
            dependencies=operation.dependencies,
            target_count=len(target_records),
            status=ExecutionStatus.PENDING,
        )
        plan.add_node(node)

    def _build_execution_order(self, plan: Plan) -> None:
        """依存関係と競合を考慮して実行順序を決定"""
        # Scheduler を使用して競合を検出し、実行順序を決定
        execution_order, conflicts = self.scheduler.schedule(plan)
        plan.set_execution_order(execution_order)

        # 競合情報を Plan に付与
        plan.conflicts = conflicts
