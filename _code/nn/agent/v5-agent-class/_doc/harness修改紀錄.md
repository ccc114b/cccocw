# Harness Engineering 架構修改紀錄

## 檔案結構

```
├── agents.py    # 所有 Agent 類別
└── main.py       # 入口點
```

## Agent 類別架構

### Agent (基類)

所有 Agent 的父類，提供通用介面：

| 屬性/方法 | 說明 |
|-----------|------|
| `name` | Agent 名稱 |
| `system` | 系統提示詞 |
| `memory: str` | 長期記憶 |
| `messages: list[str]` | 對話歷史 |
| `max_turns: int` | 最大歷史回合數（預設 5） |
| `read(msg)` | 讀取訊息 |
| `write(content)` | 寫出訊息 |
| `get_context()` | 取得完整上下文（含 memory + history） |
| `record(user_msg, assistant_msg)` | 記錄對話到 messages |
| `think(context)` | 呼叫 LLM（自動包含 memory） |
| `remember(user_msg, assistant_msg)` | 從對話提取長期記憶 |

### Planner

負責規劃任務步驟，可讀取磁碟資訊但不寫程式。

| 屬性/方法 | 說明 |
|-----------|------|
| `guard` | Guard 實例（共享） |
| `execute(cmd, cwd)` | 執行 shell 命令（僅限讀取） |
| `plan(user_input)` | 規劃任務 |

### Executor

負責執行 shell 命令，包括寫入檔案等操作。

| 屬性/方法 | 說明 |
|-----------|------|
| `guard` | Guard 實例（共享） |
| `execute(cmd, cwd)` | 執行 shell 命令 |

### Evaluator

負責驗證執行結果，可執行 shell 命令進行測試。

| 屬性/方法 | 說明 |
|-----------|------|
| `guard` | Guard 實例（共享） |
| `execute(cmd, cwd)` | 執行 shell 命令（用於驗證） |
| `evaluate(task, result)` | 評估任務完成度 |

### UserAgent

協調者，支援 Plan/Exec/Eval 三種模式。

| 屬性/方法 | 說明 |
|-----------|------|
| `mode` | 當前模式 |
| `planner` | Planner 實例 |
| `executor` | Executor 實例 |
| `evaluator` | Evaluator 實例 |
| `chat(user_input)` | 依據模式處理輸入 |

## 操作模式

| 指令 | 模式 | 說明 |
|------|------|------|
| `/plan` | Plan Mode | 切換至 Planner，可讀取資訊、規劃步驟 |
| `/exec` | Exec Mode | 切換至 Executor，執行 shell 命令 |
| `/eval` | Eval Mode | 切換至 Evaluator，驗證結果 |
| `/memory` | - | 顯示長期記憶 |
| `/quit` | - | 結束 |

### 預設模式

系統啟動時預設為 **Plan Mode**。

### 工作流程

```
User: 需求
  ↓ (Plan Mode)
Planner: 分析需求、讀取相關資訊、規劃步驟
  ↓
User: /exec
  ↓ (Exec Mode)
Executor: 執行規劃的步驟
  ↓
User: /eval
  ↓ (Eval Mode)
Evaluator: 驗證執行結果是否正確
  ↓
User: /plan
  ↓ (Plan Mode)
Planner: 根據驗證結果規劃下一輪
```

## Guard 類別

安全審查者，控管所有 shell 命令的執行。

| 屬性/方法 | 說明 |
|-----------|------|
| `allowed_paths: set` | 已授權存取的外部路徑 |
| `review_command(cmd)` | 呼叫 LLM 判斷命令是否安全 |
| `check_and_execute(cmd, cwd)` | 檢查並執行命令 |
| `ask_outside_access(path)` | 詢問用戶是否授權外部路徑 |

## check_outside_access 函式

檢查命令是否存取工作目錄外的檔案。

```python
check_outside_access(cmd: str, cwd: str) -> tuple[bool, str]
# 回傳 (是否需要授權, 路徑)
```

## 使用範例

```python
from agents import UserAgent

agent = UserAgent()
agent.run()
```

互動範例：

```
你：幫我建立一個 hello.py
🤖 [PLAN] 好的，我先了解一下專案結構...
你：/exec
>>> 切換至 Exec Mode
你：建立一個 hello.py
🤖 [EXEC] 已建立 hello.py
你：/eval
>>> 切換至 Eval Mode
你：執行測試
🤖 [EVAL] 測試通過
你：/plan
>>> 切換至 Plan Mode
```
