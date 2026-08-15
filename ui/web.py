from flask import Flask, render_template_string, request, jsonify
from typing import Dict, Any, List
import json

from core.action import Update, Delete
from core.target import Where, AllRecords
from core.operation import SimpleOperation
from engine.runtime import OperationRuntime
from adapters.memory import MemoryAdapter

# HTML テンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Operation Runtime - Web UI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        header {
            background: #333;
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 { font-size: 2em; margin-bottom: 10px; }
        .subtitle { font-size: 0.9em; opacity: 0.8; }
        main {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 30px;
        }
        .section {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            background: #f9f9f9;
        }
        .section h2 {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #333;
        }
        label {
            display: block;
            margin-top: 15px;
            font-weight: bold;
            color: #555;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 0.95em;
        }
        textarea { min-height: 120px; font-family: monospace; }
        button {
            margin-top: 20px;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: background 0.3s;
        }
        button:hover { background: #764ba2; }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .records {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-top: 15px;
            background: white;
        }
        .record-item {
            background: #f0f0f0;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 3px;
            font-size: 0.9em;
            font-family: monospace;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            display: none;
        }
        .result.success {
            display: block;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .result.error {
            display: block;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .full-width {
            grid-column: 1 / -1;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        .stat {
            background: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border: 1px solid #ddd;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Operation Runtime</h1>
            <p class="subtitle">Batch data operations interface</p>
        </header>

        <main>
            <div class="section">
                <h2>📊 Data Management</h2>
                <label>Data (JSON)</label>
                <textarea id="dataInput" placeholder='[{"id":1,"status":"pending"}]'></textarea>
                <label>Records Count: <span id="recordCount">0</span></label>
                <div id="records" class="records"></div>
                <button onclick="loadData()">Load Data</button>
            </div>

            <div class="section">
                <h2>⚙️ Operation</h2>
                <label>Operation Type</label>
                <select id="operationType">
                    <option value="update">Update</option>
                    <option value="delete">Delete</option>
                </select>

                <label>Filter (optional, e.g., status=pending)</label>
                <input type="text" id="filterInput" placeholder="status=pending">

                <label>Set Values (e.g., status=completed)</label>
                <input type="text" id="setInput" placeholder="status=completed" id="setInput">

                <button onclick="executeOperation()">Execute</button>
                <button onclick="showPlan()">Show Plan</button>
            </div>

            <div class="section">
                <h2>📈 Statistics</h2>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value" id="successCount">0</div>
                        <div class="stat-label">Successful</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="failureCount">0</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="targetCount">0</div>
                        <div class="stat-label">Targets</div>
                    </div>
                </div>
            </div>

            <div class="section full-width">
                <h2>✅ Results</h2>
                <div id="result" class="result"></div>
            </div>
        </main>
    </div>

    <script>
        let data = [];
        let runtime = null;

        function loadData() {
            const input = document.getElementById('dataInput').value;
            try {
                data = JSON.parse(input);
                document.getElementById('recordCount').textContent = data.length;
                updateRecordsDisplay();
                document.getElementById('result').innerHTML = '';
            } catch (e) {
                showError('Invalid JSON: ' + e.message);
            }
        }

        function updateRecordsDisplay() {
            const container = document.getElementById('records');
            container.innerHTML = data.map((r, i) =>
                `<div class="record-item">${i+1}. ${JSON.stringify(r)}</div>`
            ).join('');
        }

        function executeOperation() {
            if (data.length === 0) {
                showError('Please load data first');
                return;
            }

            const type = document.getElementById('operationType').value;
            const filter = document.getElementById('filterInput').value;
            const setValues = document.getElementById('setInput').value;

            fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: data,
                    type: type,
                    filter: filter,
                    set: setValues
                })
            })
            .then(r => r.json())
            .then(result => {
                if (result.success) {
                    data = result.data;
                    updateRecordsDisplay();
                    showSuccess(`Operation completed: ${result.success_count} success, ${result.failure_count} failed`);
                    document.getElementById('successCount').textContent = result.success_count;
                    document.getElementById('failureCount').textContent = result.failure_count;
                } else {
                    showError(result.error);
                }
            })
            .catch(e => showError(e.message));
        }

        function showPlan() {
            if (data.length === 0) {
                showError('Please load data first');
                return;
            }

            const filter = document.getElementById('filterInput').value;
            const setValues = document.getElementById('setInput').value;

            fetch('/api/plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: data,
                    filter: filter,
                    set: setValues
                })
            })
            .then(r => r.json())
            .then(result => {
                document.getElementById('targetCount').textContent = result.target_count;
                showSuccess(
                    `Plan: ${result.target_count} targets, ` +
                    `${result.operations} operations, ` +
                    `${result.conflicts} conflicts`
                );
            })
            .catch(e => showError(e.message));
        }

        function showSuccess(msg) {
            const el = document.getElementById('result');
            el.className = 'result success';
            el.innerHTML = `<strong>✓ Success:</strong> ${msg}`;
        }

        function showError(msg) {
            const el = document.getElementById('result');
            el.className = 'result error';
            el.innerHTML = `<strong>✗ Error:</strong> ${msg}`;
        }

        // 初期データをロード
        window.addEventListener('load', () => {
            document.getElementById('dataInput').value = JSON.stringify([
                { id: 1, status: 'pending', value: 100 },
                { id: 2, status: 'pending', value: 200 },
                { id: 3, status: 'active', value: 300 }
            ], null, 2);
            loadData();
        });
    </script>
</body>
</html>
"""


class OperationWeb:
    """Operation Runtime の Web UI"""

    def __init__(self, debug=False):
        self.app = Flask(__name__)
        self.runtime = OperationRuntime()
        self.data: List[Dict[str, Any]] = []
        self.debug = debug

        self._setup_routes()

    def _setup_routes(self) -> None:
        """ルートを設定"""

        @self.app.route("/")
        def index():
            return render_template_string(HTML_TEMPLATE)

        @self.app.route("/api/execute", methods=["POST"])
        def execute():
            try:
                payload = request.json
                self.data = payload.get("data", [])
                operation_type = payload.get("type", "update")
                filter_str = payload.get("filter", "")
                set_str = payload.get("set", "")

                adapter = MemoryAdapter(self.data)
                adapter.connect()
                self.runtime = OperationRuntime(adapter)

                target = self._parse_filter(filter_str) if filter_str else AllRecords()

                if operation_type == "update":
                    if not set_str:
                        return jsonify({"success": False, "error": "Set values required"})
                    updates = self._parse_set(set_str)
                    operation = SimpleOperation(
                        target=target, actions=[Update(updates)]
                    )
                else:
                    operation = SimpleOperation(target=target, actions=[Delete()])

                result = self.runtime.execute(operation, self.data)

                return jsonify(
                    {
                        "success": True,
                        "data": self.data,
                        "success_count": result.total_success,
                        "failure_count": result.total_failure,
                    }
                )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})

        @self.app.route("/api/plan", methods=["POST"])
        def plan():
            try:
                payload = request.json
                self.data = payload.get("data", [])
                filter_str = payload.get("filter", "")
                set_str = payload.get("set", "")

                adapter = MemoryAdapter(self.data)
                adapter.connect()
                self.runtime = OperationRuntime(adapter)

                target = self._parse_filter(filter_str) if filter_str else AllRecords()
                updates = self._parse_set(set_str)
                operation = SimpleOperation(target=target, actions=[Update(updates)])

                plan_obj = self.runtime.plan(operation, self.data)
                summary = plan_obj.get_summary()

                return jsonify(
                    {
                        "target_count": summary["total_targets"],
                        "operations": summary["total_nodes"],
                        "conflicts": len(plan_obj.conflicts),
                    }
                )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})

    def _parse_filter(self, filter_str: str):
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

            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass

            updates[key] = value

        return updates

    def run(self, host="127.0.0.1", port=5000) -> None:
        """Web サーバーを起動"""
        print(f"\n{'='*60}")
        print(f"Operation Runtime Web UI")
        print(f"{'='*60}")
        print(f"Server running at http://{host}:{port}")
        print(f"Press Ctrl+C to stop")
        print(f"{'='*60}\n")

        self.app.run(host=host, port=port, debug=self.debug)


def main():
    """Web UI エントリーポイント"""
    web = OperationWeb(debug=True)
    web.run()


if __name__ == "__main__":
    main()
