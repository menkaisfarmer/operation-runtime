from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from core.action import Update, Delete
from core.target import Where, AllRecords
from core.operation import SimpleOperation
from .parser import ParsedIntent, NaturalLanguageParser


@dataclass
class GeneratedOperation:
    """生成された Operation とメタ情報"""

    operation: Optional[SimpleOperation]
    intent: ParsedIntent
    confidence: float
    explanation: str
    suggestions: List[str]


class OperationGenerator:
    """自然言語の意図から Operation を生成"""

    def __init__(self):
        self.parser = NaturalLanguageParser()

    def generate_from_text(
        self, text: str, data: Optional[List[Dict[str, Any]]] = None
    ) -> GeneratedOperation:
        """テキストから Operation を生成"""
        # テキストを解析
        intent = self.parser.parse(text)

        # Operation を生成
        if intent.operation_type == "update":
            return self._generate_update_operation(intent, data)
        elif intent.operation_type == "delete":
            return self._generate_delete_operation(intent, data)
        elif intent.operation_type == "list":
            return self._generate_list_operation(intent, data)
        else:
            return GeneratedOperation(
                operation=None,
                intent=intent,
                confidence=0.0,
                explanation="Could not determine operation type",
                suggestions=self._get_suggestions(text),
            )

    def _generate_update_operation(
        self,
        intent: ParsedIntent,
        data: Optional[List[Dict[str, Any]]] = None,
    ) -> GeneratedOperation:
        """UPDATE Operation を生成"""
        try:
            # ターゲットを生成
            target = self._parse_target(intent.target_condition)

            # 更新値を解析
            updates = self._parse_updates(intent.update_values)

            if not updates:
                return GeneratedOperation(
                    operation=None,
                    intent=intent,
                    confidence=intent.confidence * 0.5,
                    explanation="Failed to parse update values",
                    suggestions=["Specify values: key=value"],
                )

            # Operation を作成
            operation = SimpleOperation(
                target=target,
                actions=[Update(updates)],
            )

            # サジェッションを生成
            suggestions = self._generate_suggestions(operation, data)

            return GeneratedOperation(
                operation=operation,
                intent=intent,
                confidence=intent.confidence,
                explanation=intent.explanation,
                suggestions=suggestions,
            )

        except Exception as e:
            return GeneratedOperation(
                operation=None,
                intent=intent,
                confidence=0.0,
                explanation=f"Error generating operation: {str(e)}",
                suggestions=[],
            )

    def _generate_delete_operation(
        self,
        intent: ParsedIntent,
        data: Optional[List[Dict[str, Any]]] = None,
    ) -> GeneratedOperation:
        """DELETE Operation を生成"""
        try:
            target = self._parse_target(intent.target_condition)

            operation = SimpleOperation(
                target=target,
                actions=[Delete()],
            )

            suggestions = [
                "⚠️ This operation will DELETE records permanently",
                "Use --dry-run to preview changes before execution",
            ]

            if data:
                target_records = target.filter(data) if isinstance(target, Where) else data
                suggestions.insert(
                    0, f"This will affect {len(target_records)} record(s)"
                )

            return GeneratedOperation(
                operation=operation,
                intent=intent,
                confidence=intent.confidence,
                explanation=intent.explanation,
                suggestions=suggestions,
            )

        except Exception as e:
            return GeneratedOperation(
                operation=None,
                intent=intent,
                confidence=0.0,
                explanation=f"Error generating operation: {str(e)}",
                suggestions=[],
            )

    def _generate_list_operation(
        self,
        intent: ParsedIntent,
        data: Optional[List[Dict[str, Any]]] = None,
    ) -> GeneratedOperation:
        """LIST Operation を生成"""
        suggestions = []

        if data:
            if intent.target_condition:
                target = self._parse_target(intent.target_condition)
                records = target.filter(data) if isinstance(target, Where) else data
                suggestions.append(f"Found {len(records)} matching record(s)")
            else:
                suggestions.append(f"Total: {len(data)} record(s)")

        return GeneratedOperation(
            operation=None,
            intent=intent,
            confidence=intent.confidence,
            explanation="List operation - no execution needed",
            suggestions=suggestions,
        )

    def _parse_target(self, condition: Optional[str]):
        """条件文からターゲットを生成"""
        if not condition:
            return AllRecords()

        # "key=value" をパースして Where に変換
        parts = condition.split(",")
        conditions = {}

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                conditions[key.strip()] = value.strip()

        if conditions:
            return Where(conditions)

        return AllRecords()

    def _parse_updates(self, update_str: Optional[str]) -> Optional[Dict[str, Any]]:
        """更新値文字列をパース"""
        if not update_str:
            return None

        updates = {}
        parts = update_str.split(",")

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()

                # 型推定
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

                updates[key] = value

        return updates if updates else None

    def _generate_suggestions(
        self,
        operation: SimpleOperation,
        data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """操作に対するサジェッションを生成"""
        suggestions = []

        if data and isinstance(operation.target, Where):
            target_records = operation.target.filter(data)
            suggestions.append(f"This will affect {len(target_records)} record(s)")

        if len(operation.actions) > 1:
            suggestions.append(f"{len(operation.actions)} actions will be applied")

        suggestions.append("Use --dry-run to preview changes")

        return suggestions

    def _get_suggestions(self, text: str) -> List[str]:
        """テキストが不明確な場合のサジェッション"""
        return [
            "Try: 'Update records where status=pending to status=completed'",
            "Try: 'Delete records where status=archived'",
            "Try: 'List all records'",
            "Try: 'UPDATE table SET value=100 WHERE type=A'",
        ]
