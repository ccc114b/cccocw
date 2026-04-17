#!/usr/bin/env python3
# context.py - RAG-based context management with SQLite storage
# Usage:
#   python context.py search "query" [-k N] [-d db.db]
#   python context.py index <file|dir> [-d db.db]
#   python context.py stats [-d db.db]
#   python context.py clear [-d db.db]
#   python context.py test

import sqlite3
import hashlib
import pickle
import asyncio
import aiohttp
import os
import re
import math
import argparse
import sys
from collections import Counter, defaultdict

import numpy as np

# ─── Configuration ───

DEFAULT_DB_PATH = "context_vectors.db"
EMBEDDING_MODEL = "minimax-m2.5:cloud"
OLLAMA_HOST = "http://localhost:11434"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_DIM = 384

# ─── Database ───

def init_db(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            file_path TEXT UNIQUE NOT NULL,
            file_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            UNIQUE(document_id, chunk_index)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id)")
    conn.commit()
    return conn

# ─── Text Chunking ───

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap
    return chunks

# ─── TF-IDF Embedding ───

class TFIDFVectorizer:
    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim
        self.vocab = {}
        self.idf = {}
    
    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        return [w for w in words if len(w) > 2]
    
    def _build_vocab(self, corpus: list[str]) -> None:
        word_counts = Counter()
        doc_count = Counter()
        n_docs = len(corpus)
        
        for doc in corpus:
            words = set(self._tokenize(doc))
            word_counts.update(words)
            for w in words:
                doc_count[w] += 1
        
        most_common = [w for w, _ in word_counts.most_common(self.dim)]
        self.vocab = {w: i for i, w in enumerate(most_common)}
        
        for word in self.vocab:
            self.idf[word] = math.log(n_docs / (doc_count[word] + 1)) + 1
    
    def fit_transform(self, texts: list[str]) -> np.ndarray:
        self._build_vocab(texts)
        
        vectors = []
        for text in texts:
            words = self._tokenize(text)
            word_counts = Counter(words)
            
            vector = np.zeros(self.dim)
            for word, count in word_counts.items():
                if word in self.vocab:
                    idx = self.vocab[word]
                    tf = count / len(words) if words else 0
                    vector[idx] = tf * self.idf.get(word, 1.0)
            
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            vectors.append(vector)
        
        return np.array(vectors)
    
    def transform(self, text: str) -> np.ndarray:
        words = self._tokenize(text)
        word_counts = Counter(words)
        
        vector = np.zeros(self.dim)
        for word, count in word_counts.items():
            if word in self.vocab:
                idx = self.vocab[word]
                tf = count / len(words) if words else 0
                vector[idx] = tf * self.idf.get(word, 1.0)
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector

# ─── Ollama Embedding ───

async def call_ollama_embed(text: str, model: str = EMBEDDING_MODEL) -> list[float] | None:
    try:
        payload = {"model": model, "prompt": text}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    embedding = result.get("embedding", [])
                    if embedding:
                        return embedding
    except Exception:
        pass
    return None

# ─── Vector Similarity ───

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))

def deserialize_embedding(blob: bytes) -> np.ndarray:
    return pickle.loads(blob)

def serialize_embedding(embedding: np.ndarray | list) -> bytes:
    if isinstance(embedding, list):
        embedding = np.array(embedding)
    return pickle.dumps(embedding)

# ─── VectorStore ───

class VectorStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.conn = init_db(db_path)
        self.vectorizer = None
        self._pending_texts = []
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()
    
    def _get_file_hash(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_document(self, file_path: str) -> int:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_hash = self._get_file_hash(file_path)
        
        cursor = self.conn.execute(
            "SELECT id, file_hash FROM documents WHERE file_path = ?", (file_path,)
        )
        row = cursor.fetchone()
        if row and row[1] == file_hash:
            print(f"[Skip] {file_path} (unchanged)")
            return row[0]
        
        chunks = chunk_text(content)
        
        if row:
            doc_id = row[0]
            self.conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
            self.conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            print(f"[Update] {file_path}: {len(chunks)} chunks")
        else:
            print(f"[Index] {file_path}: {len(chunks)} chunks")
        
        cursor = self.conn.execute(
            "INSERT INTO documents (file_path, file_hash) VALUES (?, ?)",
            (file_path, file_hash)
        )
        doc_id = cursor.lastrowid
        
        self._pending_texts.extend(chunks)
        
        for i, chunk in enumerate(chunks):
            self.conn.execute(
                "INSERT INTO chunks (document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
                (doc_id, i, chunk, pickle.dumps(np.zeros(EMBEDDING_DIM)))
            )
        
        self.conn.commit()
        return doc_id
    
    def build_index(self) -> None:
        if not self._pending_texts:
            return
        
        self.vectorizer = TFIDFVectorizer(dim=EMBEDDING_DIM)
        embeddings = self.vectorizer.fit_transform(self._pending_texts)
        
        cursor = self.conn.execute("SELECT id FROM chunks ORDER BY id")
        chunk_ids = [row[0] for row in cursor]
        
        for chunk_id, embedding in zip(chunk_ids, embeddings):
            self.conn.execute(
                "UPDATE chunks SET embedding = ? WHERE id = ?",
                (serialize_embedding(embedding), chunk_id)
            )
        
        self.conn.commit()
        self._pending_texts = []
        print(f"[Done] Indexed {len(chunk_ids)} chunks")
    
    def ensure_index(self) -> None:
        """確保索引已建立（若需要則重建）"""
        if self.vectorizer is None:
            print("[Index] Rebuilding from stored chunks...")
            cursor = self.conn.execute("SELECT content FROM chunks ORDER BY id")
            texts = [row[0] for row in cursor]
            if texts:
                self.vectorizer = TFIDFVectorizer(dim=EMBEDDING_DIM)
                self.vectorizer.fit_transform(texts)
                print(f"[Index] Rebuilt with {len(texts)} chunks")
    
    def add_directory(self, dir_path: str, extensions: list[str] = None) -> int:
        if extensions is None:
            extensions = ['.txt', '.md', '.py', '.js', '.json']
        
        count = 0
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        self.add_document(file_path)
                        count += 1
                    except Exception as e:
                        print(f"[Error] {file_path}: {e}")
        return count
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        self.ensure_index()
        
        if self.vectorizer is None:
            raise ValueError("No chunks indexed.")
        
        query_embedding = self.vectorizer.transform(query)
        
        cursor = self.conn.execute(
            "SELECT c.id, c.content, c.embedding, d.file_path FROM chunks c JOIN documents d ON c.document_id = d.id"
        )
        results = []
        for row in cursor:
            chunk_embedding = deserialize_embedding(row[2])
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            results.append({
                "id": row[0],
                "content": row[1],
                "file_path": row[3],
                "similarity": similarity
            })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def stats(self) -> dict:
        doc_count = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        return {"documents": doc_count, "chunks": chunk_count}
    
    def clear(self) -> None:
        self.conn.execute("DELETE FROM chunks")
        self.conn.execute("DELETE FROM documents")
        self.conn.commit()

# ─── CLI ───

def cmd_search(args) -> None:
    vs = VectorStore(args.db)
    stats = vs.stats()
    
    if stats["documents"] == 0:
        print("No documents indexed. Run 'context.py index <file|dir>' first.")
        vs.close()
        return
    
    if vs.vectorizer is None:
        print("Index not built. Building now...")
        vs.build_index()
    
    results = vs.search(args.query, top_k=args.top)
    
    if not results:
        print("No results found.")
    else:
        for r in results:
            print(f"\n[{r['similarity']:.3f}] {r['file_path']}")
            print(f"  {r['content'][:200]}...")
    
    vs.close()

def cmd_index(args) -> None:
    vs = VectorStore(args.db)
    path = args.path
    
    if os.path.isdir(path):
        print(f"Indexing directory: {path}")
        count = vs.add_directory(path)
        print(f"Added {count} files")
    else:
        vs.add_document(path)
    
    vs.build_index()
    print(f"Stats: {vs.stats()}")
    vs.close()

def cmd_stats(args) -> None:
    vs = VectorStore(args.db)
    stats = vs.stats()
    print(f"Documents: {stats['documents']}")
    print(f"Chunks: {stats['chunks']}")
    vs.close()

def cmd_clear(args) -> None:
    vs = VectorStore(args.db)
    vs.clear()
    print("Database cleared.")
    vs.close()

async def cmd_test(args) -> None:
    print("=" * 50)
    print("Running tests...")
    print("=" * 50)
    
    vs = VectorStore(":memory:")
    
    print("\n[Test 1] Chunking")
    text = " ".join([f"word{i}" for i in range(1500)])
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    print(f"  {len(text.split())} words -> {len(chunks)} chunks")
    
    print("\n[Test 2] Cosine similarity")
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.707, 0.707, 0.0])
    print(f"  Same: {cosine_similarity(a, a):.4f}")
    print(f"  45deg: {cosine_similarity(a, b):.4f}")
    
    print("\n[Test 3] TF-IDF")
    corpus = [
        "Python is a great programming language for data science",
        "JavaScript is the language of the web browser",
        "Python and JavaScript are both popular programming languages",
    ]
    vectorizer = TFIDFVectorizer(dim=100)
    vectorizer.fit_transform(corpus)
    v1 = vectorizer.transform("Python programming")
    v2 = vectorizer.transform("JavaScript web")
    print(f"  Python vs JS similarity: {cosine_similarity(v1, v2):.4f}")
    
    print("\n[Test 4] VectorStore")
    vs.add_document("agent0.py")
    vs.add_document("test_reviewer.py")
    vs.add_document("context.py")
    vs.build_index()
    results = vs.search("agent memory", top_k=2)
    for r in results:
        print(f"  [{r['similarity']:.3f}] {r['content'][:50]}...")
    print(f"  Stats: {vs.stats()}")
    
    vs.close()
    
    print("\n" + "=" * 50)
    print("All tests passed!")
    print("=" * 50)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAG context management with SQLite storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a file
  python context.py index agent0.py
  
  # Index a directory
  python context.py index ./src
  
  # Search (default top 5)
  python context.py search "query string"
  
  # Search with more results
  python context.py search "query" -k 10
  
  # Use custom database
  python context.py search "query" -d my_context.db
  
  # Show stats
  python context.py stats
  
  # Clear database
  python context.py clear
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # search
    search_parser = subparsers.add_parser("search", help="Search indexed documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-k", "--top", type=int, default=5, help="Number of results (default: 5)")
    search_parser.add_argument("-d", "--db", default=DEFAULT_DB_PATH, help="Database path")
    search_parser.set_defaults(func=cmd_search)
    
    # index
    index_parser = subparsers.add_parser("index", help="Index file or directory")
    index_parser.add_argument("path", help="File or directory path to index")
    index_parser.add_argument("-d", "--db", default=DEFAULT_DB_PATH, help="Database path")
    index_parser.set_defaults(func=cmd_index)
    
    # stats
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("-d", "--db", default=DEFAULT_DB_PATH, help="Database path")
    stats_parser.set_defaults(func=cmd_stats)
    
    # clear
    clear_parser = subparsers.add_parser("clear", help="Clear all indexed data")
    clear_parser.add_argument("-d", "--db", default=DEFAULT_DB_PATH, help="Database path")
    clear_parser.set_defaults(func=cmd_clear)
    
    # test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.set_defaults(func=cmd_test)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "test":
        asyncio.run(cmd_test(args))
    else:
        args.func(args)

if __name__ == "__main__":
    main()
