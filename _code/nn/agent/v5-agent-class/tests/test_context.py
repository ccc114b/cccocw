#!/usr/bin/env python3
# tests/test_context.py - pytest tests for context.py

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from context import (
    init_db,
    chunk_text,
    TFIDFVectorizer,
    cosine_similarity,
    VectorStore,
)


class TestChunkText:
    def test_empty_text(self):
        assert chunk_text("") == []

    def test_short_text(self):
        chunks = chunk_text("hello world")
        assert len(chunks) == 1
        assert chunks[0] == "hello world"

    def test_exact_chunks(self):
        words = " ".join([f"word{i}" for i in range(1000)])
        chunks = chunk_text(words, chunk_size=500, overlap=50)
        assert len(chunks) == 3  # 0-500, 450-950, 900-999

    def test_overlapping_chunks(self):
        chunks = chunk_text("a b c d e f g h", chunk_size=3, overlap=1)
        assert len(chunks) == 4  # a b c, c d e, e f g, g h
        assert chunks[0] == "a b c"
        assert chunks[1] == "c d e"
        assert chunks[2] == "e f g"

    def test_large_text(self):
        words = " ".join([f"word{i}" for i in range(1500)])
        chunks = chunk_text(words, chunk_size=500, overlap=50)
        assert len(chunks) == 4
        assert chunks[0].startswith("word0")
        assert chunks[-1].endswith("word1499")


class TestTFIDFVectorizer:
    def test_fit_transform(self):
        corpus = [
            "python programming language",
            "javascript web development",
            "python and javascript both programming",
        ]
        vectorizer = TFIDFVectorizer(dim=50)
        vectors = vectorizer.fit_transform(corpus)
        assert vectors.shape == (3, 50)
        assert len(vectorizer.vocab) <= 50

    def test_transform(self):
        corpus = ["python is great", "javascript is great"]
        vectorizer = TFIDFVectorizer(dim=100)
        vectorizer.fit_transform(corpus)
        vec = vectorizer.transform("python programming")
        assert vec.shape == (100,)

    def test_same_text_similarity(self):
        corpus = ["python programming", "java programming"]
        vectorizer = TFIDFVectorizer(dim=100)
        vectorizer.fit_transform(corpus)
        v1 = vectorizer.transform("python")
        v2 = vectorizer.transform("python")
        sim = cosine_similarity(v1, v2)
        assert sim == pytest.approx(1.0, abs=0.01)

    def test_different_text_similarity(self):
        corpus = ["python programming", "web development"]
        vectorizer = TFIDFVectorizer(dim=100)
        vectorizer.fit_transform(corpus)
        v1 = vectorizer.transform("python")
        v2 = vectorizer.transform("web")
        sim = cosine_similarity(v1, v2)
        assert sim < 0.5

    def test_tokenize(self):
        vectorizer = TFIDFVectorizer()
        tokens = vectorizer._tokenize("Hello WORLD! Python3.0 is great.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "python3" in tokens  # Python3.0 -> python3
        assert "great" in tokens
        assert "is" not in tokens  # too short


class TestCosineSimilarity:
    def test_same_vector(self):
        import numpy as np
        a = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity(a, a) == pytest.approx(1.0)

    def test_orthogonal(self):
        import numpy as np
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_45_degrees(self):
        import numpy as np
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.707, 0.707, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(0.707, abs=0.01)

    def test_opposite(self):
        import numpy as np
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([-1.0, 0.0, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(-1.0)


class TestInitDb:
    def test_create_in_memory(self):
        conn = init_db(":memory:")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor]
        assert "documents" in tables
        assert "chunks" in tables
        conn.close()

    def test_create_file_db(self, tmp_path):
        db_path = tmp_path / "test.db"
        conn = init_db(str(db_path))
        assert db_path.exists()
        conn.close()


class TestVectorStore:
    def test_init(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))
        assert vs.conn is not None
        assert vs.vectorizer is None
        vs.close()

    def test_stats_empty(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))
        stats = vs.stats()
        assert stats["documents"] == 0
        assert stats["chunks"] == 0
        vs.close()

    def test_add_document(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world python programming")

        doc_id = vs.add_document(str(test_file))
        assert doc_id > 0
        assert vs.stats()["documents"] == 1
        assert vs.stats()["chunks"] > 0
        vs.close()

    def test_add_same_document_skip(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world python programming")

        vs.add_document(str(test_file))
        stats_before = vs.stats()

        vs.add_document(str(test_file))
        stats_after = vs.stats()

        assert stats_before == stats_after
        vs.close()

    def test_add_modified_document(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        vs.add_document(str(test_file))
        stats1 = vs.stats()

        test_file.write_text("modified content")
        vs.add_document(str(test_file))
        stats2 = vs.stats()

        assert stats1["chunks"] == stats2["chunks"]
        vs.close()

    def test_add_nonexistent_file(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        with pytest.raises(FileNotFoundError):
            vs.add_document(str(tmp_path / "nonexistent.txt"))
        vs.close()

    def test_build_index(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        test_file = tmp_path / "test.txt"
        test_file.write_text("python programming " * 100)

        vs.add_document(str(test_file))
        vs.build_index()

        assert vs.vectorizer is not None
        vs.close()

    def test_search(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        test_file = tmp_path / "test.txt"
        test_file.write_text("python is a great programming language for data science")

        vs.add_document(str(test_file))
        vs.build_index()

        results = vs.search("python programming", top_k=5)

        assert len(results) > 0
        assert all("content" in r for r in results)
        assert all("similarity" in r for r in results)
        assert all("file_path" in r for r in results)
        vs.close()

    def test_search_no_index(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        test_file = tmp_path / "test.txt"
        test_file.write_text("python programming " * 100)
        vs.add_document(str(test_file))

        results = vs.search("python")
        assert len(results) > 0
        vs.close()

    def test_search_returns_sorted(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        file1 = tmp_path / "python.txt"
        file1.write_text("python programming " * 100)

        file2 = tmp_path / "java.txt"
        file2.write_text("java programming " * 100)

        vs.add_document(str(file1))
        vs.add_document(str(file2))
        vs.build_index()

        results = vs.search("python", top_k=2)

        assert len(results) == 2
        assert results[0]["similarity"] >= results[1]["similarity"]
        vs.close()

    def test_clear(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world python")

        vs.add_document(str(test_file))
        vs.build_index()
        assert vs.stats()["documents"] > 0

        vs.clear()
        stats = vs.stats()
        assert stats["documents"] == 0
        assert stats["chunks"] == 0
        vs.close()

    def test_add_directory(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        (tmp_path / "file1.txt").write_text("python code")
        (tmp_path / "file2.txt").write_text("java code")
        (tmp_path / "file3.md").write_text("markdown content")

        count = vs.add_directory(str(tmp_path), extensions=['.txt', '.md'])
        assert count == 3
        assert vs.stats()["documents"] == 3
        vs.close()

    def test_add_directory_excludes_special(self, tmp_path):
        db_path = tmp_path / "test.db"
        vs = VectorStore(str(db_path))

        (tmp_path / "file1.txt").write_text("valid")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "bad.txt").write_text("should be excluded")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "bad.py").write_text("should be excluded")

        count = vs.add_directory(str(tmp_path))
        assert count == 1
        vs.close()


class TestVectorStoreIntegration:
    def test_full_workflow(self, tmp_path):
        db_path = tmp_path / "context.db"
        vs = VectorStore(str(db_path))

        file1 = tmp_path / "python.txt"
        file1.write_text("Python is a programming language. Python is great for AI.")

        file2 = tmp_path / "java.txt"
        file2.write_text("Java is a programming language. Java runs on JVM.")

        vs.add_document(str(file1))
        vs.add_document(str(file2))
        vs.build_index()

        results = vs.search("python AI", top_k=2)
        assert len(results) >= 1
        assert results[0]["file_path"].endswith("python.txt")

        vs.clear()
        assert vs.stats()["documents"] == 0

        vs.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
