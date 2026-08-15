from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.target import Target
from core.action import Action


class BaseAdapter(ABC):
    """Adapter の基底クラス"""

    @abstractmethod
    def connect(self) -> None:
        """バックエンドへの接続"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """バックエンドからの切断"""
        pass

    @abstractmethod
    def read(self, target: Optional[Target] = None) -> List[Dict[str, Any]]:
        """データを読み取る"""
        pass

    @abstractmethod
    def write(self, records: List[Dict[str, Any]]) -> bool:
        """データを書き込む"""
        pass

    @abstractmethod
    def apply_action(
        self, record: Dict[str, Any], action: Action
    ) -> Dict[str, Any]:
        """アクションを適用する"""
        pass

    @abstractmethod
    def begin_transaction(self) -> str:
        """トランザクション開始"""
        pass

    @abstractmethod
    def commit_transaction(self, tx_id: str) -> bool:
        """トランザクションコミット"""
        pass

    @abstractmethod
    def rollback_transaction(self, tx_id: str) -> bool:
        """トランザクションロールバック"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """接続状態を確認"""
        pass
