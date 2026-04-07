# Context Engineering (上下文工程)

## 概述

上下文工程是設計和管理與 AI 模型互動時的上下文（Context）策略，最大化模型對任務的理解和表現。是 Prompt 工程的延伸，專注於資訊的組織和呈現方式。

## Context 的組成

```
┌─────────────────────────────────────────────────────────────┐
│                    Context 組成                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  System Context                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 角色定義、能力邊界、行為約束                          │  │
│  └─────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  Task Context                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 任務描述、成功標準、預期輸出格式                      │  │
│  └─────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  World Context                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 程式碼庫結構、相關檔案、領域知識                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  Session Context                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 對話歷史、已確定的決策、相關約束                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 上下文管理策略

### 1. RAG (Retrieval Augmented Generation)

```python
from langchain import OpenAI, VectorDBQA
from langchain.embeddings import OpenAIEmbeddings

class CodebaseRAG:
    def __init__(self, codebase_path: str):
        self.codebase = CodebaseIndexer(codebase_path)
        self.embeddings = OpenAIEmbeddings()
    
    def get_context(self, query: str, max_tokens: int = 4000) -> str:
        # 1. 檢索相關程式碼
        relevant_docs = self.codebase.search(query, top_k=5)
        
        # 2. 按相關性排序
        relevant_docs.sort(key=lambda d: d.score, reverse=True)
        
        # 3. 截斷至 token 限制
        context = ""
        for doc in relevant_docs:
            if len(context) + len(doc.content) < max_tokens:
                context += f"\n\n{doc.metadata}\n{doc.content}"
        
        return context
    
    def query(self, question: str) -> str:
        context = self.get_context(question)
        prompt = f"""根據以下程式碼上下文回答問題：

{context}

問題: {question}

回答:"""
        return llm(prompt)
```

### 2. 對話歷史管理

```python
class ConversationManager:
    def __init__(self, max_turns: int = 10):
        self.messages = []
        self.max_turns = max_turns
        self.summary_history = []
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        
        # 定期摘要
        if len(self.messages) > self.max_turns:
            self._summarize_and_compress()
    
    def _summarize_and_compress(self):
        # 將前半部分摘要
        old_messages = self.messages[:len(self.messages)//2]
        summary_prompt = "摘要以下對話的要點：\n" + "\n".join(
            f"{m['role']}: {m['content'][:200]}" for m in old_messages
        )
        summary = llm(summary_prompt)
        
        # 替換為摘要
        self.summary_history.append(summary)
        self.messages = self.messages[len(old_messages):]
    
    def get_context_window(self) -> list[dict]:
        return self.summary_history + self.messages
```

### 3. 分塊策略 (Chunking)

```python
class CodeChunker:
    def chunk_by_function(self, code: str) -> list[dict]:
        """按函式分塊"""
        tree = ast.parse(code)
        chunks = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chunk_code = ast.get_source_segment(code, node)
                chunks.append({
                    "type": "function",
                    "name": node.name,
                    "content": chunk_code,
                    "docstring": ast.get_docstring(node)
                })
        return chunks
    
    def chunk_by_file(self, repo_path: str) -> list[dict]:
        """按檔案分塊"""
        chunks = []
        for filepath in glob(f"{repo_path}/**/*.py", recursive=True):
            with open(filepath) as f:
                chunks.append({
                    "type": "file",
                    "path": filepath,
                    "content": f.read()
                })
        return chunks
    
    def smart_chunk(self, code: str, max_lines: int = 100) -> list[str]:
        """智能分塊，保留語義完整性"""
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_lines = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            current_lines += 1
            
            # 在語義邊界處分割
            if current_lines >= max_lines:
                if self._is_semantic_boundary(lines, i):
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_lines = 0
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
```

## 上下文最佳化

### 1. 相關性檢索

```python
class ContextSelector:
    def __init__(self, embeddings_model):
        self.embeddings = embeddings_model
    
    def select_relevant(self, query: str, 
                       documents: list[dict],
                       top_k: int = 5,
                       rerank: bool = True) -> list[dict]:
        
        # 1. 向量相似度檢索
        query_embedding = self.embeddings.embed(query)
        
        scored_docs = []
        for doc in documents:
            doc_embedding = self.embeddings.embed(doc['content'])
            similarity = cosine_similarity(query_embedding, doc_embedding)
            scored_docs.append((similarity, doc))
        
        # 2. 排序
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # 3. 重排（MMR）
        if rerank:
            return self._max_marginal_relevance(scored_docs[:top_k*2], query)
        
        return [doc for _, doc in scored_docs[:top_k]]
    
    def _max_marginal_relevance(self, docs: list, query: str, 
                               lambda_mult: float = 0.5) -> list[dict]:
        """最大邊際相關性，避免冗餘"""
        selected = []
        selected_embeddings = []
        
        for _, doc in docs:
            doc_emb = self.embeddings.embed(doc['content'])
            
            # 計算 MMR 分數
            relevance = cosine_similarity(doc_emb, self.embeddings.embed(query))
            diversity = max(
                cosine_similarity(doc_emb, emb) 
                for emb in selected_embeddings
            ) if selected_embeddings else 0
            
            mmr_score = relevance - lambda_mult * diversity
            
            if len(selected) < 5:
                selected.append(doc)
                selected_embeddings.append(doc_emb)
        
        return selected
```

### 2. 上下文視窗管理

```python
class SlidingWindowContext:
    def __init__(self, model: str, max_tokens: int = 128000):
        self.max_tokens = max_tokens
        self.model = model
        self.messages = []
    
    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._ensure_within_limit()
    
    def _ensure_within_limit(self):
        total_tokens = self._count_tokens(self.messages)
        
        while total_tokens > self.max_tokens and len(self.messages) > 1:
            self.messages.pop(0)
            total_tokens = self._count_tokens(self.messages)
    
    def get_context(self) -> list[dict]:
        return self.messages
```

## 上下文工程最佳實踐

| 原則 | 說明 |
|------|------|
| 精確相關 | 只包含與當前任務相關的資訊 |
| 結構清晰 | 使用標題、分隔符號組織資訊 |
| 優先排序 | 最重要資訊放在前面 |
| 及時清理 | 移除不再需要的上下文 |
| 版本控制 | 追蹤上下文變化 |

## 評估指標

```python
def evaluate_context(context: str, task: str, response: str) -> dict:
    return {
        "relevance": compute_relevance(context, task),
        "coverage": compute_coverage(context, task),
        "conciseness": compute_conciseness(context),
        "effectiveness": evaluate_task_success(response, task)
    }
```

## 相關資源

- 相關概念：[[Prompt工程]]
- 相關概念：[[Harness Engineering]]

## Tags

#Context #上下文工程 #RAG #LLM #資訊檢索
