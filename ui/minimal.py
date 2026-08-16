#!/usr/bin/env python3
"""
Minimal Operation Runtime UI
最小限で実用的な Web インターフェース
"""

from flask import Flask, render_template_string, request, jsonify
import json
from typing import List, Dict, Any

from core.action import Update, Delete
from core.target import Where, AllRecords
from core.operation import SimpleOperation
from engine.runtime import OperationRuntime
from adapters.memory import MemoryAdapter

app = Flask(__name__)
runtime = OperationRuntime()
data = []

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Operation Runtime</title>
    <style>
        body { font-family: Arial; max-width: 900px; margin: 40px auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .section { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        textarea, input, select { width: 100%; padding: 10px; margin: 10px 0; font-size: 14px; border: 1px solid #ddd; border-radius: 3px; }
        textarea { min-height: 100px; font-family: monospace; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 14px; }
        button:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; border-radius: 3px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .records { background: #f9f9f9; padding: 15px; border-radius: 3px; max-height: 300px; overflow-y: auto; }
        .record { background: white; padding: 10px; margin: 5px 0; border-left: 3px solid #007bff; }
        .stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 15px 0; }
        .stat { background: #f9f9f9; padding: 15px; text-align: center; border-radius: 3px; }
        .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <h1>🚀 Operation Runtime</h1>

    <div class="section">
        <h2>📊 Data</h2>
        <textarea id="data" placeholder='[{"id":1,"status":"pending"},{"id":2,"status":"pending"}]'></textarea>
        <button onclick="loadData()">Load Data</button>
        <div id="records" class="records"></div>
    </div>

    <div class="section">
        <h2>⚙️ Operation</h2>
        <select id="opType" onchange="updateInputs()">
            <option value="update">Update</option>
            <option value="delete">Delete</option>
        </select>
        <input type="text" id="filter" placeholder="Filter (e.g. status=pending)">
        <input type="text" id="set" placeholder="Set values (e.g. status=completed)">
        <button onclick="execute()">Execute</button>
        <button onclick="dryRun()">Dry Run</button>
    </div>

    <div class="section stats">
        <div class="stat">
            <div class="stat-value" id="totalRecords">0</div>
            <div>Total Records</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="successCount">0</div>
            <div>Successful</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="failureCount">0</div>
            <div>Failed</div>
        </div>
    </div>

    <div id="result"></div>

    <script>
        function loadData() {
            try {
                data = JSON.parse(document.getElementById('data').value);
                updateDisplay();
                showResult('Data loaded: ' + data.length + ' records', 'info');
            } catch(e) {
                showResult('Invalid JSON: ' + e.message, 'error');
            }
        }

        function updateDisplay() {
            document.getElementById('totalRecords').textContent = data.length;
            const html = data.map((r, i) =>
                '<div class="record">' + (i+1) + '. ' + JSON.stringify(r) + '</div>'
            ).join('');
            document.getElementById('records').innerHTML = html;
        }

        function updateInputs() {
            const type = document.getElementById('opType').value;
            const setInput = document.getElementById('set');
            if (type === 'delete') {
                setInput.style.display = 'none';
            } else {
                setInput.style.display = 'block';
            }
        }

        function execute() {
            if (data.length === 0) {
                showResult('Load data first', 'error');
                return;
            }

            fetch('/api/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    data: data,
                    type: document.getElementById('opType').value,
                    filter: document.getElementById('filter').value,
                    set: document.getElementById('set').value
                })
            })
            .then(r => r.json())
            .then(res => {
                if (res.success) {
                    data = res.data;
                    updateDisplay();
                    document.getElementById('successCount').textContent = res.success_count;
                    document.getElementById('failureCount').textContent = res.failure_count;
                    showResult('✓ Success: ' + res.success_count + ' affected', 'success');
                } else {
                    showResult('✗ Error: ' + res.error, 'error');
                }
            });
        }

        function dryRun() {
            if (data.length === 0) {
                showResult('Load data first', 'error');
                return;
            }

            fetch('/api/dryrun', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    data: data,
                    filter: document.getElementById('filter').value,
                    set: document.getElementById('set').value
                })
            })
            .then(r => r.json())
            .then(res => {
                showResult('Preview: Will affect ' + res.targets + ' record(s)', 'info');
            });
        }

        function showResult(msg, type) {
            const el = document.getElementById('result');
            el.className = 'result ' + type;
            el.innerHTML = msg;
        }

        window.addEventListener('load', () => {
            document.getElementById('data').value = JSON.stringify([
                {id: 1, status: 'pending', value: 100},
                {id: 2, status: 'pending', value: 200},
                {id: 3, status: 'active', value: 300}
            ], null, 2);
            loadData();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/api/execute', methods=['POST'])
def execute():
    global data
    try:
        payload = request.json
        data = payload.get('data', [])
        op_type = payload.get('type')
        filter_str = payload.get('filter', '')
        set_str = payload.get('set', '')

        adapter = MemoryAdapter(data)
        adapter.connect()
        rt = OperationRuntime(adapter)

        # Parse target
        target = AllRecords()
        if filter_str:
            conditions = {}
            for part in filter_str.split(','):
                if '=' in part:
                    k, v = part.split('=', 1)
                    conditions[k.strip()] = v.strip()
            if conditions:
                target = Where(conditions)

        # Execute operation
        if op_type == 'update':
            updates = {}
            for part in set_str.split(','):
                if '=' in part:
                    k, v = part.split('=', 1)
                    k = k.strip()
                    v = v.strip()
                    try:
                        v = int(v)
                    except:
                        try:
                            v = float(v)
                        except:
                            pass
                    updates[k] = v
            operation = SimpleOperation(target=target, actions=[Update(updates)])
        else:
            operation = SimpleOperation(target=target, actions=[Delete()])

        result = rt.execute(operation, data)
        return jsonify({
            'success': True,
            'data': data,
            'success_count': result.total_success,
            'failure_count': result.total_failure
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/dryrun', methods=['POST'])
def dry_run():
    try:
        payload = request.json
        data_local = payload.get('data', [])
        filter_str = payload.get('filter', '')

        target = AllRecords()
        if filter_str:
            conditions = {}
            for part in filter_str.split(','):
                if '=' in part:
                    k, v = part.split('=', 1)
                    conditions[k.strip()] = v.strip()
            if conditions:
                target = Where(conditions)

        if isinstance(target, Where):
            targets = target.filter(data_local)
        else:
            targets = data_local

        return jsonify({'targets': len(targets)})
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    print('\n' + '='*60)
    print('Operation Runtime - Minimal UI')
    print('='*60)
    print('Starting server: http://127.0.0.1:5000')
    print('Press Ctrl+C to stop')
    print('='*60 + '\n')
    app.run(debug=True, use_reloader=False)
