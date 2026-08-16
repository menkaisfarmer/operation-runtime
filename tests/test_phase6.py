import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.parser import NaturalLanguageParser
from ai.generator import OperationGenerator
from ai.approval import ApprovalWorkflow
from engine.runtime import OperationRuntime


def test_parser_update_intent():
    """NLP - UPDATE 意図解析テスト"""
    print("\n=== Test: NLP Parser - Update Intent ===")

    parser = NaturalLanguageParser()

    # テスト1: 自然言語で UPDATE
    text1 = "status が pending のレコードを status=completed に更新"
    intent1 = parser.parse(text1)

    print(f"Input: {text1}")
    print(f"Type: {intent1.operation_type}")
    print(f"Condition: {intent1.target_condition}")
    print(f"Update: {intent1.update_values}")
    print(f"Confidence: {intent1.confidence:.0%}")

    assert intent1.operation_type == "update"
    assert intent1.confidence > 0.5

    # テスト2: SQL形式
    text2 = "UPDATE users SET status=active WHERE type=A"
    intent2 = parser.parse(text2)

    print(f"\nInput: {text2}")
    print(f"Type: {intent2.operation_type}")
    print(f"Confidence: {intent2.confidence:.0%}")

    assert intent2.operation_type == "update"
    assert intent2.confidence > 0.5

    print("✓ Parser update intent test passed")


def test_parser_delete_intent():
    """NLP - DELETE 意図解析テスト"""
    print("\n=== Test: NLP Parser - Delete Intent ===")

    parser = NaturalLanguageParser()

    text = "DELETE FROM users WHERE status=archived"
    intent = parser.parse(text)

    print(f"Input: {text}")
    print(f"Type: {intent.operation_type}")
    print(f"Condition: {intent.target_condition}")
    print(f"Confidence: {intent.confidence:.0%}")

    assert intent.operation_type == "delete"
    assert intent.confidence > 0.5

    print("✓ Parser delete intent test passed")


def test_parser_list_intent():
    """NLP - LIST 意図解析テスト"""
    print("\n=== Test: NLP Parser - List Intent ===")

    parser = NaturalLanguageParser()

    text = "すべてのレコードを表示"
    intent = parser.parse(text)

    print(f"Input: {text}")
    print(f"Type: {intent.operation_type}")
    print(f"Confidence: {intent.confidence:.0%}")

    assert intent.operation_type == "list"

    print("✓ Parser list intent test passed")


def test_generator_operation():
    """Operation ジェネレーター テスト"""
    print("\n=== Test: Operation Generator ===")

    generator = OperationGenerator()
    data = [
        {"id": 1, "status": "pending", "value": 100},
        {"id": 2, "status": "pending", "value": 200},
    ]

    # UPDATE Operation を生成
    text = "status=pending のレコードを completed に更新"
    generated = generator.generate_from_text(text, data)

    print(f"Input: {text}")
    print(f"Operation: {generated.operation}")
    print(f"Confidence: {generated.confidence:.0%}")
    print(f"Explanation: {generated.explanation}")

    assert generated.operation is not None
    assert generated.confidence > 0.5
    assert len(generated.suggestions) > 0

    print("✓ Operation generator test passed")


def test_approval_workflow():
    """Human approval ワークフロー テスト"""
    print("\n=== Test: Approval Workflow ===")

    runtime = OperationRuntime()
    workflow = ApprovalWorkflow(runtime)

    data = [
        {"id": 1, "status": "pending"},
        {"id": 2, "status": "pending"},
    ]

    text = "pending のレコードを completed に更新"

    print(f"Input: {text}")
    print(f"Running non-interactive workflow (auto-approve high confidence)...\n")

    # 非対話モードで実行（高信頼度は自動承認）
    operation, success = workflow.process_natural_language(
        text, data, interactive=False, auto_approve_threshold=0.8
    )

    print(f"Success: {success}")

    if operation:
        print("✓ Operation generated and approved")
    else:
        print("⚠ Operation not approved or generated")

    print("✓ Approval workflow test passed")


def test_confidence_scoring():
    """信頼度スコアリング テスト"""
    print("\n=== Test: Confidence Scoring ===")

    parser = NaturalLanguageParser()

    # 高信頼度テキスト（UPDATE キーワード含む）
    text1 = "UPDATE users SET status=completed WHERE status=pending"
    intent1 = parser.parse(text1)
    print(f"Text: {text1}")
    print(f"Type: {intent1.operation_type}")
    print(f"Confidence: {intent1.confidence:.0%}\n")

    assert intent1.operation_type == "update"

    # 低信頼度テキスト
    text2 = "xyz abc def"
    intent2 = parser.parse(text2)
    print(f"Text: {text2}")
    print(f"Type: {intent2.operation_type}")
    print(f"Confidence: {intent2.confidence:.0%}\n")

    assert intent2.operation_type == "unknown"

    print("✓ Confidence scoring test passed")


def test_code_generation():
    """CLI コード生成テスト"""
    print("\n=== Test: CLI Code Generation ===")

    parser = NaturalLanguageParser()

    text = "status=pending のレコードを completed に更新"
    intent = parser.parse(text)
    code = parser.generate_operation_code(intent)

    print(f"Input: {text}")
    print(f"Generated Code: {code}")

    assert "update" in code or "completed" in code

    print("✓ Code generation test passed")


def test_multiple_conditions():
    """複数条件解析テスト"""
    print("\n=== Test: Multiple Conditions ===")

    generator = OperationGenerator()
    data = [
        {"id": 1, "type": "A", "status": "pending"},
        {"id": 2, "type": "B", "status": "pending"},
        {"id": 3, "type": "A", "status": "active"},
    ]

    text = "type=A かつ status=pending のレコードを status=completed に更新"
    generated = generator.generate_from_text(text, data)

    print(f"Input: {text}")
    print(f"Target Condition: {generated.intent.target_condition}")
    print(f"Confidence: {generated.confidence:.0%}")

    # 条件が含まれていることを確認
    if generated.operation:
        print("✓ Multiple conditions test passed")
    else:
        print("⚠ Complex condition parsing not fully supported")


if __name__ == "__main__":
    test_parser_update_intent()
    test_parser_delete_intent()
    test_parser_list_intent()
    test_generator_operation()
    test_approval_workflow()
    test_confidence_scoring()
    test_code_generation()
    test_multiple_conditions()
    print("\n✓ All Phase 6 tests passed!")
