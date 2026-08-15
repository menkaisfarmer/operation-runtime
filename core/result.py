from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from engine.transaction import TransactionLog


@dataclass
class Result:
    """操作結果を表す基底クラス"""

    operation_id: str
    success_count: int = 0
    failure_count: int = 0
    changes: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def add_success(self, change: Dict[str, Any]) -> None:
        """成功した変更を記録"""
        self.success_count += 1
        self.changes.append(change)

    def add_failure(self, error: str) -> None:
        """失敗を記録"""
        self.failure_count += 1
        self.errors.append(error)

    def is_successful(self) -> bool:
        """全体として成功したか"""
        return self.failure_count == 0

    def get_summary(self) -> Dict[str, Any]:
        """結果の概要"""
        return {
            "operation_id": self.operation_id,
            "success": self.is_successful(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_count": self.success_count + self.failure_count,
            "changes": self.changes,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"Result({self.operation_id}, "
            f"success={self.success_count}, "
            f"failed={self.failure_count})"
        )


@dataclass
class ExecutionResult:
    """全体的な実行結果"""

    operation_id: str
    results: Dict[str, Result] = field(default_factory=dict)
    total_success: int = 0
    total_failure: int = 0
    undo_log: List[Dict[str, Any]] = field(default_factory=list)
    transaction_log: Optional[Any] = None

    def add_result(self, result: Result) -> None:
        """操作の結果を追加"""
        self.results[result.operation_id] = result
        self.total_success += result.success_count
        self.total_failure += result.failure_count

    def add_undo_log(self, log: Dict[str, Any]) -> None:
        """Undo用ログを追加"""
        self.undo_log.append(log)

    def is_successful(self) -> bool:
        """全体として成功したか"""
        return self.total_failure == 0

    def get_summary(self) -> Dict[str, Any]:
        """実行結果の概要"""
        return {
            "operation_id": self.operation_id,
            "success": self.is_successful(),
            "total_success": self.total_success,
            "total_failure": self.total_failure,
            "total": self.total_success + self.total_failure,
            "results": {k: v.get_summary() for k, v in self.results.items()},
        }

    def __repr__(self) -> str:
        return (
            f"ExecutionResult({self.operation_id}, "
            f"success={self.total_success}, "
            f"failed={self.total_failure})"
        )
