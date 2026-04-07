# Prompt Engineering (提示詞工程)

## 概述

提示詞工程是設計和最佳化輸入提示詞（Prompt）的實踐，以獲得更好的 AI 模型輸出。是與大型語言模型 (LLM) 有效互動的關鍵技能。

## 提示詞基本結構

```
┌─────────────────────────────────────────────────────────────┐
│                    Prompt 結構                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [System]     你是一個專業的程式設計師                      │
│      ↓                                                   │
│  [Context]    使用 Python 3.9+，遵循 PEP 8 規範           │
│      ↓                                                   │
│  [Examples]   輸入: 交換兩個變數                          │
│               輸出: a, b = b, a                           │
│      ↓                                                   │
│  [Task]       寫一個計算費波那契數列的函式                  │
│      ↓                                                   │
│  [Format]     只輸出程式碼，不做解釋                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 核心策略

### 1. 清晰具體的指令

```python
# ❌ 不好的提示
"Write code"

# ✅ 好的提示
"""寫一個 Python 函式 calculate_fibonacci(n: int) -> int:
- 使用迭代而非遞迴
- 時間複雜度 O(n)
- 包含型別註解
- 附上 doctest 範例"""
```

### 2. Few-shot 範例

```python
prompt = """將以下句子翻譯成繁體中文：

範例 1:
英文: Hello, world!
中文: 你好，世界！

範例 2:
英文: How are you?
中文: 你好嗎？

現在翻譯:
英文: The weather is nice today.
中文:"""
```

### 3. Chain-of-Thought (思維鏈)

```python
prompt = """解決這個數學問題。請逐步思考。

問題：小明有 15 顆蘋果，給了朋友 7 顆，又買了 12 顆。
問題：他現在有幾顆蘋果？

讓我們逐步計算：

步驟 1: 初始數量 = 15 顆
步驟 2: 送出後 = 15 - 7 = 8 顆
步驟 3: 買進後 = 8 + 12 = 20 顆

答案：20 顆"""
```

### 4. 角色扮演

```python
prompt = """你是一位資深 DevOps 工程師，專精 Kubernetes 和 CI/CD。
你有 10 年的雲端原生開發經驗。

請評估以下部署策略，並提供改進建議：

deployment.yaml:
[您的 YAML 內容]

請從以下角度分析：
1. 資源配置是否合理
2. 高可用性設計
3. 安全性最佳實踐
4. 監控和日誌策略"""
```

## 進階技巧

### 1. 限制輸出格式

```python
# 要求特定格式
prompt = """用以下 JSON 格式回傳用戶資訊：
{
    "name": "姓名",
    "email": "電子郵件",
    "role": "角色"
}

只回傳 JSON，不要其他文字。"""
```

### 2. 結構化輸出

```python
from pydantic import BaseModel

class CodeReview(BaseModel):
    issues: list[str]
    suggestions: list[str]
    score: int  # 1-10

prompt = """你是一個程式碼審查員。分析以下程式碼並以 JSON 格式回傳：

[您的程式碼]

回傳格式：
{
    "issues": ["問題1", "問題2"],
    "suggestions": ["建議1", "建議2"],
    "score": 8
}"""
```

### 3. 分解複雜任務

```python
# ❌ 一步完成複雜任務
prompt = "建立一個電子商務系統"

# ✅ 分步驟
prompts = [
    "設計資料庫 schema，只回傳 SQL",
    "根據 schema 實作 CRUD API，只回傳 Python 程式碼",
    "實作身份驗證中間件",
    "實作錯誤處理和日誌記錄"
]
```

## Prompt 模式

### 1. Template Pattern

```python
class PromptTemplate:
    def __init__(self, template: str):
        self.template = template
    
    def render(self, **kwargs) -> str:
        return self.template.format(**kwargs)

# 使用
template = PromptTemplate("""
分析以下 {language} 程式碼：

```{language}
{code}
```

回傳格式：
- 時間複雜度: O(?)
- 空間複雜度: O(?)
- 主要問題: ...
- 改進建議: ...
""")

prompt = template.render(language="python", code=my_code)
```

### 2. Chain Pattern

```python
def chain_of_prompts(user_input: str) -> str:
    # 第一步：分類
    classification = llm(f"""分類這個請求: {user_input}""")
    
    # 第二步：根據分類處理
    if "code" in classification:
        return llm(f"為這個需求寫程式碼: {user_input}")
    elif "debug" in classification:
        return llm(f"找出這個錯誤的原因: {user_input}")
    else:
        return llm(f"回答這個問題: {user_input}")
```

### 3. Ensemble Pattern

```python
def ensemble_prompt(prompt: str, n_responses: int = 3) -> str:
    responses = []
    for _ in range(n_responses):
        response = llm(prompt)
        responses.append(response)
    
    # 讓 LLM 綜合所有回答
    return llm(f"""综合以下多个回答，给出最佳回复：

回答1: {responses[0]}
回答2: {responses[1]}
回答3: {responses[2]}

请给出最全面、最准确的答案。""")
```

## 常見陷阱

| 陷阱 | 說明 | 解決方法 |
|------|------|----------|
| 模糊指令 | 指令不夠具體 | 使用明確的動作詞 |
| 資訊過載 | 一次給太多資訊 | 分步驟處理 |
| 缺乏上下文 | 模型不知道背景 | 提供相關上下文 |
| 忽略限制 | 沒說不要做什麼 | 明確列舉限制 |

## 測試和疊代

```python
def test_prompt(prompt: str, test_cases: list[dict]) -> dict:
    results = []
    for case in test_cases:
        response = llm(prompt.format(**case["input"]))
        results.append({
            "input": case["input"],
            "expected": case["expected"],
            "actual": response,
            "passed": evaluate(response, case["expected"])
        })
    return {
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": [r for r in results if not r["passed"]]
    }
```

## 相關資源

- 相關概念：[[Context Engineering]]
- 相關概念：[[Harness Engineering]]

## Tags

#Prompt #提示詞工程 #LLM #AI工程
