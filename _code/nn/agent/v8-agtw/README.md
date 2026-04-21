# agtw - Agent Team Work

一個類似 Git/Docker CLI 的多智能體協調系統。

## 功能特色

- **Session 管理** - 建立、切換、刪除工作階段
- **多元代理** - Planner（規劃）、Executor（執行）、Evaluator（評估）
- **安全審查** - Shell 命令由 Guard 代理審查後才執行
- **TCP 伺服器** - 持久化服務 daemon
- **CLI 界面** - Git 風格的命令列工具

## 安裝

```bash
pip install agtw
```

或開發模式：

```bash
git clone https://github.com/your-repo/v8-agtw.git
cd v8-agtw
pip install -e ".[dev]"
```

## 快速開始

### 1. 啟動伺服器

```bash
agtw server
```

### 2. 建立 Session

```bash
agtw session new myproject
```

### 3. 列出 Sessions

```bash
agtw session list
```

### 4. 切換 Session

```bash
agtw session switch <session-id>
```

### 5. 建立 Executor

```bash
agtw agent exec "寫一個 hello.py"
```

### 6. 建立 Evaluator

```bash
agtw agent eval "檢查程式品質"

## 指令列表

| 指令 | 說明 |
|------|------|
| `agtw server` | 啟動 agtw 伺服器 |
| `agtw session new [name]` | 建立新 session |
| `agtw session list` | 列出所有 sessions |
| `agtw session switch <id>` | 切換至指定 session |
| `agtw session delete <id>` | 刪除 session |
| `agtw agent list` | 列出目前 session 的代理 |
| `agtw agent exec <task>` | 建立並執行 executor |
| `agtw agent eval <desc>` | 建立 evaluator |
| `agtw planner <prompt>` | 執行 planner |
| `agtw status` | 顯示伺服器狀態 |

## 系統架構

```
┌─────────────────────────────────────────────────┐
│                   agtw CLI                      │
│              (git-style commands)                │
└─────────────────┬───────────────────────────────┘
                  │ TCP (JSON)
┌─────────────────▼───────────────────────────────┐
│               agtw Server                       │
│  ┌─────────────────────────────────────────┐   │
│  │           SessionManager               │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │ Session │ │ Session │ │ Session │  │   │
│  │  │  ┌────┐ │ │  ┌────┐ │ │  ┌────┐ │  │   │
│  │  │  │Planner│ │  │Planner│ │  │Planner│ │  │   │
│  │  │  └────┘ │ │  └────┘ │ │  └────┘ │  │   │
│  │  │  ┌────┐ │ │  ┌────┐ │ │  ┌────┐ │  │   │
│  │  │  │Exec │ │ │  │Exec │ │ │  │Exec │ │  │   │
│  │  │  └────┘ │ │  └────┘ │ │  └────┘ │  │   │
│  │  │  ┌────┐ │ │  ┌────┐ │ │  ┌────┐ │  │   │
│  │  │  │Eval │ │ │  │Eval │ │ │  │Eval │ │  │   │
│  │  │  └────┘ │ │  └────┘ │ │  └────┘ │  │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘  │   │
│  │       └───────────┼───────────┘       │   │
│  │              ┌────▼────┐               │   │
│  │              │  Guard  │               │   │
│  │              └────┬────┘               │   │
│  └──────────────────┼─────────────────────┘   │
└─────────────────────┼───────────────────────────┘
                      │ Shell Commands
              ┌───────▼───────┐
              │    System     │
              └───────────────┘
```

## 代理說明

- **Planner** - 分析需求、規劃任務、協調團隊
- **Executor** - 執行 Planner 交辦的具體任務
- **Evaluator** - 驗證 Executor 的執行結果
- **Guard** - 安全審查員，檢查 Shell 命令是否危險

## 開發指令

```bash
# 執行測試
python -m pytest tests/ -v

# 打包上傳 PyPI
python -m build
twine upload dist/*
```

## 依賴

- Python >= 3.10
- aiohttp >= 3.8.0

## License

MIT
