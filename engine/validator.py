from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.plan import Plan, PlanNode
from core.operation import Operation
from core.action import Delete


@dataclass
class ValidationError:
    """バリデーションエラー"""

    code: str
    message: str
    node_id: Optional[str] = None
    severity: str = "error"  # error, warning

    def __repr__(self) -> str:
        return f"ValidationError({self.code}: {self.message})"


class Validator:
    """操作実行前のバリデーション"""

    def validate(
        self, plan: Plan, data: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """計画を検証"""
        errors = []

        for node_id, node in plan.nodes.items():
            errors.extend(self._validate_node(node, data))

        errors.extend(self._validate_plan_structure(plan))

        return errors

    def _validate_node(
        self, node: PlanNode, data: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """単一ノードを検証"""
        errors = []

        # ターゲットが空の場合の警告
        if node.target_count == 0 and node.target is not None:
            errors.append(
                ValidationError(
                    "NO_TARGET_MATCH",
                    f"No records match the target condition",
                    node.operation_id,
                    severity="warning",
                )
            )

        # Delete 操作の検証
        for action in node.actions:
            if isinstance(action, Delete):
                if node.target_count > 100:
                    errors.append(
                        ValidationError(
                            "LARGE_DELETE",
                            f"Attempting to delete {node.target_count} records. "
                            "Please confirm.",
                            node.operation_id,
                            severity="warning",
                        )
                    )

        return errors

    def _validate_plan_structure(self, plan: Plan) -> List[ValidationError]:
        """計画全体の構造を検証"""
        errors = []

        # サイクルの検出
        visited = set()
        rec_stack = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = plan.nodes[node_id]
            for dep_id in node.dependencies:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in plan.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    errors.append(
                        ValidationError(
                            "CYCLE_DETECTED",
                            f"Circular dependency detected in operation graph",
                            severity="error",
                        )
                    )

        return errors

    def is_valid(
        self, plan: Plan, data: List[Dict[str, Any]]
    ) -> bool:
        """計画が有効か（エラーなし）"""
        errors = self.validate(plan, data)
        return not any(e.severity == "error" for e in errors)

    def get_errors(
        self, plan: Plan, data: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """エラーのみを取得"""
        return [e for e in self.validate(plan, data) if e.severity == "error"]

    def get_warnings(
        self, plan: Plan, data: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """警告のみを取得"""
        return [
            e
            for e in self.validate(plan, data)
            if e.severity == "warning"
        ]
