from typing import Optional, Tuple
from enum import Enum
import sys

from core.operation import SimpleOperation
from engine.runtime import OperationRuntime
from .generator import GeneratedOperation


class ApprovalStatus(Enum):
    """承認ステータス"""

    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ApprovalRequest:
    """ユーザー承認リクエスト"""

    def __init__(
        self,
        generated_op: GeneratedOperation,
        runtime: OperationRuntime,
        data,
    ):
        self.generated_op = generated_op
        self.runtime = runtime
        self.data = data
        self.approved = False
        self.approval_status = None

    def request_approval(self, interactive: bool = True) -> bool:
        """ユーザーに承認をリクエスト"""
        self._display_operation()
        self._display_suggestions()

        if interactive:
            return self._get_user_approval()
        else:
            # 信頼度が高い場合は自動承認
            return self.generated_op.confidence >= 0.85

    def _display_operation(self) -> None:
        """操作内容を表示"""
        print(f"\n{'='*60}")
        print("PROPOSED OPERATION")
        print(f"{'='*60}")

        intent = self.generated_op.intent
        print(f"Type: {intent.operation_type.upper()}")
        print(f"Confidence: {self.generated_op.confidence:.0%}")
        print(f"Explanation: {self.generated_op.explanation}")

        if intent.target_condition:
            print(f"Target: {intent.target_condition}")

        if intent.update_values:
            print(f"Update: {intent.update_values}")

        # Dry run を実行して影響を表示
        if self.generated_op.operation and self.data:
            try:
                plan = self.runtime.plan(
                    self.generated_op.operation, self.data
                )
                summary = plan.get_summary()
                print(
                    f"\nImpact: {summary['total_targets']} record(s) "
                    f"from {len(self.data)} total"
                )
            except Exception as e:
                print(f"Error calculating impact: {e}")

        print(f"{'='*60}\n")

    def _display_suggestions(self) -> None:
        """サジェッションを表示"""
        if self.generated_op.suggestions:
            print("ℹ️  Suggestions:")
            for i, suggestion in enumerate(self.generated_op.suggestions, 1):
                print(f"   {i}. {suggestion}")
            print()

    def _get_user_approval(self) -> bool:
        """ユーザーから承認を取得"""
        while True:
            prompt = "\nApprove this operation? (yes/no/dry-run/cancel): "
            response = input(prompt).strip().lower()

            if response in ["yes", "y"]:
                self.approval_status = ApprovalStatus.APPROVED
                return True

            elif response in ["no", "n"]:
                self.approval_status = ApprovalStatus.REJECTED
                print("Operation cancelled")
                return False

            elif response == "dry-run":
                self._execute_dry_run()
                # Dry run 後も承認を求める
                continue

            elif response == "cancel":
                self.approval_status = ApprovalStatus.REJECTED
                print("Operation cancelled")
                return False

            else:
                print("Invalid response. Please enter: yes, no, dry-run, or cancel")

    def _execute_dry_run(self) -> None:
        """Dry run を実行して結果を表示"""
        if not self.generated_op.operation or not self.data:
            print("Cannot execute dry-run")
            return

        try:
            print("\nExecuting DRY-RUN...\n")
            plan = self.runtime.plan(
                self.generated_op.operation, self.data
            )

            print(f"Targets: {plan.get_total_target_count()}")
            print(f"Operations: {len(plan.nodes)}")

            if plan.conflicts:
                print(f"Conflicts: {len(plan.conflicts)}")
                for conflict in plan.conflicts:
                    print(f"  - {conflict}")

            print("\nDry-run completed (no changes made)")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"Error executing dry-run: {e}")


class ApprovalWorkflow:
    """Human approval ワークフロー"""

    def __init__(self, runtime: OperationRuntime):
        self.runtime = runtime

    def process_natural_language(
        self,
        text: str,
        data,
        interactive: bool = True,
        auto_approve_threshold: float = 0.85,
    ) -> Tuple[Optional[object], bool]:
        """自然言語を処理して Operation を実行"""
        from .generator import OperationGenerator

        # Operation を生成
        generator = OperationGenerator()
        generated_op = generator.generate_from_text(text, data)

        print(f"\n{'='*60}")
        print("NATURAL LANGUAGE PROCESSING")
        print(f"{'='*60}")
        print(f"Input: {text}")
        print(f"Intent: {generated_op.intent.operation_type}")
        print(f"Confidence: {generated_op.confidence:.0%}")
        print(f"{'='*60}\n")

        # 信頼度が低い場合は警告
        if generated_op.confidence < 0.6:
            print("⚠️  Low confidence in operation interpretation")
            print("   Please review carefully\n")

        # 操作がない場合
        if generated_op.operation is None:
            if generated_op.intent.operation_type == "list":
                print("List operation - executing without approval\n")
                return None, True
            else:
                print("✗ Could not generate operation")
                print("Suggestions:")
                for suggestion in generated_op.suggestions:
                    print(f"  - {suggestion}")
                return None, False

        # 承認をリクエスト
        approval_request = ApprovalRequest(
            generated_op, self.runtime, data
        )

        if approval_request.request_approval(interactive):
            return generated_op.operation, True
        else:
            return None, False
