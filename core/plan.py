from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from .operation import Operation
from .action import Action
from .target import Target


class ExecutionStatus(Enum):
    """実行ステータス"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanNode:
    """実行計画のノード（1つの操作に対応）"""

    operation_id: str
    operation: Operation
    target: Optional[Target]
    actions: List[Action]
    dependencies: Set[str] = field(default_factory=set)
    target_count: int = 0
    status: ExecutionStatus = ExecutionStatus.PENDING
    changes: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def is_ready(self, completed_ops: Set[str]) -> bool:
        """すべての依存操作が完了したか"""
        return self.dependencies.issubset(completed_ops)

    def __repr__(self) -> str:
        return f"PlanNode({self.operation_id}, status={self.status.value}, target_count={self.target_count})"


@dataclass
class Plan:
    """操作の実行計画"""

    operation: Operation
    nodes: Dict[str, PlanNode] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)

    def add_node(self, node: PlanNode) -> None:
        """ノードを追加"""
        self.nodes[node.operation_id] = node

    def set_execution_order(self, order: List[str]) -> None:
        """実行順序を設定"""
        self.execution_order = order

    def get_ready_nodes(self, completed: Set[str]) -> List[PlanNode]:
        """実行可能なノードを取得"""
        ready = []
        for node_id in self.execution_order:
            node = self.nodes[node_id]
            if node.status == ExecutionStatus.PENDING and node.is_ready(completed):
                ready.append(node)
        return ready

    def get_total_target_count(self) -> int:
        """全体の対象件数"""
        return sum(node.target_count for node in self.nodes.values())

    def get_summary(self) -> Dict[str, Any]:
        """計画の概要を取得"""
        completed = {
            node_id
            for node_id, node in self.nodes.items()
            if node.status == ExecutionStatus.COMPLETED
        }
        failed = {
            node_id
            for node_id, node in self.nodes.items()
            if node.status == ExecutionStatus.FAILED
        }

        return {
            "total_nodes": len(self.nodes),
            "total_targets": self.get_total_target_count(),
            "completed_nodes": len(completed),
            "failed_nodes": len(failed),
            "remaining_nodes": len(self.nodes) - len(completed) - len(failed),
            "nodes": self.nodes,
        }

    def __repr__(self) -> str:
        summary = self.get_summary()
        return (
            f"Plan(nodes={summary['total_nodes']}, "
            f"targets={summary['total_targets']}, "
            f"status={summary['completed_nodes']}/{summary['total_nodes']})"
        )
