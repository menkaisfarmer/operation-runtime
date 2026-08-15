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

## 開発進捗

- [x] Phase 1: コア実装
- [ ] Phase 2: 依存関係・競合検出、複雑な Scheduler
- [ ] Phase 3: Transaction, Rollback
- [ ] Phase 4: Adapter (SQLite, Excel, REST API)
- [ ] Phase 5: UI (CLI, Web)
- [ ] Phase 6: AI/Natural Language

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
