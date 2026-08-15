from abc import ABC, abstractmethod
from typing import Any, Callable, Dict
from dataclasses import dataclass, field


class Action(ABC):
    """操作の基底クラス"""

    @abstractmethod
    def apply(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """1レコードに操作を適用し、変更後のレコードを返す"""
        pass


@dataclass
class Update(Action):
    """更新操作"""

    updates: Dict[str, Any] = field(default_factory=dict)

    def apply(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """レコードを更新する"""
        return {**record, **self.updates}

    def __repr__(self) -> str:
        return f"Update({self.updates})"


@dataclass
class Create(Action):
    """作成操作"""

    data: Dict[str, Any] = field(default_factory=dict)

    def apply(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """新規レコードを作成する（既存レコードは無視）"""
        return {**self.data}

    def __repr__(self) -> str:
        return f"Create({self.data})"


@dataclass
class Delete(Action):
    """削除操作"""

    def apply(self, record: Dict[str, Any]) -> None:
        """レコードを削除する"""
        return None

    def __repr__(self) -> str:
        return "Delete()"


@dataclass
class Transform(Action):
    """変換操作"""

    transformer: Callable[[Dict[str, Any]], Dict[str, Any]]

    def apply(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """カスタム変換関数を適用"""
        return self.transformer(record)

    def __repr__(self) -> str:
        return f"Transform({self.transformer.__name__})"
