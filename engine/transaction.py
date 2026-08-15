from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime


class TransactionState(Enum):
    """トランザクションの状態"""

    PENDING = "pending"
    EXECUTING = "executing"
    COMMITTED = "committed"
    ABORTED = "aborted"
    ROLLING_BACK = "rolling_back"


@dataclass
class CompensatingAction:
    """補償操作（ロールバック用）"""

    name: str
    executor: Callable[[Dict[str, Any]], None]
    params: Dict[str, Any] = field(default_factory=dict)
    executed: bool = False

    def execute(self, context: Dict[str, Any]) -> None:
        """補償操作を実行"""
        self.executor(context)
        self.executed = True

    def __repr__(self) -> str:
        return f"CompensatingAction({self.name})"


@dataclass
class TransactionLog:
    """トランザクションログ"""

    transaction_id: str
    operation_id: str
    state: TransactionState = TransactionState.PENDING
    changes: List[Dict[str, Any]] = field(default_factory=list)
    compensating_actions: List[CompensatingAction] = field(
        default_factory=list
    )
    savepoints: Dict[str, List[Dict[str, Any]]] = field(
        default_factory=dict
    )
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    committed_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None

    def add_change(self, change: Dict[str, Any]) -> None:
        """変更をログに記録"""
        self.changes.append(change)

    def add_compensating_action(self, action: CompensatingAction) -> None:
        """補償操作を追加"""
        self.compensating_actions.append(action)

    def add_error(self, error: str) -> None:
        """エラーを記録"""
        self.errors.append(error)

    def create_savepoint(self, name: str, data_snapshot: List[Dict[str, Any]]) -> None:
        """セーブポイントを作成"""
        self.savepoints[name] = [item.copy() for item in data_snapshot]

    def rollback_to_savepoint(
        self, name: str, data: List[Dict[str, Any]]
    ) -> bool:
        """セーブポイントまでロールバック"""
        if name not in self.savepoints:
            return False

        snapshot = self.savepoints[name]
        data.clear()
        data.extend([item.copy() for item in snapshot])
        return True

    def rollback(self, data: List[Dict[str, Any]]) -> bool:
        """トランザクションロールバック"""
        if self.state != TransactionState.COMMITTED:
            return False

        self.state = TransactionState.ROLLING_BACK

        # 補償操作をリバースで実行
        for action in reversed(self.compensating_actions):
            try:
                action.execute({"data": data})
            except Exception as e:
                self.add_error(f"Compensating action failed: {str(e)}")
                return False

        self.state = TransactionState.ABORTED
        self.rolled_back_at = datetime.now()
        return True

    def get_summary(self) -> Dict[str, Any]:
        """ログの概要を取得"""
        return {
            "transaction_id": self.transaction_id,
            "operation_id": self.operation_id,
            "state": self.state.value,
            "changes_count": len(self.changes),
            "compensating_actions_count": len(self.compensating_actions),
            "errors_count": len(self.errors),
            "created_at": self.created_at.isoformat(),
            "committed_at": self.committed_at.isoformat()
            if self.committed_at
            else None,
            "rolled_back_at": self.rolled_back_at.isoformat()
            if self.rolled_back_at
            else None,
        }

    def __repr__(self) -> str:
        return (
            f"TransactionLog({self.transaction_id}, "
            f"state={self.state.value}, "
            f"changes={len(self.changes)})"
        )


class Transaction:
    """トランザクション管理"""

    def __init__(self, transaction_id: str, operation_id: str):
        self.log = TransactionLog(transaction_id, operation_id)
        self._active = True

    def begin(self) -> None:
        """トランザクション開始"""
        self.log.state = TransactionState.EXECUTING

    def commit(self) -> None:
        """トランザクションコミット"""
        self.log.state = TransactionState.COMMITTED
        self.log.committed_at = datetime.now()
        self._active = False

    def abort(self) -> None:
        """トランザクション中止"""
        self.log.state = TransactionState.ABORTED
        self._active = False

    def rollback(self, data: List[Dict[str, Any]]) -> bool:
        """トランザクションロールバック"""
        # COMMITTED 状態でのみロールバック可能
        if self.log.state != TransactionState.COMMITTED:
            return False

        self.log.state = TransactionState.ROLLING_BACK

        # 補償操作をリバースで実行
        for action in reversed(self.log.compensating_actions):
            try:
                action.execute({"data": data})
            except Exception as e:
                self.log.add_error(f"Compensating action failed: {str(e)}")
                return False

        self.log.state = TransactionState.ABORTED
        self.log.rolled_back_at = datetime.now()
        return True

    def add_change(self, change: Dict[str, Any]) -> None:
        """変更をログに記録"""
        self.log.add_change(change)

    def add_compensating_action(self, action: CompensatingAction) -> None:
        """補償操作を追加"""
        self.log.add_compensating_action(action)

    def add_error(self, error: str) -> None:
        """エラーを記録"""
        self.log.add_error(error)

    def is_active(self) -> bool:
        """トランザクションがアクティブか"""
        return self._active

    def is_committed(self) -> bool:
        """コミット済みか"""
        return self.log.state == TransactionState.COMMITTED

    def get_log(self) -> TransactionLog:
        """ログを取得"""
        return self.log
