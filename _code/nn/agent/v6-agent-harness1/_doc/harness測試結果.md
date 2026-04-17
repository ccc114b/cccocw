# Harness 測試結果

## 問題：Planner 無回應

### 症狀
```
你：在 blog/ 下，用 fastapi 寫一個簡易的網誌系統。請先寫出 blog/_doc/plan.md

🤖 [PLAN] 
```

Planner 無任何輸出，直接無回應。

### 原因分析

執行測試發現 Ollama API 返回錯誤：

```bash
$ curl http://localhost:11434/api/generate -d '{"model": "minimax-m2.5:cloud", "prompt": "說 hello", "stream": false}'
{"error":"you (ccckmit) have reached your weekly usage limit, upgrade for higher limits: https://ollama.com/upgrade (ref: accb3b2d-d1c9-4524-bd8f-dd6153d980fd)"}
```

**根本原因：** `minimax-m2.5:cloud` 已達每週使用上限

### 測試過程

1. 直接呼叫 `call_ollama()` 回傳空字串
2. 檢查 Ollama API：`curl http://localhost:11434/api/tags` 成功
3. 測試 API generate：返回 usage limit 錯誤
4. 嘗試 `gemma4:31b-cloud` 模型：同樣返回 usage limit 錯誤

### 解決方案

1. **升級 Ollama 方案** - https://ollama.com/upgrade
2. **等待重置** - 每週限制會自動重置
3. **使用本地模型** - 部署本地模型避免限制

### 已實作

在 `call_ollama()` 中加入錯誤處理：

```python
if "error" in result:
    error_msg = result.get("error", "")
    if "usage limit" in error_msg.lower():
        raise Exception(f"Ollama 使用限制已達上限：{error_msg}\n請升級或等待重置。")
    raise Exception(f"Ollama 錯誤：{error_msg}")
```

現在當 API 限制達到時，會顯示清楚錯誤訊息而非靜默失敗。

### 可用模型

```json
{
  "models": [
    {"name": "gemma4:31b-cloud", "model": "gemma4:31b-cloud"},
    {"name": "minimax-m2.5:cloud", "model": "minimax-m2.5:cloud"}
  ]
}
```

兩個遠端模型都已達限制。
