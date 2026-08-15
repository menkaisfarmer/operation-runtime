from typing import List, Dict, Any

from core.operation import Operation, SimpleOperation, Sequence, Parallel
from core.plan import Plan, PlanNode, ExecutionStatus


class Planner:
    """Operation を Plan に変換する"""

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
        """依存関係に基づいて実行順序を決定（トポロジカルソート）"""
        order = []
        visited = set()
        in_progress = set()

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in in_progress:
                raise ValueError(f"Circular dependency detected: {node_id}")

            in_progress.add(node_id)
            node = plan.nodes[node_id]

            for dep_id in node.dependencies:
                visit(dep_id)

            in_progress.remove(node_id)
            visited.add(node_id)
            order.append(node_id)

        for node_id in plan.nodes:
            visit(node_id)

        plan.set_execution_order(order)
