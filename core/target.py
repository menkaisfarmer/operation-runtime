from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List
from dataclasses import dataclass


class Target(ABC):
    """操作対象を表す基底クラス"""

    @abstractmethod
    def matches(self, record: Dict[str, Any]) -> bool:
        """レコードがこのターゲットに該当するか判定"""
        pass

    @abstractmethod
    def filter(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """レコード集合をフィルタリング"""
        pass


@dataclass
class Where(Target):
    """条件指定による対象集合"""

    conditions: Dict[str, Any]

    def matches(self, record: Dict[str, Any]) -> bool:
        """すべての条件にマッチするか"""
        for key, condition in self.conditions.items():
            if isinstance(condition, dict):
                # {op: value} 形式のフィルタリング
                for op, value in condition.items():
                    record_value = record.get(key)
                    if not self._match_condition(record_value, op, value):
                        return False
            else:
                # 等値チェック
                if record.get(key) != condition:
                    return False
        return True

    def _match_condition(self, record_value: Any, op: str, value: Any) -> bool:
        """条件演算子による比較"""
        if op == "gte":
            return record_value >= value
        elif op == "gt":
            return record_value > value
        elif op == "lte":
            return record_value <= value
        elif op == "lt":
            return record_value < value
        elif op == "eq":
            return record_value == value
        elif op == "ne":
            return record_value != value
        elif op == "in":
            return record_value in value
        else:
            raise ValueError(f"Unknown operator: {op}")

    def filter(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """条件にマッチするレコードだけを返す"""
        return [r for r in records if self.matches(r)]

    def __repr__(self) -> str:
        return f"Where({self.conditions})"


@dataclass
class CustomTarget(Target):
    """カスタム条件による対象集合"""

    predicate: Callable[[Dict[str, Any]], bool]

    def matches(self, record: Dict[str, Any]) -> bool:
        return self.predicate(record)

    def filter(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [r for r in records if self.matches(r)]

    def __repr__(self) -> str:
        return f"CustomTarget({self.predicate.__name__})"


class AllRecords(Target):
    """すべてのレコードを対象とする"""

    def matches(self, record: Dict[str, Any]) -> bool:
        return True

    def filter(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return records

    def __repr__(self) -> str:
        return "AllRecords()"
