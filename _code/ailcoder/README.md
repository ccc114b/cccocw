# ailcoder

> AI Code Generator - 使用 AIL/ACL 框架

[![PyPI](https://img.shields.io/pypi/v/ailcoder)](https://pypi.org/project/ailcoder/)
[![Python](https://img.shields.io/pypi/pyversions/ailcoder)](https://pypi.org/project/ailcoder/)
[![License](https://img.shields.io/pypi/l/ailcoder)](https://opensource.org/licenses/MIT)

## 概述

ailcoder 是一個 AI 程式碼生成工具，基於 **AIL (AI Language)** 框架和 **ACL (AI Communication Language)** 通訊協定。

## AIL/ACL 簡介

### AIL (AI Language)

AIL 是一個為 AI 開發設計的 Python 框架，包含：

- **Intent** - 意圖宣告
- **Explore** - 並行探索多解法
- **Think** - 流式思考追蹤
- **Goal** - 目標導向編程
- **Memory** - 長期記憶

### ACL (AI Communication Language)

ACL 是 AI 與系統之間的結構化溝通格式：

| 指令 | 說明 |
|------|------|
| `<write file="...">` | 寫入檔案 |
| `<shell>` | 執行命令 |
| `<read file="...">` | 讀取檔案 |
| `<ask>` | 詢問指揮官 |

## 安裝

```bash
pip install ailcoder
```

## 快速開始

### 命令列

```bash
# 初始化 Ollama
ollama run minimax-m2.5:cloud

# 生成程式碼
ailcoder "建立一個 hello world 網頁"

# 指定輸出目錄
ailcoder "建立 SQLite TODO 應用" -o ./myproject

# 顯示除錯訊息
ailcoder "建立天氣查詢網站" -d
```

### Python API

```python
import asyncio
from ailcoder import MiniCode
from ailang import init_ollama

# 初始化
init_ollama(model="minimax-m2.5:cloud")

# 建立 agent
agent = MiniCode(root_dir="./generated", debug=True)

# 執行任務
async def main():
    await agent.run("""
        建立 SQLite TODO 應用：
        - 後端 Flask + SQLite
        - 首頁 /
        - API: GET/POST /api/todos
        - 前端 HTML + JS
    """)

asyncio.run(main())
```

## 架構

```
人類 → MiniCode → AIExecutor → ACL → 檔案系統
              ↑
        AICommander (回答問題)
```

## 角色分工

| 角色 | 職責 | 檔案系統 |
|------|------|---------|
| **AICommander** | 規劃、回答問題 | ❌ 無 |
| **AIExecutor** | 產生 ACL 指令 | ❌ 無 |
| **ACLHandler** | 實際寫入檔案 | ✅ 有 |

## 支援的 LLM

| 供應商 | 模型 |
|--------|------|
| Ollama | minimax-m2.5:cloud |
| Ollama | 其他本地模型 |

## 專案結構

```
ailang/
├── src/
│   ├── ailang/           # AIL 框架
│   │   ├── core.py      # Intent, Agent
│   │   ├── explore.py   # 並行探索
│   │   ├── goal.py      # 目標管理
│   │   └── llm.py       # LLM 整合
│   └── ailcoder/        # ailcoder 工具
│       ├── executor.py  # MiniCode
│       ├── acl_socket.py # ACL 通訊
│       └── cli.py       # 命令列
├── _doc/                # 文件
│   └── v0.5/           # AIL/ACL 架構
└── pyproject.toml      # PyPI 配置
```

## 論文與文件

- [AIL/ACL 架構說明](./_doc/v0.5/)
- [技術報告](./_doc/ailang_report.md)

## 授權

MIT License

## 作者

陳鍾誠 <ccc@ccc.ncku.edu.tw>
