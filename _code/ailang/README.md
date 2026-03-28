# AIL (AI Language)

為人工智慧開發設計的 Python 擴充套件

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 特色

AIL 是一個專為 AI 開發設計的 Python 框架，引入了四個核心原語：

- **Intent** - 意圖宣告，讓程式目的更清晰
- **Explore** - 並行探索多解法，自動選擇最佳結果
- **Think** - 流式思考追蹤，記錄 AI 推理過程
- **Goal** - 目標導向編程，自動追蹤任務狀態與成本

## 安裝

```bash
# 克隆專案
git clone https://github.com/ccc114b/ailang.git
cd ailang

# 安裝依賴
pip install aiohttp
```

## 快速開始

### 1. 設定環境變數

```bash
# 編輯 .env
cp .env.example .env
# 填入你的 API Key

# 或是直接設定
export OPENROUTER_API_KEY="your-key"
```

### 2. 使用範例

```python
from ailang import intent, agent, explore, think, goal

# 意圖宣告
@intent("翻譯這段文字")
async def translate(text: str):
    return await ai.translate(text)

# 並行探索
result = await explore([
    method_dfs,
    method_bfs,
    method_dp,
])

# 流式思考
think("天氣好不好") \
    .because("天空是藍色的") \
    .but("現在有雲") \
    .therefore("可能是陰天")

# 目標宣告
@goal()
async def 翻譯文章():
    return await translate_article()
```

## 執行範例

```bash
# 基本範例
./test.sh

# 或
PYTHONPATH=src python examples/basic.py

# AI 功能展示
PYTHONPATH=src python examples/ai_features.py
```

## 支援的 LLM

AIL 支援多種 LLM 供應商：

| 供應商 | 特色 |
|--------|------|
| OpenRouter | 免費額度，推薦使用 |
| MiniMax | M2.5 / M2.7 模型 |
| Groq | 速度快 |

```python
# OpenRouter (推薦)
init_openrouter(api_key, model="openrouter/free")

# MiniMax
init_minimax(api_key, model="MiniMax-M2.5")

# Groq
init_minimax(api_key, base_url="https://api.groq.com/openai/v1")
```

## 專案結構

```
ailang/
├── src/ailang/           # 核心程式碼
│   ├── core.py          # Intent, Agent, Tool
│   ├── explore.py       # 並行探索
│   ├── think.py         # 流式思考
│   ├── goal.py          # 目標管理
│   ├── memory.py        # 長期記憶
│   ├── vector.py        # 向量運算
│   └── llm.py           # LLM 整合
├── examples/            # 使用範例
│   ├── basic.py         # 基本功能
│   ├── ai_features.py   # AI 原生功能
│   ├── openrouter.py    # OpenRouter 範例
│   └── minimax.py       # MiniMax 範例
└── _doc/               # 文件
    ├── ailang_report.md      # 技術報告
    ├── ailang_paper_english.md  # 論文 (英文)
    └── ailang_paper_tw.md    # 論文 (中文)
```

## 論文與文件

- [技術報告](./_doc/ailang_report.md)
- [論文 (英文)](./_doc/ailang_paper_english.md)
- [論文 (中文)](./_doc/ailang_paper_tw.md)

## 為什麼用 AIL？

| 特性 | 傳統 Python | AIL |
|------|-------------|-----|
| 意圖表達 | 無 | `@intent` 宣告 |
| 多解法探索 | 手動 async | `explore()` 一次搞定 |
| 思考追蹤 | print 分散 | `think()` 鏈式 |
| 目標管理 | 自己寫 logger | `@goal()` 自動 |

## 授權

MIT License
