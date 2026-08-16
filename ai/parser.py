import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedIntent:
    """解析された人間の意図"""

    operation_type: str  # "update", "delete", "list"
    target_condition: Optional[str]  # "status=pending"
    update_values: Optional[str]  # "status=completed"
    confidence: float  # 0.0-1.0
    explanation: str


class NaturalLanguageParser:
    """自然言語を Operation に変換するパーサー"""

    # キーワードマッピング
    UPDATE_KEYWORDS = [
        "update",
        "change",
        "set",
        "修正",
        "変更",
        "設定",
        "更新",
    ]
    DELETE_KEYWORDS = ["delete", "remove", "clear", "削除", "消す", "クリア"]
    LIST_KEYWORDS = ["list", "show", "display", "一覧", "表示", "確認"]
    WHERE_KEYWORDS = [
        "where",
        "if",
        "that",
        "条件",
        "ただし",
        "の内",
    ]

    def __init__(self):
        self.operation_patterns = [
            # "status=pending のレコードを status=completed に更新"
            (
                r"(.+?)(?:を|の)(.+?)(?:に|へ)(.+?)(?:に|へ)?(?:更新|修正|変更)",
                self._parse_update_pattern1,
            ),
            # "DELETE FROM table WHERE status=pending"
            (
                r"(?:delete|削除).*?(?:where|condition)?(.+?)$",
                self._parse_delete_pattern,
            ),
            # "LIST all records"
            (
                r"(?:list|show|一覧|表示)(?:\s+(.+?))?$",
                self._parse_list_pattern,
            ),
            # "UPDATE table SET status=completed WHERE status=pending"
            (
                r"(?:update|更新).*?(?:set|設定)(.+?)(?:where|条件)?(.+?)$",
                self._parse_update_pattern2,
            ),
        ]

    def parse(self, text: str) -> ParsedIntent:
        """自然言語テキストを解析"""
        text = text.strip()

        # 操作タイプを判定
        operation_type = self._detect_operation_type(text)

        # 条件と値を抽出
        target_condition = self._extract_condition(text)
        update_values = self._extract_values(text)

        # パターンマッチング
        for pattern, handler in self.operation_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
            if match:
                result = handler(match, text)
                if result:
                    return result

        # 操作タイプが判定できたら、その信頼度で返す
        if operation_type != "unknown":
            return ParsedIntent(
                operation_type=operation_type,
                target_condition=target_condition,
                update_values=update_values,
                confidence=0.7,
                explanation=f"Detected {operation_type} operation",
            )

        # デフォルト：低信頼度で返す
        return ParsedIntent(
            operation_type="unknown",
            target_condition=None,
            update_values=None,
            confidence=0.0,
            explanation="Could not parse intent from text",
        )

    def _detect_operation_type(self, text: str) -> str:
        """操作タイプを検出"""
        text_lower = text.lower()

        for keyword in self.UPDATE_KEYWORDS:
            if keyword in text_lower:
                return "update"

        for keyword in self.DELETE_KEYWORDS:
            if keyword in text_lower:
                return "delete"

        for keyword in self.LIST_KEYWORDS:
            if keyword in text_lower:
                return "list"

        return "unknown"

    def _parse_update_pattern1(
        self, match, text: str
    ) -> Optional[ParsedIntent]:
        """パターン1: target を update_value に更新"""
        try:
            target = match.group(1).strip()
            update_value = match.group(3).strip()

            # 条件と値を分離
            target_condition = self._extract_condition(target)
            update_values = self._extract_values(update_value)

            if target_condition or update_values:
                return ParsedIntent(
                    operation_type="update",
                    target_condition=target_condition,
                    update_values=update_values,
                    confidence=0.8,
                    explanation=f"Update {target} to {update_value}",
                )
        except Exception:
            pass

        return None

    def _parse_update_pattern2(
        self, match, text: str
    ) -> Optional[ParsedIntent]:
        """パターン2: SET ... WHERE ..."""
        try:
            set_clause = match.group(1).strip()
            where_clause = match.group(2).strip() if match.lastindex >= 2 else ""

            update_values = self._extract_values(set_clause)
            target_condition = (
                self._extract_condition(where_clause) if where_clause else None
            )

            if update_values:
                return ParsedIntent(
                    operation_type="update",
                    target_condition=target_condition,
                    update_values=update_values,
                    confidence=0.85,
                    explanation=f"Update values: {update_values}",
                )
        except Exception:
            pass

        return None

    def _parse_delete_pattern(
        self, match, text: str
    ) -> Optional[ParsedIntent]:
        """パターン: DELETE WHERE ..."""
        try:
            where_clause = match.group(1).strip()
            target_condition = self._extract_condition(where_clause)

            if target_condition:
                return ParsedIntent(
                    operation_type="delete",
                    target_condition=target_condition,
                    update_values=None,
                    confidence=0.8,
                    explanation=f"Delete where {target_condition}",
                )
        except Exception:
            pass

        return None

    def _parse_list_pattern(self, match, text: str) -> Optional[ParsedIntent]:
        """パターン: LIST ..."""
        try:
            target = match.group(1).strip() if match.lastindex else ""
            target_condition = self._extract_condition(target) if target else None

            return ParsedIntent(
                operation_type="list",
                target_condition=target_condition,
                update_values=None,
                confidence=0.9,
                explanation="List records",
            )
        except Exception:
            pass

        return None

    def _extract_condition(self, text: str) -> Optional[str]:
        """テキストから条件を抽出"""
        if not text:
            return None

        # key=value 形式を探す
        match = re.search(r"(\w+)\s*=\s*(['\"]?)(.+?)\2", text)
        if match:
            key = match.group(1)
            value = match.group(3)
            return f"{key}={value}"

        # 自然言語の条件を解析
        # "status が pending" → "status=pending"
        match = re.search(r"(\w+)\s*(?:が|は|を)\s*(['\"]?)(.+?)\2", text, re.UNICODE)
        if match:
            key = match.group(1)
            value = match.group(3)
            return f"{key}={value}"

        return None

    def _extract_values(self, text: str) -> Optional[str]:
        """テキストから更新値を抽出"""
        if not text:
            return None

        # key=value 形式を探す
        matches = re.findall(r"(\w+)\s*=\s*(['\"]?)(.+?)\2(?:,|$)", text)
        if matches:
            values = ",".join([f"{m[0]}={m[2]}" for m in matches])
            return values

        # 自然言語の更新値を解析
        # "status を completed に" → "status=completed"
        match = re.search(
            r"(\w+)\s*(?:を|に)\s*(['\"]?)(.+?)\2(?:に|へ)?",
            text,
            re.UNICODE,
        )
        if match:
            key = match.group(1)
            value = match.group(3)
            return f"{key}={value}"

        return None

    def generate_operation_code(self, intent: ParsedIntent) -> str:
        """解析結果から Operation コードを生成"""
        if intent.operation_type == "update":
            filter_str = f'--filter "{intent.target_condition}"' if intent.target_condition else ""
            set_str = f'--set "{intent.update_values}"' if intent.update_values else ""
            return f"update {filter_str} {set_str}".strip()

        elif intent.operation_type == "delete":
            filter_str = f'--filter "{intent.target_condition}"' if intent.target_condition else ""
            return f"delete {filter_str}".strip()

        elif intent.operation_type == "list":
            return "list"

        return ""
