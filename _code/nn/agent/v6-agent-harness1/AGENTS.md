# AGENTS.md - v6-agent-harness

## 概述

Harness Engineering Agent 系統，支援 Plan/Exec/Eval 三種模式。

**依賴：** aiohttp, asyncio

## 執行

```bash
python main.py
```

## 指令

| 指令 | 說明 |
|------|------|
| `/help` | 顯示幫助 |
| `/plan` | 切換至 Plan Mode（Planner） |
| `/exec` | 切換至 Exec Mode（Executor） |
| `/eval` | 切換至 Eval Mode（Evaluator） |
| `/memory` | 顯示長期記憶 |
| `/new` | 新建 session |
| `/export` | 匯出 session transcript |
| `/init [dir]` | 初始化 AGENTS.md（預設目前資料夾） |
| `/quit` | 結束 |

## Agent 類別

| 類別 | 角色 |
|------|------|
| `Agent` | 基類，含 memory、messages、think() |
| `Planner` | 規劃任務、讀取資訊（不寫程式） |
| `Executor` | 執行 shell 命令 |
| `Evaluator` | 驗證執行結果 |
| `Guard` | 安全審查，控管命令執行 |
| `UserAgent` | 協調者，支援三種模式 |

## /init [dir]

掃描專案資料夾，讓 Planner 分析並建立理解，存入 memory。

- `dir` 為可選參數，預設為目前資料夾
- 掃描目錄結構、README、相關設定檔
- Planner 分析後輸出專案類型、框架、測試方式等

## 測試

```bash
python -m pytest tests/ -v -m "not asyncio"  # 單元測試
python -m pytest tests/ -v                    # 含整合測試
```

## 重要設定

- Ollama API: `http://localhost:11434`
- 預設模型: `minimax-m2.5:cloud`
- 工作區: `~/.agent0`
