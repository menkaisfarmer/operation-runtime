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

## 開発進捗

- [x] Phase 1: コア実装
- [x] Phase 2: 依存関係・競合検出、Validator
- [x] Phase 3: Transaction, Rollback, Compensating Actions
- [x] Phase 4: Adapter (Memory, SQLite, Excel, REST API)
- [ ] Phase 5: UI (CLI, Web)
- [ ] Phase 6: AI/Natural Language

## テスト

```bash
python3 tests/test_basic.py      # Phase 1: 4 テスト
python3 tests/test_phase2.py     # Phase 2: 6 テスト
python3 tests/test_phase3.py     # Phase 3: 7 テスト
python3 tests/test_phase4.py     # Phase 4: 5 テスト
```

計 24/24 全テスト成功

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
