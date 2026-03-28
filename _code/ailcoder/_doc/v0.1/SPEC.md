# AIL (AI Language) Specification

## 設計理念

- **AI-friendly**: 語義清晰無歧義，易於 AI 理解和生成
- **Human-readable**: 混合自然語言關鍵詞與簡潔符號
- **Natural flow**: 符合人類思考邏輯的程式執行順序

---

## 1. 基礎語法

### 1.1 變數宣告

```
let name = value
let count = 0
let message = "Hello AI"
```

### 1.2 資料類型

```
let number = 42           # 整數
let decimal = 3.14        # 浮點數
let text = "hello"        # 字串
let yes = true            # 布林值
let items = [1, 2, 3]     # 列表
let data = {              # 結構
    name: "AI"
    version: 1
}
```

### 1.3 註解

```
# 這是單行註解
```

---

## 2. 控制流

### 2.1 條件判斷

```
if condition then
    # do something
end

if score >= 60 then
    print "Pass"
else
    print "Fail"
end
```

### 2.2 迴圈

```
repeat 5 times
    print "loop"
end

for item in items
    print item
end

while count < 10
    count = count + 1
end
```

---

## 3. 函數

### 3.1 函數定義

```
function greet(name)
    return "Hello, " + name
end

function add(a, b)
    return a + b
end
```

### 3.2 函數呼叫

```
result = greet("AI")
sum = add(1, 2)
```

---

## 4. AI 專屬特性

### 4.1 意圖宣告 (Intent Declaration)

```
# 告訴 AI 這段程式碼的目的
intent "分析用戶情緒"
analyze sentiment from user_input
```

### 4.2 概率結果

```
let confidence = 0.85
when confidence > 0.7 then
    print "高置信度"
end
```

### 4.3 向量/嵌入操作

```
let embedding = vector([0.1, 0.5, 0.9])
let similarity = cosine_similarity(embedding_a, embedding_b)
```

### 4.4 工具/Agent 調用

```
# 調用外部工具
result = await tool("search", query: "天氣")
result = await agent("researcher", task: "找最新AI新聞")

# 並行執行多個任務
results = await all [
    tool("search", query: "蘋果"),
    tool("search", query: "香蕉")
]
```

### 4.5 記憶體/上下文

```
remember "user_preferences" as preferences
recall "user_preferences" into prefs
```

### 4.6 不確定性處理

```
maybe result = uncertain_operation()
if result is uncertain then
    print "需要更多資訊"
end
```

---

## 5. 模組與命名空間

### 5.1 引入模組

```
use math
use io
use ai
```

### 5.2 調用模組內容

```
math.sqrt(16)
io.print("hello")
ai.generate("寫一首詩")
```

---

## 6. 錯誤處理

```
try
    result = risky_operation()
catch error
    print "錯誤: " + error.message
finally
    print "完成清理"
end
```

---

## 7. 範例程式

### 範例 1: 簡單問答

```
use ai

let question = "什麼是人工智慧？"

intent "回答用戶問題"
answer = await ai.generate(question)

print answer
```

### 範例 2: 多 Agent 協作

```
use ai

# 三個 Agent 同時工作
news = await agent("news_finder", topic: "AI")
analysis = await agent("analyzer", data: news)
summary = await agent("summarizer", data: analysis)

print summary
```

### 範例 3: 條件式 AI 回應

```
use ai

let user_mood = "happy"

if user_mood == "happy" then
    response = await ai.generate("用開心的語氣稱讚用戶")
else if user_mood == "sad" then
    response = await ai.generate("用溫暖的語氣安慰用戶")
end

print response
```

---

## 8. 語法設計原則

| 原則 | 說明 |
|------|------|
| **意圖先行** | 用 `intent` 聲明程式碼目的 |
| **自然閱讀** | 從上到下，從左到右 |
| **明確命名** | 使用完整英文單詞，避免縮寫 |
| **縮排區塊** | 用縮排表示程式碼區塊 |
| **端點標記** | 用 `end` 標記區塊結束 |

---

## 9. 保留關鍵詞

```
if, then, else, elif, end
for, in, repeat, times, while
function, return
let, use
try, catch, finally
intent, remember, recall
true, false, maybe
await, all
```

---

## 10. 設計特點總結

1. **intent 宣告**: 讓 AI 知道每段程式碼的目標
2. **自然語法**: `if condition then` 比 `if(condition)` 更易讀
3. **AI 原語**: 內建 `vector`, `cosine_similarity`, `agent`, `tool` 等
4. **不確定性**: 處理 AI 輸出的概率性質
5. **記憶體**: 讓 AI 有長期記憶能力

---

*Version: 0.1 (Draft)*
*Design for: Human-AI Natural Interaction*
