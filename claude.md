# Operation Runtime — CLAUDE.md

## 1. プロジェクト目的

「1クリック＝1操作」という従来のGUI制約を減らし、人間の**意図・業務単位**を1つの操作として扱う汎用データ操作ランタイムをPythonで構築する。

対象はExcel、SQLite、REST API、業務システム、注文UIなど、データ操作を伴うアプリ全般。

核心思想：

> データを直接操作するのではなく、「操作」を一級オブジェクトとして扱う。

## 2. 解決したい問題

従来のUIでは、人間が実際には1つの判断をしているにもかかわらず、

```text
クリック → 編集 → 保存
クリック → 編集 → 保存
クリック → 編集 → 保存
```

のように対象を1件ずつ操作する必要がある。

DXでは単なる紙→Excelへの置換ではなく、**操作単位そのものをデジタル化する**。

目標：

```text
人間の意図
  ↓
業務操作
  ↓
対象集合
  ↓
複数データへの操作
```

## 3. 基本原則

1. 「1レコード1操作」を疑う。
2. データ単位ではなく、人間の意図・業務単位を操作単位にする。
3. 対象（Target）と操作（Action）を分離する。
4. 複数対象を集合として扱う。
5. 操作を実行前に計画（Plan）として解析する。
6. 依存関係・競合・排他をRuntime側で管理する。
7. UIと実行ロジックを分離する。
8. Backend固有の処理はAdapterに閉じ込める。
9. Dry Runを基本とする。
10. 一括操作にはUndo/Rollbackを用意する。
11. 可能な処理は並列実行し、依存する処理は順序付ける。
12. 人間にはデータではなく「結果」と「例外」を見せる。

## 4. 全体アーキテクチャ

```text
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

## 5. コア概念

### Operation

「何をしたいか」を表す一級オブジェクト。

例：

```python
Operation(
    target=customers.where(status="未訪問"),
    action=Update(next_visit=AddDays(30)),
)
```

### Target

操作対象を表す。

単一レコードではなく、条件による**対象集合**を基本とする。

```python
customers.where(
    city="柏崎市",
    status="未訪問",
)
```

### Action

対象に対して行う操作。

例：

```text
Create
Update
Delete
Move
Copy
Transform
Notify
```

### Plan

Operationを実行可能な計画へ変換したもの。

Planには少なくとも以下を含める。

* 対象件数
* 変更内容
* 依存関係
* 必要リソース
* 競合
* 実行順序
* 並列実行可能性
* Rollback情報

### Result

実行結果を表す。

* 成功件数
* 失敗件数
* 変更内容
* エラー
* Undoに必要な情報

## 6. Operationの合成

複数のActionを1つのOperationとして扱えるようにする。

```python
Sequence(
    Update(next_visit=AddDays(30)),
    Update(status="訪問予定"),
    Notify(),
)
```

操作をグラフとして表現し、依存関係を解析する。

```text
A → B → C
```

依存しない処理は並列化する。

```text
A ──→ X
B ──→ Y
```

## 7. Scheduler

Schedulerは以下を担当する。

* 操作順序決定
* 依存関係解決
* 並列実行可能性判定
* リソース競合検出
* 排他制御
* デッドロック回避
* Retry判断

特にロック順序を統一し、循環待ちを防止する。

```text
Resource ordering:
X < Y

Operation A: X → Y
Operation B: X → Y
```

必要に応じて、

* timeout
* deadlock detection
* retry
* optimistic concurrency
* idempotency

を導入する。

## 8. Transaction

一括操作は可能な限りトランザクションとして扱う。

```text
Plan
 ↓
Validate
 ↓
Execute
 ↓
Commit
```

失敗時：

```text
Execute
 ↓
Failure
 ↓
Rollback
```

Backendによって完全Rollbackできない場合は、補償操作（Compensating Action）を使用する。

## 9. Dry Run

破壊的操作は原則として実行前にPlanを生成する。

例：

```text
対象: 87件

変更:
next_visit
  2026-08-15 → 2026-09-14

status
  未訪問 → 訪問予定

通知: 87件

[実行] [キャンセル]
```

ユーザーは87件を個別確認するのではなく、**操作全体を確認**する。

## 10. Undo

一括操作には可能な限りUndoを提供する。

```python
result = runtime.execute(plan)
runtime.undo(result)
```

Undoに必要な変更前状態をResultまたはTransaction Logに保持する。

## 11. Adapter

Runtimeは特定Backendを直接知らない。

```text
Operation Runtime
 ├── Excel Adapter
 ├── SQLite Adapter
 ├── REST Adapter
 └── その他Adapter
```

同一Operationを異なるBackendで実行可能にする。

```python
runtime.execute(operation, backend=excel)
runtime.execute(operation, backend=sqlite)
```

Adapterは以下を担当する。

* Backendとの接続
* Target解決
* Action実行
* Transaction連携
* Backend固有エラーの変換

## 12. UI設計思想

UIはRuntimeの実行主体ではなく、**意図をOperationへ変換する入力層**とする。

操作方法を1つに限定しない。

```text
Button
Keyboard
Drag & Drop
Direct Input
Condition
Voice
Natural Language
AI
```

同じOperationを複数の入力方法から生成できるようにする。

## 13. 一括操作

単純な「複数選択→一括変更」だけでなく、条件によるTarget指定を優先する。

悪い例：

```text
☑ A
☑ B
☑ C
☑ D
[一括変更]
```

望ましい例：

```text
対象:
市町村 = 柏崎市
状態 = 未訪問

操作:
訪問日 += 30日
状態 = 訪問予定

[実行]
```

「対象を選択する作業」そのものも減らす。

## 14. 人間とRuntimeの役割分担

人間：

```text
目的・意図・判断
```

Runtime：

```text
対象特定
操作分解
依存関係解析
競合検出
実行順序決定
並列化
トランザクション
実行
結果集約
```

原則：

> 人間は目的と例外を扱い、Runtimeは大量の機械的操作を扱う。

## 15. Pythonプロトタイプ

最初はBackendを実装せず、Pythonメモリ上のデータだけで検証する。

```python
data = [
    {"name": "A", "value": 100},
    {"name": "B", "value": 200},
    {"name": "C", "value": 300},
]
```

例：

```python
operation = Operation(
    target=Where(value__gte=100),
    action=Add("value", 50),
)

plan = runtime.plan(operation)
result = runtime.execute(plan)
```

期待結果：

```text
A 150
B 250
C 350
```

## 16. 推奨ディレクトリ

```text
operation_runtime/
├── core/
│   ├── operation.py
│   ├── target.py
│   ├── action.py
│   ├── plan.py
│   └── result.py
├── engine/
│   ├── planner.py
│   ├── scheduler.py
│   ├── executor.py
│   └── transaction.py
├── adapters/
│   ├── memory.py
│   ├── excel.py
│   ├── sqlite.py
│   └── api.py
└── tests/
```

## 17. 開発順序

### Phase 1

Memory Backendで以下を実装する。

```text
Operation
Target
Action
Plan
Executor
Result
```

### Phase 2

以下を追加する。

```text
Sequence
Dependency Graph
Scheduler
Dry Run
Validation
```

### Phase 3

```text
Transaction
Rollback
Undo
Conflict Detection
Deadlock Prevention
```

### Phase 4

Adapterを追加する。

```text
SQLite
Excel
REST API
```

### Phase 5

UIを追加する。

```text
CLI
Web UI
GUI
```

### Phase 6

AI/Natural LanguageからOperationを生成できるようにする。

```text
User Intent
 ↓
AI
 ↓
Operation
 ↓
Plan
 ↓
Human Approval
 ↓
Execute
```

## 18. 将来的なDSL

OperationをJSON/YAMLなどで表現できるようにする。

```yaml
target:
  type: customer
  where:
    city: 柏崎市
    status: 未訪問

actions:
  - update:
      next_visit: "+30d"
  - update:
      status: 訪問予定
```

これにより、UI・CLI・AI・外部システムから同じOperation Runtimeを利用できる。

## 19. 店舗注文への応用

商品単位の操作ではなく、注文意図をOperationとして扱う。

```text
「4人分の夕食」
      ↓
Operation
      ↓
ラーメン ×4
餃子 ×2
チャーハン ×1
      ↓
確認
      ↓
注文
```

「＋」を何十回も押させるUIを避ける。

## 20. Excel/DXへの応用

Excelを単なるセル入力画面として扱わず、業務操作のBackendとして扱う。

```text
「今月訪問対象者を更新」
      ↓
Target生成
      ↓
87件を取得
      ↓
Operation Plan
      ↓
一括更新
      ↓
例外3件だけ人間が確認
```

## 21. 設計上の最重要原則

このプロジェクトの目的は「便利な一括操作ボタン」を作ることではない。

**操作そのものをデータモデル化すること**である。

```text
従来:
User → UI → 1件 → DB

Operation Runtime:
User
 ↓
Intent
 ↓
Operation
 ↓
Target Set
 ↓
Action Graph
 ↓
Execution Plan
 ↓
Scheduler / Transaction
 ↓
Backend
```

最終的な目標は、

> **「1クリック＝1操作」から「1意図＝1操作」へ**

コンピューターとの対話モデルを変えることである。
