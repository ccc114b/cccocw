"""
AIL Memory - 記憶機制模組
提供長期記憶、上下文管理功能
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MemoryEntry:
    """記憶條目"""
    key: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5
    
    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "importance": self.importance
        }


class Memory:
    """
    AI 記憶體管理器
    
    用法:
        memory = Memory()
        memory.remember("user_name", "Alice")
        memory.remember("preferences", {"theme": "dark"}, tags=["user", "config"])
        
        name = memory.recall("user_name")
        all_user_memories = memory.recall_by_tag("user")
    """
    
    def __init__(self, max_size: int = 1000):
        self._store: Dict[str, MemoryEntry] = {}
        self._max_size = max_size
    
    def remember(
        self, 
        key: str, 
        value: Any, 
        tags: List[str] = None,
        importance: float = 0.5
    ) -> None:
        """存儲記憶"""
        if len(self._store) >= self._max_size:
            self._evict_low_importance()
        
        entry = MemoryEntry(
            key=key,
            value=value,
            tags=tags or [],
            importance=importance
        )
        self._store[key] = entry
    
    def recall(self, key: str, default: Any = None) -> Any:
        """回憶特定記憶"""
        entry = self._store.get(key)
        return entry.value if entry else default
    
    def recall_by_tag(self, tag: str) -> List[MemoryEntry]:
        """透過標籤回憶"""
        return [
            entry for entry in self._store.values()
            if tag in entry.tags
        ]
    
    def recall_recent(self, n: int = 10) -> List[MemoryEntry]:
        """回憶最近的記憶"""
        sorted_entries = sorted(
            self._store.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_entries[:n]
    
    def forget(self, key: str) -> bool:
        """忘記特定記憶"""
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def clear(self) -> None:
        """清除所有記憶"""
        self._store.clear()
    
    def _evict_low_importance(self) -> None:
        """移除最不重要的記憶"""
        if not self._store:
            return
        
        lowest = min(self._store.values(), key=lambda e: e.importance)
        del self._store[lowest.key]
    
    def __len__(self) -> int:
        return len(self._store)
    
    def __repr__(self) -> str:
        return f"Memory({len(self._store)} entries)"


class ContextWindow:
    """
    上下文窗口管理器
    
    用法:
        ctx = ContextWindow(max_tokens=4000)
        ctx.add_message("user", "你好")
        ctx.add_message("assistant", "你好，有什麼可以幫你？")
        
        context = ctx.get_context()
    """
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self._messages: List[Dict[str, str]] = []
        self._token_count = 0
    
    def add_message(self, role: str, content: str, tokens: int = None) -> None:
        """添加訊息"""
        if tokens is None:
            tokens = len(content) // 4
        
        message = {"role": role, "content": content}
        self._messages.append(message)
        self._token_count += tokens
        
        while self._token_count > self.max_tokens and len(self._messages) > 1:
            removed = self._messages.pop(0)
            self._token_count -= removed.get("_tokens", len(removed["content"]) // 4)
    
    def get_context(self) -> List[Dict[str, str]]:
        """取得上下文"""
        return self._messages.copy()
    
    def clear(self) -> None:
        """清除上下文"""
        self._messages.clear()
        self._token_count = 0
    
    def __len__(self) -> int:
        return len(self._messages)
