import sqlite3
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pathlib import Path

from core.target import Target
from core.action import Action, Update, Delete
from .base import BaseAdapter


class SQLiteAdapter(BaseAdapter):
    """SQLite データベース用 Adapter"""

    def __init__(self, db_path: str, table_name: str):
        # パスの検証
        db_path = str(Path(db_path).resolve())
        if not db_path.endswith(".db"):
            raise ValueError("Database file must have .db extension")

        # テーブル名の検証（英数字とアンダースコアのみ）
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            raise ValueError(
                "Table name must contain only alphanumeric characters and underscores"
            )

        self.db_path = db_path
        self.table_name = table_name
        self.conn: Optional[sqlite3.Connection] = None
        self._transactions = {}

    def connect(self) -> None:
        """データベースに接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def disconnect(self) -> None:
        """データベースから切断"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def read(
        self, target: Optional[Target] = None
    ) -> List[Dict[str, Any]]:
        """データベースからデータを読み取る"""
        if not self.is_connected():
            raise RuntimeError("Adapter not connected")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {self.table_name}")
        rows = cursor.fetchall()

        records = [dict(row) for row in rows]

        if target is not None:
            records = target.filter(records)

        return records

    def write(self, records: List[Dict[str, Any]]) -> bool:
        """データベースにデータを書き込む"""
        if not self.is_connected():
            raise RuntimeError("Adapter not connected")

        try:
            cursor = self.conn.cursor()

            # テーブルをクリア
            cursor.execute(f"DELETE FROM {self.table_name}")

            # 新しいデータを挿入
            if records:
                columns = list(records[0].keys())
                placeholders = ", ".join(["?"] * len(columns))
                insert_sql = (
                    f"INSERT INTO {self.table_name} "
                    f"({', '.join(columns)}) VALUES ({placeholders})"
                )

                for record in records:
                    values = [record.get(col) for col in columns]
                    cursor.execute(insert_sql, values)

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
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
        try:
            self.conn.execute("BEGIN")
            # スナップショット用にデータを読み取る
            snapshot = self.read()
            self._transactions[tx_id] = snapshot
            return tx_id
        except Exception as e:
            raise RuntimeError(f"Begin transaction failed: {str(e)}")

    def commit_transaction(self, tx_id: str) -> bool:
        """トランザクションコミット"""
        if tx_id not in self._transactions:
            return False

        try:
            self.conn.commit()
            del self._transactions[tx_id]
            return True
        except Exception as e:
            raise RuntimeError(f"Commit failed: {str(e)}")

    def rollback_transaction(self, tx_id: str) -> bool:
        """トランザクションロールバック"""
        if tx_id not in self._transactions:
            return False

        try:
            self.conn.rollback()
            snapshot = self._transactions[tx_id]
            self.write(snapshot)
            del self._transactions[tx_id]
            return True
        except Exception as e:
            raise RuntimeError(f"Rollback failed: {str(e)}")

    def is_connected(self) -> bool:
        """接続状態を確認"""
        return self.conn is not None

    def create_table(
        self, schema: Dict[str, str]
    ) -> None:
        """テーブルを作成"""
        if not self.is_connected():
            raise RuntimeError("Adapter not connected")

        columns_def = ", ".join(
            [f"{col} {col_type}" for col, col_type in schema.items()]
        )
        create_sql = f"CREATE TABLE IF NOT EXISTS {self.table_name} ({columns_def})"

        cursor = self.conn.cursor()
        cursor.execute(create_sql)
        self.conn.commit()
