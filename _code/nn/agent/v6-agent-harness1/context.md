# context.py 使用說明

RAG 語義檢索工具，使用 SQLite 儲存向量索引。

## 安裝

無需額外依賴，僅需 Python 標準庫 + numpy：

```bash
pip install numpy
```

## 快速開始

```bash
# 索引單一文件
python context.py index agent0.py

# 索引整個目錄
python context.py index ./src

# 搜尋
python context.py search "memory management"

# 查看統計
python context.py stats
```

## 命令

### search - 語義搜尋

```bash
python context.py search "query" [-k N] [-d db.db]
```

**參數：**
- `query` - 搜尋關鍵字
- `-k, --top` - 返回結果數量（預設 5）
- `-d, --db` - 資料庫路徑（預設 `context_vectors.db`）

**範例：**
```bash
# 基本搜尋
python context.py search "async await"

# 返回更多結果
python context.py search "database" -k 10

# 使用自訂資料庫
python context.py search "sqlite" -d my_docs.db
```

**輸出格式：**
```
[0.847] agent0.py
  async def call_ollama(prompt: str, system: str = "") -> str:...

[0.623] context.py
  def search(self, query: str, top_k: int = 5) -> list[dict]:...
```

---

### index - 建立索引

```bash
python context.py index <file|dir> [-d db.db]
```

**參數：**
- `path` - 檔案或目錄路徑
- `-d, --db` - 資料庫路徑（預設 `context_vectors.db`）

**範例：**
```bash
# 索引單一檔案
python context.py index agent0.py

# 索引整個專案
python context.py index .

# 索引特定目錄
python context.py index ./src

# 使用自訂資料庫
python context.py index ./docs -d project.db
```

**支援格式：** `.txt`, `.md`, `.py`, `.js`, `.json`

**自動排除：** `node_modules`, `__pycache__`, `.git`, `venv`

---

### stats - 統計資訊

```bash
python context.py stats [-d db.db]
```

**範例：**
```bash
python context.py stats
# 輸出：
# Documents: 5
# Chunks: 23
```

---

### clear - 清除資料

```bash
python context.py clear [-d db.db]
```

**範例：**
```bash
# 清除預設資料庫
python context.py clear

# 清除自訂資料庫
python context.py clear -d old_project.db
```

---

### test - 執行測試

```bash
python context.py test
```

---

## 在程式碼中使用

```python
from context import VectorStore

# 建立或開啟資料庫
vs = VectorStore("my_context.db")

# 索引檔案
vs.add_document("agent0.py")
vs.add_document("context.py")
vs.build_index()

# 搜尋
results = vs.search("async await", top_k=5)
for r in results:
    print(f"[{r['similarity']:.3f}] {r['file_path']}")
    print(f"  {r['content']}")

# 關閉
vs.close()
```

### API 參考

#### VectorStore

| 方法 | 說明 |
|------|------|
| `add_document(path)` | 索引單一檔案 |
| `add_directory(path)` | 索引目錄下所有支援的檔案 |
| `build_index()` | 建立 TF-IDF 向量索引 |
| `search(query, top_k)` | 語義搜尋，返回 top_k 個結果 |
| `stats()` | 返回 `{"documents": N, "chunks": N}` |
| `clear()` | 清除所有資料 |
| `close()` | 關閉資料庫連接 |

#### 回傳格式

`search()` 返回的結果格式：

```python
{
    "id": 1,
    "content": "chunk text content...",
    "file_path": "agent0.py",
    "similarity": 0.847  # 0.0 ~ 1.0
}
```

---

## 工作原理

```
1. 讀取檔案 → 分塊（每塊 500 words，重疊 50）
2. 所有文本 → TF-IDF 向量化（384 維）
3. 向量 → 存入 SQLite BLOB 欄位
4. 查詢時：查詢文字 → 向量化 → 計算餘弦相似度 → 排序返回
```

---

## 常見問題

**Q: 為什麼用 TF-IDF 而不是 Ollama embeddings？**
A: Ollama 的 embedding API 並非所有模型都支援，TF-IDF作為備選方案可在任何環境運作。

**Q: 如何處理二進制檔案？**
A: 目前僅支援文字檔，二進制檔案會被跳過。

**Q: 資料庫可以跨語言使用嗎？**
A: 可以，SQLite 是跨平台的，embedding BLOB 可被任何語言解析。

**Q: 如何增量更新索引？**
A: 再次執行 `index` 命令即可自動偵測變更的檔案並更新。
