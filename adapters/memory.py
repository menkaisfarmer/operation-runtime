from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.target import Target
from core.action import Action, Delete
from .base import BaseAdapter


class MemoryAdapter(BaseAdapter):
    """メモリ内データストア用 Adapter"""

    def __init__(self, data: Optional[List[Dict[str, Any]]] = None):
        self.data = data or []
        self._connected = False
        self._transactions = {}

    def connect(self) -> None:
        """接続（メモリなので何もしない）"""
        self._connected = True

    def disconnect(self) -> None:
        """切断"""
        self._connected = False

    def read(
        self, target: Optional[Target] = None
    ) -> List[Dict[str, Any]]:
        """データを読み取る"""
        if not self._connected:
            raise RuntimeError("Adapter not connected")

        if target is None:
            return [item.copy() for item in self.data]

        return [item.copy() for item in target.filter(self.data)]

    def write(self, records: List[Dict[str, Any]]) -> bool:
        """データを書き込む"""
        if not self._connected:
            raise RuntimeError("Adapter not connected")

        self.data = [item.copy() for item in records]
        return True

    def apply_action(
        self, record: Dict[str, Any], action: Action
    ) -> Dict[str, Any]:
        """アクションを適用"""
        if isinstance(action, Delete):
            return None
        return action.apply(record)

    def begin_transaction(self) -> str:
        """トランザクション開始"""
        if not self._connected:
            raise RuntimeError("Adapter not connected")

        tx_id = str(uuid4())
        # スナップショットを保存
        self._transactions[tx_id] = [item.copy() for item in self.data]
        return tx_id

    def commit_transaction(self, tx_id: str) -> bool:
        """トランザクションコミット"""
        if tx_id not in self._transactions:
            return False

        del self._transactions[tx_id]
        return True

    def rollback_transaction(self, tx_id: str) -> bool:
        """トランザクションロールバック"""
        if tx_id not in self._transactions:
            return False

        snapshot = self._transactions[tx_id]
        self.data = [item.copy() for item in snapshot]
        del self._transactions[tx_id]
        return True

    def is_connected(self) -> bool:
        """接続状態を確認"""
        return self._connected
