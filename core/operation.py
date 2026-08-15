from abc import ABC, abstractmethod
from typing import List, Optional, Set
from dataclasses import dataclass, field
from uuid import uuid4

from .action import Action
from .target import Target


class Operation(ABC):
    """操作の基底クラス"""

    def __init__(self, op_id: Optional[str] = None):
        self.op_id = op_id or str(uuid4())
        self.dependencies: Set[str] = set()

    @abstractmethod
    def get_actions(self) -> List[Action]:
        """この操作が含むアクションのリストを返す"""
        pass

    @abstractmethod
    def get_target(self) -> Optional[Target]:
        """この操作が対象とするターゲットを返す"""
        pass

    def add_dependency(self, other_op_id: str) -> None:
        """他の操作への依存関係を追加"""
        self.dependencies.add(other_op_id)

    def __repr__(self) -> str:
        return f"Operation({self.op_id})"


@dataclass
class SimpleOperation(Operation):
    """単純な操作: 1つのターゲットと1つ以上のアクション"""

    target: Target
    actions: List[Action] = field(default_factory=list)

    def __init__(
        self,
        target: Target,
        actions: List[Action],
        op_id: Optional[str] = None,
    ):
        super().__init__(op_id)
        self.target = target
        self.actions = actions

    def get_actions(self) -> List[Action]:
        return self.actions

    def get_target(self) -> Optional[Target]:
        return self.target

    def __repr__(self) -> str:
        return f"SimpleOperation(target={self.target}, actions={self.actions})"


@dataclass
class Sequence(Operation):
    """複数の操作を順序付けで実行"""

    operations: List[Operation] = field(default_factory=list)

    def __init__(self, *ops: Operation, op_id: Optional[str] = None):
        super().__init__(op_id)
        self.operations = list(ops)
        # 順序付けによって依存関係を自動設定
        for i in range(1, len(self.operations)):
            self.operations[i].add_dependency(self.operations[i - 1].op_id)

    def get_actions(self) -> List[Action]:
        """すべての操作から全アクションを抽出"""
        actions = []
        for op in self.operations:
            actions.extend(op.get_actions())
        return actions

    def get_target(self) -> Optional[Target]:
        """最初の操作のターゲットを返す"""
        if self.operations:
            return self.operations[0].get_target()
        return None

    def __repr__(self) -> str:
        return f"Sequence({', '.join(str(op) for op in self.operations)})"


@dataclass
class Parallel(Operation):
    """複数の操作を並列実行"""

    operations: List[Operation] = field(default_factory=list)

    def __init__(self, *ops: Operation, op_id: Optional[str] = None):
        super().__init__(op_id)
        self.operations = list(ops)

    def get_actions(self) -> List[Action]:
        actions = []
        for op in self.operations:
            actions.extend(op.get_actions())
        return actions

    def get_target(self) -> Optional[Target]:
        if self.operations:
            return self.operations[0].get_target()
        return None

    def __repr__(self) -> str:
        return f"Parallel({', '.join(str(op) for op in self.operations)})"
