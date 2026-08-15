from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.target import Target
from core.action import Action, Delete
from .base import BaseAdapter


class RestAdapter(BaseAdapter):
    """REST API 用 Adapter"""

    def __init__(
        self,
        base_url: str,
        get_endpoint: str,
        create_endpoint: str,
        update_endpoint: str,
        delete_endpoint: str,
    ):
        self.base_url = base_url
        self.get_endpoint = get_endpoint
        self.create_endpoint = create_endpoint
        self.update_endpoint = update_endpoint
        self.delete_endpoint = delete_endpoint
        self._connected = False
        self._transactions = {}
        self.session = None

    def connect(self) -> None:
        """REST API に接続"""
        try:
            import requests

            self.session = requests.Session()
            # 接続テスト
            response = self.session.get(
                f"{self.base_url}/{self.get_endpoint}"
            )
            if response.status_code == 200:
                self._connected = True
            else:
                raise RuntimeError(
                    f"Connection failed: {response.status_code}"
                )
        except Exception as e:
            raise RuntimeError(f"Connect failed: {str(e)}")

    def disconnect(self) -> None:
        """REST API から切断"""
        if self.session:
            self.session.close()
            self.session = None
        self._connected = False

    def read(
        self, target: Optional[Target] = None
    ) -> List[Dict[str, Any]]:
        """REST API からデータを読み取る"""
        if not self.is_connected():
            raise RuntimeError("Adapter not connected")

        try:
            response = self.session.get(
                f"{self.base_url}/{self.get_endpoint}"
            )
            response.raise_for_status()

            data = response.json()
            records = data if isinstance(data, list) else [data]

            if target is not None:
                records = target.filter(records)

            return records
        except Exception as e:
            raise RuntimeError(f"Read failed: {str(e)}")

    def write(self, records: List[Dict[str, Any]]) -> bool:
        """REST API にデータを書き込む"""
        if not self.is_connected():
            raise RuntimeError("Adapter not connected")

        try:
            for record in records:
                if record.get("id"):
                    # 更新
                    response = self.session.put(
                        f"{self.base_url}/{self.update_endpoint}",
                        json=record,
                    )
                else:
                    # 作成
                    response = self.session.post(
                        f"{self.base_url}/{self.create_endpoint}",
                        json=record,
                    )

                response.raise_for_status()

            return True
        except Exception as e:
            raise RuntimeError(f"Write failed: {str(e)}")

    def apply_action(
        self, record: Dict[str, Any], action: Action
    ) -> Dict[str, Any]:
        """アクションを適用"""
        if isinstance(action, Delete):
            return None
        return action.apply(record)

    def begin_transaction(self) -> str:
        """トランザクション開始"""
        if not self.is_connected():
            raise RuntimeError("Adapter not connected")

        tx_id = str(uuid4())
        # スナップショット用にデータを読み取る
        snapshot = self.read()
        self._transactions[tx_id] = snapshot
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

        try:
            snapshot = self._transactions[tx_id]
            self.write(snapshot)
            del self._transactions[tx_id]
            return True
        except Exception as e:
            raise RuntimeError(f"Rollback failed: {str(e)}")

    def is_connected(self) -> bool:
        """接続状態を確認"""
        return self._connected and self.session is not None
