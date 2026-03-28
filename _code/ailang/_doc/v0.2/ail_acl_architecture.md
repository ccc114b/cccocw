# AIL 與 ACL 系統架構說明

## 概述

AIL (AI Language) 與 ACL (AI Communication Language) 構成一個完整的 AI 程式開發框架。AIL 作為高層框架，讓人類以目標導向的方式指揮 AI 完成任務；ACL 作為通訊層，定義 AI 與系統之間的結構化溝通格式。

## 系統分層

```
┌─────────────────────────────────────────────────────────────┐
│                      人類開發者                              │
│              (描述任務目標，而非實作細節)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    AIL 框架層                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │   Goal      │  │   Agent     │  │   Memory        │     │
│  │   目標追蹤   │  │   代理程式   │  │   長期記憶       │     │
│  └─────────────┘  └─────────────┘  └─────────────────┘     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │   Explore   │  │   Think     │  │   Intent        │     │
│  │   探索執行   │  │   推理思考   │  │   意圖識別       │     │
│  └─────────────┘  └─────────────┘  └─────────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │ 任務指派
┌──────────────────────────▼──────────────────────────────────┐
│                 MiniCode 實作層                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  - 解析 ACL 指令                                       ││
│  │  - 執行 <write>, <shell>, <read>                      ││
│  │  - 檔案系統操作                                       ││
│  │  - 命令列執行                                         ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │ ACL 通訊格式
┌──────────────────────────▼──────────────────────────────────┐
│                    AI 模型層                                 │
│              (MiniMax M2.5 via Ollama)                      │
│                                                                 │
│   <write file="backend.py">...</write>                       │
│   <shell>ls</shell>                                           │
│   <read file="config.json"></read>                            │
└─────────────────────────────────────────────────────────────┘
```

## ACL - AI Communication Language

### 設計理念

傳統上，人類與 AI 的溝通使用自然語言，容易產生誤解：
- AI 可能輸出過多解釋而非執行指令
- AI 可能遺漏重要步驟
- 解析輸出困難，容易混入說明文字

ACL 採用結構化的 XML 格式，確保雙向溝通明確無誤。

### 指令格式

#### 1. 寫入檔案 `<write>`

```
<write file="路徑/檔名">
檔案內容...
</write>
```

範例：
```xml
<write file="backend.py">
from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)
DB_NAME = "todo.db"

# ... 完整程式碼
</write>
```

#### 2. 執行命令 `<shell>`

```
<shell>命令</shell>
```

範例：
```xml
<shell>mkdir -p templates</shell>
<shell>pip install flask</shell>
<shell>python3 main.py</shell>
```

#### 3. 讀取檔案 `<read>`

```
<read file="路徑/檔名"></read>
```

範例：
```xml
<read file="config.json"></read>
```

### 多重指令

AI 可以一次輸出多個指令：

```xml
<shell>mkdir -p templates</shell>
<write file="backend.py">
from flask import Flask
app = Flask(__name__)
</write>
<write file="templates/index.html">
<!DOCTYPE html>
<html>
<body>
    <h1>Hello</h1>
</body>
</html>
</write>
<shell>python3 backend.py</shell>
```

## AIL 框架模組

### Goal - 目標追蹤

```python
from ailang import goal, get_tracker

# 宣告目標
with goal("建立電子商務網站"):
    # 規劃階段
    plan_step("分析需求")
    
    # 執行階段
    result = await agent(task="建立商品列表頁面")
    plan_step(f"完成: {result[:100]}")
```

### Agent - 代理程式

```python
from ailang import Agent

# 建立代理
coder = Agent("coder", system_prompt="你擅長 Python 開發")

# 執行任務
result = await coder(task="建立 REST API")
```

### Memory - 長期記憶

```python
from ailang import Memory

memory = Memory()
memory.remember("使用者偏好淺色主題")
recalls = memory.recall("主題")
```

### Explore - 平行探索

```python
from ailang import explore

# 同時嘗試多種解法
results = await explore(
    task="優化查詢效能",
    strategies=["建立索引", "使用快取", "改寫 SQL"]
)
# 自動選擇最佳解
```

### Think - 推理思考

```python
from ailang import think

# 展示 AI 推理過程
async for chunk in think("如何解決這個演算法問題?"):
    print(chunk, end="")
```

## MiniCode 實作

MiniCode 是基於 AIL 框架的 CLI 工具，類似簡化版的 OpenCode。

### 使用方式

```bash
PYTHONPATH=src python3 minicode_ail.py
```

或在 Python 中使用：

```python
from minicode_ail import MiniCode, init_ollama

init_ollama(model='minimax-m2.5:cloud')
agent = MiniCode(root_dir='./project')

await agent.run("建立一個天氣查詢網站")
```

### 工作流程

1. **接收任務**：人類描述目標（如「建立 TODO 應用」）
2. **分析環境**：列出現有檔案結構
3. **AI 規劃**：AI 思考需要哪些檔案
4. **ACL 輸出**：AI 以結構化格式輸出指令
5. **執行指令**：MiniCode 解析並執行
6. **回饋結果**：顯示執行的檔案和命令

## 實際範例：建立 SQLite TODO 應用

### 任務描述

```
建立 SQLite TODO 應用：
1. backend.py - Flask 後端，首頁 /
2. templates/index.html - 前端
功能：新增、刪除、標記完成
```

### AI 輸出（ACL 格式）

```xml
<shell>mkdir -p templates</shell>
<write file="backend.py">
from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)
DB_NAME = "todo.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        completed INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/todos', methods=['GET'])
def get_todos():
    conn = sqlite3.connect(DB_NAME)
    todos = conn.execute('SELECT * FROM todos').fetchall()
    conn.close()
    return jsonify([dict(row) for row in todos])

@app.route('/api/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.execute('INSERT INTO todos (title) VALUES (?)', (data['title'],))
    conn.commit()
    conn.close()
    return jsonify({'id': cursor.lastrowid})

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json()
    conn = sqlite3.connect(DB_NAME)
    conn.execute('UPDATE todos SET completed = ? WHERE id = ?',
                 (data.get('completed', 0), todo_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
</write>
<write file="templates/index.html">
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>TODO 應用</title>
    <style>
        /* CSS 樣式 */
    </style>
</head>
<body>
    <h1>TODO 列表</h1>
    <input id="todoInput" placeholder="輸入新任務">
    <button onclick="addTodo()">新增</button>
    <ul id="todoList"></ul>
    <script>
        // JavaScript 邏輯
    </script>
</body>
</html>
</write>
```

### 執行結果

```
📝 寫入: backend.py
✓ 已寫入: backend.py

📝 寫入: templates/index.html
✓ 已寫入: templates/index.html

⚡ 執行: mkdir -p templates
```

## 優勢與價值

### 1. 目標導向而非程序導向

人類只需要描述「要什麼」，不需要寫詳細的程式碼：

```python
# AIL 風格
goal("建立部落格系統")
await agent(task="包含文章列表、發表、評論功能")

# 傳統風格
# 需要自己寫 Flask routes, models, templates...
```

### 2. 結構化溝通

ACL 消除歧義，確保 AI 輸出可解析、可執行。

### 3. 可追蹤性

AIL 的 Goal 追蹤讓開發者清楚任務進度。

### 4. 可擴展性

新增功能只需擴展 ACL 指令集或 AIL 模組。

## 未來發展方向

1. **更多 ACL 指令**：加入 `<ask>`, `<confirm>`, `<search>` 等
2. **Agent 協作**：多個 Agent 分工合作
3. **自我修復**：AI 根據錯誤自動修正程式碼
4. **測試整合**：自動執行測試驗證功能
5. **部署功能**：一鍵部署到雲端

## 結論

AIL 和 ACL 的設計理念是讓人類與 AI 的協作更加自然：

- **AIL** 讓人類以目標導向思考
- **ACL** 讓 AI 以結構化方式執行
- **MiniCode** 是這一理念的具體實現

這類似從「組合語言」進化到「高階語言」的過程，讓程式開發更加高效、直覺。
