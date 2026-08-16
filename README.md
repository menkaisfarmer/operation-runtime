# Operation Runtime

人間の意図・業務単位を一級オブジェクト化した、汎用データ操作ランタイム。

## 核心思想

従来の UI では「1クリック = 1操作」を強制されるが、実際には人間は 1 つの判断をしている。

```
従来:
クリック → 編集 → 保存
クリック → 編集 → 保存  ← 1 つの意図を繰り返す

目標:
人間の意図 → Operation → 複数対象への一括実行
```

## アーキテクチャ

```
Human Intent
     ↓
Operation
     ↓
Target + Action
     ↓
Operation Graph / Plan
     ↓
Dependency / Conflict Analysis
     ↓
Scheduler
     ↓
Transaction
     ↓
Executor
     ↓
Adapter
     ↓
Excel / SQLite / API / UI / その他
```

## Phase 1 実装完了

✓ Operation, Target, Action, Plan, Result
✓ Planner, Executor
✓ Sequence, Parallel
✓ Dry Run
✓ Undo ログ

## Phase 2 実装完了

✓ Scheduler: 競合検出（Write-Write, Read-Write, Resource）
✓ Validator: 事前検証と警告
✓ トポロジカルソート（競合考慮）
✓ 並列実行可能性判定

## Phase 3 実装完了

✓ Transaction: ACID 準拠のトランザクション管理
✓ Compensating Actions: ロールバック用の補償操作
✓ Savepoints: トランザクション内のセーブポイント
✓ Undo/Rollback: 実行済み操作の完全なロールバック

## Phase 4 実装完了

✓ BaseAdapter: 抽象アダプター インターフェース
✓ MemoryAdapter: メモリ内データストア
✓ SQLiteAdapter: SQLite データベース
✓ ExcelAdapter: Excel ファイル（openpyxl）
✓ RestAdapter: REST API バックエンド

## Phase 5 実装完了

✓ CLI Interface: コマンドラインツール
  - list, update, delete, plan コマンド
  - フィルタリングと値の更新
  - メモリ/SQLite/Excel サポート
✓ Web UI: Flask ベースの Web インターフェース
  - リアルタイムデータ管理
  - 操作の視覚的フィードバック
  - 実行計画プレビュー
  - レスポンシブデザイン

## Phase 6 実装完了

✓ NaturalLanguageParser: 自然言語解析
  - 操作タイプ自動検出（update/delete/list）
  - 条件と値の抽出
  - 信頼度スコアリング
  - 日本語/英語対応
✓ OperationGenerator: Operation 自動生成
  - 解析結果から Operation を生成
  - 複数条件対応
  - 操作ごとのサジェッション生成
✓ ApprovalWorkflow: Human approval ワークフロー
  - 実行前確認機能
  - Dry-run プレビュー
  - 対話/非対話モード

## 開発進捗

- [x] Phase 1: コア実装
- [x] Phase 2: 依存関係・競合検出、Validator
- [x] Phase 3: Transaction, Rollback, Compensating Actions
- [x] Phase 4: Adapter (Memory, SQLite, Excel, REST API)
- [x] Phase 5: UI (CLI, Web)
- [x] Phase 6: AI/Natural Language

## テスト

```bash
python3 tests/test_basic.py      # Phase 1: 4 テスト
python3 tests/test_phase2.py     # Phase 2: 6 テスト
python3 tests/test_phase3.py     # Phase 3: 7 テスト
python3 tests/test_phase4.py     # Phase 4: 5 テスト
python3 tests/test_phase5.py     # Phase 5: 8 テスト
python3 tests/test_phase6.py     # Phase 6: 8 テスト
```

計 38/38 全テスト成功

## CLI 使用例

```bash
# メモリ内データを更新
python3 -m ui.cli memory --data '[{"id":1,"status":"pending"}]' update --set status=completed

# SQLite データベースを更新
python3 -m ui.cli sqlite data.db users update --filter 'status=pending' --set status=completed

# Excel ファイルを更新
python3 -m ui.cli excel data.xlsx Sheet1 update --set value=100 --dry-run
```

## Web UI

```bash
# Flask をインストール
pip install flask

# Web UI を起動
python3 -m ui.web
# http://127.0.0.1:5000 にアクセス
```

## Natural Language Processing

```python
from ai.approval import ApprovalWorkflow
from engine.runtime import OperationRuntime

runtime = OperationRuntime()
workflow = ApprovalWorkflow(runtime)

data = [
    {"id": 1, "status": "pending"},
    {"id": 2, "status": "pending"}
]

# 自然言語から Operation を生成・実行
operation, success = workflow.process_natural_language(
    "status=pending のレコードを status=completed に更新",
    data,
    interactive=True  # ユーザー確認を要求
)
```

### サポート対象の自然言語形式

```
# UPDATE
"UPDATE users SET status=completed WHERE status=pending"
"status が pending のレコードを status=completed に更新"
"pending のレコードを completed に変更"

# DELETE
"DELETE FROM users WHERE status=archived"
"status=archived のレコードを削除"

# LIST
"LIST all records"
"すべてのレコードを表示"
```

## Adapter 使用例

```python
from adapters.sqlite import SQLiteAdapter
from engine.runtime import OperationRuntime

# SQLite Adapter を使用
adapter = SQLiteAdapter("data.db", "users")
adapter.connect()

runtime = OperationRuntime(adapter)
result = runtime.execute_with_adapter(operation)

adapter.disconnect()
```

## クイックスタート

```python
from core.action import Update
from core.target import Where
from core.operation import SimpleOperation
from engine.runtime import OperationRuntime

runtime = OperationRuntime()

operation = SimpleOperation(
    target=Where({"status": "未訪問"}),
    actions=[Update({"status": "訪問予定"})],
)

result = runtime.execute(operation, data)
```

## テスト実行

```bash
python3 tests/test_basic.py
```
