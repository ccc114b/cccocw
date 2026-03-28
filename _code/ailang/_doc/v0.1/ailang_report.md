# AIL (AI Language) 技術報告

## 為 AI 設計的程式語言 / Python 擴充套件

**作者**: AIL 開發團隊  
**日期**: 2026-03-28  
**版本**: 0.1.0

---

## 摘要

本報告介紹 AIL (AI Language)，一個專為人工智慧開發設計的 Python 擴充套件。傳統程式語言均以人類為主要使用者設計，而 AIL 旨在解決 AI 程式開發的特殊需求，包括意圖表達、多解法並行探索、流式思考追蹤、目標導向編程等特性。

---

## 1. 背景與動機

### 1.1 現有程式語言的局限性

現有程式語言（如 Python、JavaScript、Go）均以人類為主要使用者設計，其語法特點包括：

- **命令式編程**：告訴電腦「如何做」而不是「做什麼」
- **確定性輸出**：假設每個函數都會返回確定結果
- **單一路徑**：一次只執行一種解法
- **缺乏意圖追蹤**：程式碼目的需要閱讀整體才能理解

### 1.2 AI 開發的特殊需求

人工智慧開發具有以下獨特需求：

1. **不確定性處理**：AI 輸出本質上是概率性的
2. **多解法探索**：需要同時嘗試多種方法並比較結果
3. **思考過程追蹤**：AI 的推理過程需要被記錄和解釋
4. **目標導向**：更強調「做什麼」而非「怎麼做」
5. **多 Agent 協作**：多個 AI Agent 需要有效溝通

---

## 2. AIL 設計

### 2.1 設計原則

AIL 遵循以下設計原則：

| 原則 | 說明 |
|------|------|
| **意圖先行** | 用 `@intent` 聲明程式碼目的 |
| **自然可讀** | 語法接近自然語言 (`if condition then`) |
| **AI 原生** | 內建向量、信心度、Agent 等 AI 概念 |
| **漸進採用** | 可與現有 Python 程式碼共存 |

### 2.2 核心功能模組

```
ailang/
├── core.py          # 核心功能 (intent, agent, tool)
├── memory.py        # 長期記憶機制
├── vector.py        # 向量/嵌入操作
├── explore.py       # 並行探索多解法
├── think.py         # 流式思考追蹤
├── goal.py          # 目標宣告與追蹤
└── parser.py        # 自訂語法解析器
```

---

## 3. 功能說明

### 3.1 意圖宣告 (Intent)

```python
@intent("翻譯這段文字")
async def translate(text: str, to_lang: str) -> str:
    return await ai.translate(text, to_lang)
```

**效益**：讓 AI 知道每段程式碼的目的，提升協作效率。

### 3.2 並行探索 (Explore)

```python
# 同時嘗試三種解法，選擇最佳結果
result = await explore([
    method_dfs,
    method_bfs,
    method_dp,
])
```

**效益**：AI 可同時探索多種解法，適用於複雜問題求解。

### 3.3 流式思考 (Think)

```python
# 建立清晰的推理鏈
result = think("天氣好不好") \
    .because("天空是藍色的") \
    .but("現在有雲") \
    .therefore("可能是陰天")
```

**效益**：記錄 AI 思考過程，便於解釋和 Debug。

### 3.4 目標宣告 (Goal)

```python
@goal()
async def 翻譯文章():
    return await translate_article()

# 或使用上下文管理器
async with goal("翻譯文章") as g:
    result = await do_work()
    g.complete(result)
```

**效益**：自動追蹤目標狀態、耗時、成本等指標。

### 3.5 不確定性處理 (Maybe)

```python
# AI 輸出帶有信心度
result = maybe(llm_output, confidence=0.85)
if result.is_certain:
    use(result.value)
```

**效益**：原生支援 AI 輸出的概率性質。

---

## 4. 實作與整合

### 4.1 LLM 整合

AIL 支援多種 LLM API：

```python
# OpenRouter (推薦 - 有免費額度)
init_openrouter(api_key, model="openrouter/free")

# MiniMax
init_minimax(api_key, model="MiniMax-M2.5")

# Groq
init_minimax(api_key, base_url="https://api.groq.com/openai/v1")
```

### 4.2 環境變數配置

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-xxx
MINIMAX_API_KEY=sk-api-xxx
```

---

## 5. 比較分析

### 5.1 功能比較

| 特性 | 傳統 Python | AIL |
|------|-------------|-----|
| 意圖宣告 | 無 | `@intent` 裝飾器 |
| 多解法探索 | 需手動寫 async | `explore()` 一次搞定 |
| 思考追蹤 | print 分散各處 | `think()` 鏈式表達 |
| 目標管理 | 自己寫 logger | `@goal()` 自動追蹤 |
| 不確定性 | 無 | `maybe()` 原生支援 |
| 向量運算 | 需 NumPy | 原生 `Vector` 類 |
| Agent 機制 | 需框架 | 原生 `Agent` 類 |

### 5.2 程式碼範例比較

#### 翻譯功能

```python
# 傳統 Python
@router.post("/translate")
async def translate(text: str, to_lang: str):
    result = await llm.translate(text, to_lang)
    logger.info(f"翻譯: {text} -> {to_lang}")
    return result

# AIL
@intent("翻譯用戶輸入的文字")
async def translate(text: str, to_lang: str) -> str:
    return await llm.translate(text, to_lang)
```

#### 多解法探索

```python
# 傳統 Python
async def solve_with_all_methods(problem):
    results = await asyncio.gather(
        method_a(problem),
        method_b(problem),
        method_c(problem)
    )
    # 手動比較結果
    best = max(results, key=lambda x: x.confidence)
    return best

# AIL
result = await explore([method_a, method_b, method_c])
```

### 5.3 優缺點對比

#### AIL 優點

1. **表達性更強**：意圖一目了然
2. **開發效率高**：減少樣板代碼
3. **AI 友好**：专为 AI 开发场景优化
4. **可解釋性**：思考過程可追蹤

#### AIL 缺點

1. **學習成本**：需學新 API
2. **靈活性較低**：受框架約束
3. **生態年輕**： 無現成庫支援
4. **效能開銷**：抽象層有額外開銷

#### 適用場景

```
AIL 適合:
✓ AI Agent 開發
✓ 多模型協作專案
✓ 需要思考過程追蹤
✓ 實驗性研究

傳統 Python 適合:
✓ 效能敏感應用
✓ 簡單腳本
✓ 已有完整生態的項目
✓ 團隊不熟悉新框架
```

---

## 6. 技術規格

### 6.1 環境需求

- Python 3.10+
- aiohttp (用於非同步 HTTP)

### 6.2 安裝

```bash
pip install aiohttp
export PYTHONPATH=src
```

### 6.3 執行範例

```bash
# 基本範例
PYTHONPATH=src python examples/basic.py

# AI 功能範例
PYTHONPATH=src python examples/ai_features.py
```

---

## 7. 結論

AIL 並非要取代傳統程式語言，而是在 **AI 開發** 這個特定領域提供更表達性的抽象。透過引入意圖宣告、並行探索、流式思考、目標追蹤等特性，AIL 使 AI 程式的開發更直觀、除錯更容易、協作更高效。

隨著 AI 技術的發展，我們相信未來會有更多針對 AI 開發最佳化的新語言和工具出現。AIL 正是這一方向的初步嘗試。

---

## 8. 參考與連結

- GitHub: [https://github.com/ailang/ailang](https://github.com/ailang/ailang)
- OpenRouter: https://openrouter.ai
- MiniMax: https://platform.minimax.io
- Groq: https://console.groq.com

---

*本報告採用 Markdown 格式撰寫*
