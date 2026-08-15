from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.plan import PlanNode, Plan


class ConflictType(Enum):
    """競合の種類"""

    WRITE_WRITE = "write_write"
    READ_WRITE = "read_write"
    RESOURCE_CONFLICT = "resource_conflict"


@dataclass
class Conflict:
    """操作間の競合情報"""

    node_id_a: str
    node_id_b: str
    conflict_type: ConflictType
    affected_fields: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Conflict({self.node_id_a} vs {self.node_id_b}, "
            f"type={self.conflict_type.value})"
        )


class Scheduler:
    """高度なスケジューリングエンジン"""

    def schedule(self, plan: Plan) -> Tuple[List[str], List[Conflict]]:
        """実行計画のスケジューリング"""
        conflicts = self._detect_conflicts(plan)
        execution_order = self._topological_sort_with_conflicts(
            plan, conflicts
        )
        return execution_order, conflicts

    def _detect_conflicts(self, plan: Plan) -> List[Conflict]:
        """操作間の競合を検出"""
        conflicts = []
        node_ids = list(plan.nodes.keys())

        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                node_a = plan.nodes[node_ids[i]]
                node_b = plan.nodes[node_ids[j]]

                conflict = self._check_conflict(node_a, node_b)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _check_conflict(
        self, node_a: PlanNode, node_b: PlanNode
    ) -> Optional[Conflict]:
        """2つのノード間の競合を検出"""
        # 同じターゲットへの操作
        if self._same_target(node_a, node_b):
            # Write-Write 競合
            if self._is_write_operation(node_a) and self._is_write_operation(
                node_b
            ):
                return Conflict(
                    node_a.operation_id,
                    node_b.operation_id,
                    ConflictType.WRITE_WRITE,
                )

        # リソース競合（同じフィールドへの操作）
        conflicting_fields = self._get_conflicting_fields(node_a, node_b)
        if conflicting_fields:
            return Conflict(
                node_a.operation_id,
                node_b.operation_id,
                ConflictType.RESOURCE_CONFLICT,
                affected_fields=conflicting_fields,
            )

        return None

    def _same_target(self, node_a: PlanNode, node_b: PlanNode) -> bool:
        """同じターゲットを持つか"""
        if node_a.target is None or node_b.target is None:
            return False
        return str(node_a.target) == str(node_b.target)

    def _is_write_operation(self, node: PlanNode) -> bool:
        """書き込み操作か"""
        from core.action import Update, Create, Delete, Delete

        return any(
            isinstance(action, (Update, Create, Delete))
            for action in node.actions
        )

    def _get_conflicting_fields(
        self, node_a: PlanNode, node_b: PlanNode
    ) -> List[str]:
        """競合するフィールドを取得"""
        from core.action import Update

        fields_a = set()
        fields_b = set()

        for action in node_a.actions:
            if isinstance(action, Update):
                fields_a.update(action.updates.keys())

        for action in node_b.actions:
            if isinstance(action, Update):
                fields_b.update(action.updates.keys())

        return list(fields_a & fields_b)

    def _topological_sort_with_conflicts(
        self, plan: Plan, conflicts: List[Conflict]
    ) -> List[str]:
        """競合を考慮したトポロジカルソート"""
        # 競合する操作には順序依存関係を追加
        temp_dependencies = {
            node_id: set(plan.nodes[node_id].dependencies)
            for node_id in plan.nodes
        }

        for conflict in conflicts:
            if conflict.conflict_type == ConflictType.WRITE_WRITE:
                # Write-Write 競合は順序化
                temp_dependencies[conflict.node_id_b].add(
                    conflict.node_id_a
                )

        # トポロジカルソート
        visited = set()
        in_progress = set()
        order = []

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in in_progress:
                raise ValueError(
                    f"Circular dependency detected: {node_id}"
                )

            in_progress.add(node_id)
            for dep_id in temp_dependencies[node_id]:
                visit(dep_id)

            in_progress.remove(node_id)
            visited.add(node_id)
            order.append(node_id)

        for node_id in plan.nodes:
            visit(node_id)

        return order

    def can_parallelize(
        self, node_ids: List[str], conflicts: List[Conflict]
    ) -> bool:
        """ノードが並列実行可能か"""
        node_set = set(node_ids)

        for conflict in conflicts:
            if (
                conflict.node_id_a in node_set
                and conflict.node_id_b in node_set
            ):
                return False

        return True
