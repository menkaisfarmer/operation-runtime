import sys
import json
from typing import List, Dict, Any, Optional
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from core.action import Update, Delete, Create
from core.target import Where, AllRecords
from core.operation import SimpleOperation, Sequence
from engine.runtime import OperationRuntime
from adapters.memory import MemoryAdapter
from adapters.sqlite import SQLiteAdapter
from adapters.excel import ExcelAdapter


class OperationCLI:
    """Operation Runtime の CLI インターフェース"""

    def __init__(self):
        self.runtime: Optional[OperationRuntime] = None
        self.adapter = None
        self.data: List[Dict[str, Any]] = []

    def parse_args(self, args: List[str]) -> None:
        """コマンドラインを解析"""
        parser = ArgumentParser(
            description="Operation Runtime - Batch data operations",
            formatter_class=RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s memory --data '[{"id":1,"status":"pending"}]' update --set status=completed
  %(prog)s sqlite data.db users update --filter 'status=pending' --set status=completed
  %(prog)s excel data.xlsx Sheet1 update --filter 'type=A' --set value=100
            """,
        )

        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # memory コマンド
        memory_parser = subparsers.add_parser(
            "memory", help="In-memory data store"
        )
        memory_parser.add_argument(
            "--data",
            type=str,
            required=True,
            help="JSON data",
        )
        self._add_operation_subparsers(memory_parser)

        # sqlite コマンド
        sqlite_parser = subparsers.add_parser("sqlite", help="SQLite database")
        sqlite_parser.add_argument("db_path", help="Database file path")
        sqlite_parser.add_argument("table_name", help="Table name")
        self._add_operation_subparsers(sqlite_parser)

        # excel コマンド
        excel_parser = subparsers.add_parser("excel", help="Excel file")
        excel_parser.add_argument("file_path", help="Excel file path")
        excel_parser.add_argument(
            "sheet_name", nargs="?", default="Sheet1", help="Sheet name"
        )
        self._add_operation_subparsers(excel_parser)

        # help コマンド
        subparsers.add_parser("help", help="Show help")

        parsed = parser.parse_args(args)

        if parsed.command == "help" or not parsed.command:
            parser.print_help()
            sys.exit(0)

        self.execute_command(parsed)

    def _add_operation_subparsers(self, parent_parser) -> None:
        """操作サブコマンドを追加"""
        ops = parent_parser.add_subparsers(dest="operation")

        # update コマンド
        update_cmd = ops.add_parser("update", help="Update records")
        update_cmd.add_argument(
            "--filter",
            type=str,
            help="Filter condition (e.g., status=pending)",
        )
        update_cmd.add_argument(
            "--set",
            type=str,
            required=True,
            help="Update values (e.g., status=completed)",
        )
        update_cmd.add_argument("--dry-run", action="store_true")

        # delete コマンド
        delete_cmd = ops.add_parser("delete", help="Delete records")
        delete_cmd.add_argument(
            "--filter",
            type=str,
            required=True,
            help="Filter condition",
        )
        delete_cmd.add_argument("--dry-run", action="store_true")

        # list コマンド
        ops.add_parser("list", help="List records")

        # plan コマンド
        plan_cmd = ops.add_parser("plan", help="Show execution plan")
        plan_cmd.add_argument(
            "--filter",
            type=str,
            help="Filter condition",
        )
        plan_cmd.add_argument(
            "--set",
            type=str,
            help="Update values",
        )

    def execute_command(self, args) -> None:
        """コマンドを実行"""
        if args.command == "memory":
            self._init_memory(args)
        elif args.command == "sqlite":
            self._init_sqlite(args)
        elif args.command == "excel":
            self._init_excel(args)

        if hasattr(args, "operation"):
            self._execute_operation(args)

    def _init_memory(self, args) -> None:
        """Memory Adapter を初期化"""
        self.data = json.loads(args.data)
        self.adapter = MemoryAdapter(self.data)
        self.adapter.connect()
        self.runtime = OperationRuntime(self.adapter)

    def _init_sqlite(self, args) -> None:
        """SQLite Adapter を初期化"""
        self.adapter = SQLiteAdapter(args.db_path, args.table_name)
        self.adapter.connect()
        self.runtime = OperationRuntime(self.adapter)
        self.data = self.adapter.read()

    def _init_excel(self, args) -> None:
        """Excel Adapter を初期化"""
        self.adapter = ExcelAdapter(args.file_path, args.sheet_name)
        self.adapter.connect()
        self.runtime = OperationRuntime(self.adapter)
        self.data = self.adapter.read()

    def _execute_operation(self, args) -> None:
        """操作を実行"""
        if args.operation == "list":
            self._list_records()
        elif args.operation == "update":
            self._update_records(args)
        elif args.operation == "delete":
            self._delete_records(args)
        elif args.operation == "plan":
            self._show_plan(args)

    def _list_records(self) -> None:
        """レコードを表示"""
        print(f"\nTotal records: {len(self.data)}")
        print(json.dumps(self.data, indent=2, ensure_ascii=False))

    def _update_records(self, args) -> None:
        """レコードを更新"""
        # ターゲットを解析
        target = self._parse_filter(args.filter) if args.filter else AllRecords()

        # 更新値を解析
        updates = self._parse_set(args.set)

        # Operation を作成
        operation = SimpleOperation(
            target=target,
            actions=[Update(updates)],
        )

        # 実行
        if args.dry_run:
            plan = self.runtime.plan(operation, self.data)
            self._print_plan(plan)
        else:
            result = self.runtime.execute(
                operation, self.data, dry_run=False, use_transaction=True
            )
            self._print_result(result)

    def _delete_records(self, args) -> None:
        """レコードを削除"""
        target = self._parse_filter(args.filter)
        operation = SimpleOperation(target=target, actions=[Delete()])

        if args.dry_run:
            plan = self.runtime.plan(operation, self.data)
            self._print_plan(plan)
        else:
            result = self.runtime.execute(
                operation, self.data, dry_run=False, use_transaction=True
            )
            self._print_result(result)

    def _show_plan(self, args) -> None:
        """実行計画を表示"""
        if args.set:
            target = self._parse_filter(args.filter) if args.filter else AllRecords()
            updates = self._parse_set(args.set)
            operation = SimpleOperation(
                target=target,
                actions=[Update(updates)],
            )
        else:
            print("Error: --set is required for plan")
            return

        plan = self.runtime.plan(operation, self.data)
        self._print_plan(plan)

    def _parse_filter(self, filter_str: str) -> Optional[Where]:
        """フィルター文字列を解析"""
        if not filter_str:
            return None

        conditions = {}
        for condition in filter_str.split(","):
            key, value = condition.split("=")
            conditions[key.strip()] = value.strip()

        return Where(conditions)

    def _parse_set(self, set_str: str) -> Dict[str, Any]:
        """SET 文字列を解析"""
        updates = {}
        for item in set_str.split(","):
            key, value = item.split("=")
            key = key.strip()
            value = value.strip()

            # 数値に変換を試みる
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass  # 文字列のまま

            updates[key] = value

        return updates

    def _print_plan(self, plan) -> None:
        """計画を表示"""
        summary = plan.get_summary()
        print(f"\n{'='*60}")
        print(f"EXECUTION PLAN")
        print(f"{'='*60}")
        print(f"Target records: {summary['total_targets']}")
        print(f"Operations: {summary['total_nodes']}")
        if plan.conflicts:
            print(f"Conflicts detected: {len(plan.conflicts)}")
            for conflict in plan.conflicts:
                print(f"  - {conflict}")
        print(f"{'='*60}\n")

    def _print_result(self, result) -> None:
        """結果を表示"""
        print(f"\n{'='*60}")
        print(f"EXECUTION RESULT")
        print(f"{'='*60}")
        print(f"Success: {result.total_success}")
        print(f"Failed: {result.total_failure}")

        if result.transaction_log:
            print(f"Transaction: {result.transaction_log.state.value}")

        print(f"{'='*60}\n")

        if result.total_success > 0:
            print("✓ Operation completed successfully")
        else:
            print("✗ Operation failed")


def main():
    """CLI エントリーポイント"""
    cli = OperationCLI()
    cli.parse_args(sys.argv[1:])


if __name__ == "__main__":
    main()
