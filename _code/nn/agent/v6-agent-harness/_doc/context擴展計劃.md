# Context 擴展計劃 - RAG 系統

## 現況分析

現有的 `agent0.py` 使用以下 context 策略：
- **短期記憶**：滾動的對話歷史（最近 N 輪）
- **長期記憶**：XML 格式的關鍵資訊列表（`<item>` 標籤）
- **Context 建構**：將 memory + history 拼接進 prompt

缺少：
- 文件級別的知識檢索（RAG）
- 向量嵌入（embeddings）
- 語意相似度搜索

---

## 設計方針

- **儲存載體**：SQLite（無需額外套件，Python 原生支援）
- **向量生成**：使用 Ollama embeddings API
- **相似度計算**：餘弦相似度（純 Python 實現）
- **依賴**：僅 `aiohttp`（現有）+ 標準庫

---

## RAG 系統架構

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  文件載入     │ ──▶ │   分塊       │ ──▶ │  向量化      │
│  (txt/md/py) │     │  500 tokens  │     │  Ollama API │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Agent Prompt │ ◀── │  相似度檢索   │ ◀── │   SQLite     │
│  (context)   │     │  (top_k)     │     │  向量庫      │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## SQLite Schema

```sql
-- context_vectors.db

-- 文件元數據表
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 分塊向量表
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB NOT NULL,  -- 存儲為 binary (pickle 或 numpy)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    UNIQUE(document_id, chunk_index)
);

-- 索引以加速相似度搜索
CREATE INDEX idx_chunks_doc ON chunks(document_id);
```

---

## 實作階段

### Phase 1: 基礎設施

- [ ] 新增 `rag.py` 模組
- [ ] 實現 `init_db()` - 建立 SQLite 表
- [ ] 實現 `chunk_text()` - 文字分塊
- [ ] 實現 `encode_embedding()` - Ollama embeddings

### Phase 2: 向量儲存

- [ ] 實現 `VectorStore` 類別
- [ ] `add_document(file_path)` - 載入並索引文件
- [ ] `save_chunk(doc_id, chunk)` - 存入 SQLite
- [ ] `get_embedding(text)` - 取得向量

### Phase 3: 檢索系統

- [ ] 實現 `cosine_similarity(a, b)` - 向量相似度
- [ ] 實現 `search(query, top_k)` - 檢索相關塊
- [ ] 實現 `index_directory(path)` - 批量索引

### Phase 4: Agent 整合

- [ ] 在 `build_context()` 中加入 RAG 結果
- [ ] 新增指令：`/index <path>` - 索引文件或目錄
- [ ] 新增指令：`/search <query>` - 搜尋知識庫
- [ ] 新增指令：`/rag on/off` - 開關 RAG

---

## API 設計

### VectorStore 類別

```python
import sqlite3
import hashlib
import json
import pickle
import numpy as np

class VectorStore:
    def __init__(self, db_path: str = "context_vectors.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化 SQLite 資料庫"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE NOT NULL,
                file_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        self.conn.commit()
    
    def add_document(self, file_path: str) -> int:
        """索引文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_hash = hashlib.md5(content.encode()).hexdigest()
        
        # 檢查是否已存在且未變更
        cursor = self.conn.execute(
            "SELECT id, file_hash FROM documents WHERE file_path = ?", (file_path,)
        )
        row = cursor.fetchone()
        if row and row[1] == file_hash:
            return row[0]  # 無需更新
        
        # 分塊
        chunks = chunk_text(content)
        
        # 刪除舊記錄
        if row:
            doc_id = row[0]
            self.conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
            self.conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        
        # 插入新記錄
        cursor = self.conn.execute(
            "INSERT INTO documents (file_path, file_hash) VALUES (?, ?)",
            (file_path, file_hash)
        )
        doc_id = cursor.lastrowid
        
        # 存入每個 chunk
        for i, chunk in enumerate(chunks):
            embedding = self._get_embedding(chunk)
            self.conn.execute(
                "INSERT INTO chunks (document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
                (doc_id, i, chunk, pickle.dumps(embedding))
            )
        
        self.conn.commit()
        return doc_id
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """呼叫 Ollama API 取得 embedding"""
        # 實現見 Phase 1
        ...
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """搜尋最相關的 chunks"""
        query_embedding = self._get_embedding(query)
        
        # 取出所有 chunks 計算相似度
        cursor = self.conn.execute(
            "SELECT id, content, embedding FROM chunks"
        )
        results = []
        for row in cursor:
            chunk_embedding = pickle.loads(row[2])
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            results.append({
                "id": row[0],
                "content": row[1],
                "similarity": similarity
            })
        
        # 取 top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """計算餘弦相似度"""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """將文字分塊（按字元，簡化版）"""
    words = text.split()
    chunks = []
    start = 0
    
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # 重疊
    
    return chunks
```

### Ollama Embedding

```python
async def call_ollama_embed(text: str) -> list[float]:
    """呼叫 Ollama embeddings API"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "minimax-m2.5:cloud", "prompt": text},
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            result = await resp.json()
            return result.get("embedding", [])
```

---

## Context 整合

### Prompt 模板

```python
RAG_ENABLED = True
RAG_TOP_K = 3
RAG_SIMILARITY_THRESHOLD = 0.5

def build_context():
    context_parts = []
    
    # 1. 知識庫檢索
    if RAG_ENABLED and user_query:
        results = vector_store.search(user_query, top_k=RAG_TOP_K)
        if results:
            knowledge = "\n".join(f"[{r['similarity']:.2f}] {r['content']}" for r in results)
            context_parts.append(f"<knowledge>\n{knowledge}\n</knowledge>")
    
    # 2. 長期記憶
    if key_info:
        items_xml = "\n".join(f"  <item>{k}</item>" for k in key_info)
        context_parts.append(f"<memory>\n{items_xml}\n</memory>")
    
    # 3. 對話歷史
    if conversation_history:
        context_parts.append("<history>\n" + "\n".join(conversation_history[-MAX_TURNS*2:]) + "\n</history>")
    
    return "\n\n".join(context_parts)
```

---

## 測試

```bash
# 測試資料庫初始化
python -c "from rag import VectorStore; vs = VectorStore(); print('DB OK')"

# 測試索引
python -c "from rag import VectorStore; vs = VectorStore(); vs.add_document('hello.py'); print('Indexed')"

# 測試搜尋
python -c "from rag import VectorStore; vs = VectorStore(); print(vs.search('hello'))"

# 清理測試資料庫
rm context_vectors.db
```

---

## 資料庫遷移（未來）

若需要支援多專案：

```sql
ALTER TABLE documents ADD COLUMN project_id TEXT;
ALTER TABLE chunks ADD COLUMN project_id TEXT;
CREATE INDEX idx_project ON chunks(project_id);
```

---

## 待討論事項

1. **相似度閾值**：預設 0.5 是否合適？
2. **Chunk 大小**：500 tokens 是否需要動態調整？
3. **更新策略**：檔案變更時全量重索引或增量更新？
4. **多模態**：是否支援圖片、PDF？
