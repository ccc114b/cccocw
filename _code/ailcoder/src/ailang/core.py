"""
AIL Core - 核心功能模組
包含 intent, agent, tool, maybe 等 AI 專屬功能
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from functools import wraps
import json


_current_intent: Optional[str] = None
_memory_store: Dict[str, Any] = {}


def intent(description: str) -> Callable:
    """
    意圖宣告裝飾器
    
    用法:
        @intent("翻譯這段文字")
        def translate(text):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            global _current_intent
            _current_intent = description
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                _current_intent = None
        
        wrapper._ail_intent = description
        return wrapper
    
    return decorator


def get_current_intent() -> Optional[str]:
    """取得當前意圖"""
    return _current_intent


@dataclass
class Tool:
    """工具定義"""
    name: str
    func: Callable
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    async def call(self, **kwargs) -> Any:
        """調用工具"""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)


class ToolRegistry:
    """工具註冊中心"""
    _tools: Dict[str, Tool] = {}
    
    @classmethod
    def register(cls, name: str = None):
        """裝飾器：註冊工具"""
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            cls._tools[tool_name] = Tool(
                name=tool_name,
                func=func,
                description=func.__doc__ or ""
            )
            return func
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Optional[Tool]:
        """取得工具"""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> List[str]:
        """列出所有工具"""
        return list(cls._tools.keys())


async def tool(name: str = None, **params):
    """
    調用工具
    
    用法:
        result = await tool("search", query="天氣")
    """
    tool_name = name or params.get('_tool_name')
    if not tool_name:
        raise ValueError("tool name is required")
    
    t = ToolRegistry.get(tool_name)
    if not t:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    # 合併參數
    all_params = {**params}
    return await t.call(**all_params)


class Agent:
    """
    Agent 代理
    
    用法:
        researcher = Agent("researcher")
        result = await researcher(task="找AI新聞")
    """
    
    def __init__(
        self, 
        name: str, 
        model: str = "MiniMax-M2.5",
        system_prompt: str = "",
        use_minimax: bool = True,
        api_key: str = None
    ):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt or f"You are {name}, a helpful AI assistant."
        self._history: List[Dict] = []
        self._use_minimax = use_minimax
        
        if use_minimax:
            try:
                from .llm import MiniMaxAgent as RealAgent, get_client
                # 傳入全局 client
                self._real_agent = RealAgent(name, api_key=api_key, model=model, system_prompt=self.system_prompt, client=get_client())
            except ImportError:
                self._real_agent = None
        else:
            self._real_agent = None
    
    async def __call__(self, task: str, **kwargs) -> str:
        """執行任務"""
        intent = get_current_intent()
        full_task = f"[Intent: {intent}] {task}" if intent else task
        
        message = {
            "role": "user", 
            "content": full_task,
            "intent": intent
        }
        self._history.append(message)
        
        # 如果有 MiniMax client，調用真實 API
        if self._real_agent:
            result = await self._real_agent(full_task)
            # 同步歷史
            for msg in self._real_agent.history()[-2:]:
                self._history.append(msg)
        else:
            # 模擬結果
            result = f"[{self.name}] 處理任務: {task}"
        
        self._history.append({"role": "assistant", "content": result})
        return result
    
    def history(self) -> List[Dict]:
        """取得對話歷史"""
        return self._history.copy()


async def agent(name: str, **kwargs) -> str:
    """
    快速創建並調用 Agent
    
    用法:
        result = await agent("researcher", task="找最新AI新聞")
    """
    a = Agent(name)
    return await a(kwargs.get("task", ""))


def remember(key: str, value: Any = None):
    """
    記憶：存儲資訊到長期記憶
    
    用法:
        remember("user_preferences", {"theme": "dark"})
        # 或作為裝飾器
        @remember("cache_result")
        def expensive_operation():
            ...
    """
    global _memory_store
    
    if callable(key):
        # 作為裝飾器使用
        func = key
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            _memory_store[func.__name__] = result
            return result
        return wrapper
    
    if value is not None:
        _memory_store[key] = value
        return value
    
    # 返回記憶的值
    return _memory_store.get(key)


def recall(key: str, default: Any = None) -> Any:
    """
    回憶：從記憶中取得資訊
    
    用法:
        prefs = recall("user_preferences", default={})
    """
    return _memory_store.get(key, default)


def clear_memory():
    """清除所有記憶"""
    global _memory_store
    _memory_store = {}


class Uncertain:
    """
    不確定性結果包裝器
    
    用法:
        result = maybe(uncertain_operation())
        if result.is_uncertain:
            print("需要更多資訊")
    """
    
    def __init__(
        self, 
        value: Any, 
        confidence: float = 0.5,
        reason: str = ""
    ):
        self.value = value
        self.confidence = max(0.0, min(1.0, confidence))
        self.reason = reason
    
    @property
    def is_uncertain(self) -> bool:
        return self.confidence < 0.7
    
    @property
    def is_certain(self) -> bool:
        return self.confidence >= 0.7
    
    def __repr__(self):
        return f"Uncertain(value={self.value}, confidence={self.confidence})"


def maybe(result: Any, confidence: float = 0.5, reason: str = "") -> Uncertain:
    """
    將結果包裝為不確定性結果
    
    用法:
        result = maybe(llm_output, confidence=0.85)
        if result.is_certain:
            print(result.value)
    """
    return Uncertain(result, confidence, reason)


async def gather_all(*tasks):
    """
    並行執行多個任務
    
    用法:
        results = await gather_all(
            agent("researcher", task="找蘋果"),
            agent("researcher", task="找香蕉")
        )
    """
    return await asyncio.gather(*tasks)
