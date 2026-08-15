from typing import Any, Dict, List, Optional
from uuid import uuid4
from urllib.parse import urlparse
import ipaddress

from core.target import Target
from core.action import Action, Delete
from .base import BaseAdapter

# デフォルトタイムアウト（秒）
DEFAULT_TIMEOUT = 10


class RestAdapter(BaseAdapter):
    """REST API 用 Adapter"""

    def __init__(
        self,
        base_url: str,
        get_endpoint: str,
        create_endpoint: str,
        update_endpoint: str,
        delete_endpoint: str,
        timeout: int = DEFAULT_TIMEOUT,
        allow_private_ips: bool = False,
    ):
        # URL の検証
        self._validate_url(base_url, allow_private_ips)

        # エンドポイントの検証（パストラバーサル対策）
        for ep in [get_endpoint, create_endpoint, update_endpoint, delete_endpoint]:
            self._validate_endpoint(ep)

        self.base_url = base_url
        self.get_endpoint = get_endpoint
        self.create_endpoint = create_endpoint
        self.update_endpoint = update_endpoint
        self.delete_endpoint = delete_endpoint
        self.timeout = timeout
        self.allow_private_ips = allow_private_ips
        self._connected = False
        self._transactions = {}
        self.session = None

    @staticmethod
    def _validate_endpoint(endpoint: str) -> None:
        """エンドポイントの検証（パストトラバーサル対策）"""
        # ../  を含む場合は拒否
        if ".." in endpoint or endpoint.startswith("/"):
            raise ValueError("Invalid endpoint: cannot contain .. or start with /")

    @staticmethod
    def _validate_url(url: str, allow_private_ips: bool = False) -> None:
        """URL の検証（SSRF 対策）"""
        try:
            parsed = urlparse(url)

            # スキームの検証
            if parsed.scheme not in ("http", "https"):
                raise ValueError("Only HTTP and HTTPS are allowed")

            # ホスト名の検証
            if not parsed.netloc:
                raise ValueError("Invalid URL: missing hostname")

            # ホスト名とポートの検証
            hostname = parsed.hostname
            if not hostname:
                raise ValueError("Invalid hostname")

            # プライベート IP の検証
            if not allow_private_ips:
                # ホスト名から IP を解決（DNS リバインディング対策）
                try:
                    import socket
                    try:
                        ip_addr = socket.gethostbyname(hostname)
                        ip = ipaddress.ip_address(ip_addr)
                        if ip.is_private or ip.is_loopback or ip.is_reserved:
                            raise ValueError(
                                "Private/reserved IP addresses are not allowed"
                            )
                    except socket.gaierror:
                        # DNS 解決失敗時も慎重に
                        pass

                    # リテラル IP の場合も検証
                    try:
                        ip = ipaddress.ip_address(hostname)
                        if ip.is_private or ip.is_loopback or ip.is_reserved:
                            raise ValueError(
                                "Private/reserved IP addresses are not allowed"
                            )
                    except ValueError:
                        pass  # ホスト名の場合はここで例外になる

                except Exception as e:
                    if "not allowed" not in str(e):
                        raise ValueError(f"URL validation failed: {str(e)}")
                    raise

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

    def connect(self) -> None:
        """REST API に接続"""
        try:
            import requests

            self.session = requests.Session()
            # 接続テスト（タイムアウト付き）
            response = self.session.get(
                f"{self.base_url}/{self.get_endpoint}",
                timeout=self.timeout,
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
                f"{self.base_url}/{self.get_endpoint}",
                timeout=self.timeout,
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
                        timeout=self.timeout,
                    )
                else:
                    # 作成
                    response = self.session.post(
                        f"{self.base_url}/{self.create_endpoint}",
                        json=record,
                        timeout=self.timeout,
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
