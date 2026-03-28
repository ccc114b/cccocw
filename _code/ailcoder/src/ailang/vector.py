"""
AIL Vector - 向量/嵌入操作模組
處理向量計算、相似度等 AI 基礎操作
"""

from typing import List, Union, Optional
import math


class Vector:
    """
    向量類
    
    用法:
        v1 = Vector([0.1, 0.5, 0.9])
        v2 = Vector([0.2, 0.4, 0.8])
        
        similarity = v1.cosine_similarity(v2)
        print(f"相似度: {similarity}")
    """
    
    def __init__(self, data: List[Union[int, float]]):
        self.data = list(data)
    
    @property
    def magnitude(self) -> float:
        """向量長度"""
        return math.sqrt(sum(x * x for x in self.data))
    
    def dot(self, other: "Vector") -> float:
        """點積"""
        if len(self.data) != len(other.data):
            raise ValueError("Vectors must have same dimension")
        return sum(a * b for a, b in zip(self.data, other.data))
    
    def cosine_similarity(self, other: "Vector") -> float:
        """餘弦相似度"""
        mag_product = self.magnitude * other.magnitude
        if mag_product == 0:
            return 0.0
        return self.dot(other) / mag_product
    
    def euclidean_distance(self, other: "Vector") -> float:
        """歐氏距離"""
        if len(self.data) != len(other.data):
            raise ValueError("Vectors must have same dimension")
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.data, other.data)))
    
    def normalize(self) -> "Vector":
        """歸一化"""
        mag = self.magnitude
        if mag == 0:
            return Vector([0.0] * len(self.data))
        return Vector([x / mag for x in self.data])
    
    def add(self, other: "Vector") -> "Vector":
        """向量加法"""
        if len(self.data) != len(other.data):
            raise ValueError("Vectors must have same dimension")
        return Vector([a + b for a, b in zip(self.data, other.data)])
    
    def scale(self, scalar: float) -> "Vector":
        """向量縮放"""
        return Vector([x * scalar for x in self.data])
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, index: int) -> float:
        return self.data[index]
    
    def __repr__(self) -> str:
        return f"Vector({self.data})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return self.data == other.data


def vector(data: List[Union[int, float]]) -> Vector:
    """
    向量工廠函數
    
    用法:
        v = vector([0.1, 0.5, 0.9])
    """
    return Vector(data)


def cosine_similarity(a: Vector, b: Vector) -> float:
    """
    計算兩個向量的餘弦相似度
    
    用法:
        sim = cosine_similarity(embedding_a, embedding_b)
    """
    return a.cosine_similarity(b)


def euclidean_distance(a: Vector, b: Vector) -> float:
    """計算歐氏距離"""
    return a.euclidean_distance(b)


class EmbeddingCache:
    """
    嵌入緩存
    
    用法:
        cache = EmbeddingCache()
        cache.store("hello", [0.1, 0.2, 0.3])
        vec = cache.get("hello")
    """
    
    def __init__(self):
        self._cache: dict = {}
    
    def store(self, text: str, embedding: List[float]) -> None:
        """存儲嵌入"""
        self._cache[text] = Vector(embedding)
    
    def get(self, text: str) -> Optional[Vector]:
        """取得嵌入"""
        return self._cache.get(text)
    
    def most_similar(self, query: Vector, top_k: int = 5) -> List[tuple]:
        """找最相似的"""
        similarities = [
            (text, query.cosine_similarity(vec))
            for text, vec in self._cache.items()
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def __len__(self) -> int:
        return len(self._cache)
    
    def clear(self) -> None:
        self._cache.clear()
