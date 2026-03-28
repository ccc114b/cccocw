"""
AIL Think - 流式思考
讓 AI 一邊思考一邊行動，類似人類的思考過程
"""

import asyncio
from typing import AsyncGenerator, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re


class ThoughtType(Enum):
    """思考類型"""
    REASONING = "reasoning"     # 推理過程
    OBSERVATION = "observation" # 觀察發現
    HYPOTHESIS = "hypothesis"   # 假設
    PLAN = "plan"               # 計劃
    CHECK = "check"             # 檢查
    CORRECTION = "correction"   # 修正
    CONCLUSION = "conclusion"   # 結論


@dataclass
class Thought:
    """思考節點"""
    type: ThoughtType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    parent: Optional["Thought"] = None
    metadata: dict = field(default_factory=dict)


class ThinkStream:
    """
    思考流管理器
    
    用法:
        async for thought in think("解決這個問題"):
            print(f"[{thought.type.value}] {thought.content}")
    """
    
    def __init__(self):
        self.thoughts: List[Thought] = []
        self._stream_queue: asyncio.Queue = asyncio.Queue()
        self._current: Optional[Thought] = None
    
    def say(self, content: str, type: ThoughtType = ThoughtType.REASONING):
        """新增一個思考"""
        thought = Thought(
            type=type,
            content=content,
            parent=self._current
        )
        self.thoughts.append(thought)
        self._current = thought
        self._stream_queue.put_nowait(thought)
    
    def reason(self, content: str):
        """推理"""
        self.say(content, ThoughtType.REASONING)
    
    def observe(self, content: str):
        """觀察"""
        self.say(content, ThoughtType.OBSERVATION)
    
    def hypothesize(self, content: str):
        """假設"""
        self.say(content, ThoughtType.HYPOTHESIS)
    
    def plan(self, content: str):
        """計劃"""
        self.say(content, ThoughtType.PLAN)
    
    def check(self, content: str):
        """檢查"""
        self.say(content, ThoughtType.CHECK)
    
    def correct(self, content: str):
        """修正"""
        self.say(content, ThoughtType.CORRECTION)
    
    def conclude(self, content: str, confidence: float = 1.0):
        """結論"""
        thought = Thought(
            type=ThoughtType.CONCLUSION,
            content=content,
            confidence=confidence,
            parent=self._current
        )
        self.thoughts.append(thought)
        self._current = thought
        self._stream_queue.put_nowait(thought)
    
    def revise(self, old_thought: Thought, new_content: str):
        """修正之前的思考"""
        # 標記舊思考為已修正
        old_thought.metadata["revised"] = True
        old_thought.metadata["replacement"] = new_content
        
        # 新增修正後的思考
        self.correct(f"修正: {old_thought.content} → {new_content}")
    
    async def stream(self) -> AsyncGenerator[Thought, None]:
        """流式產出思考"""
        while not self._stream_queue.empty():
            yield await self._stream_queue.get()
    
    def get_path(self) -> List[Thought]:
        """取得思考路徑"""
        if not self.thoughts:
            return []
        
        # 從結論回溯
        path = []
        current = self.thoughts[-1]  # 最後一個是結論
        
        while current:
            path.insert(0, current)
            current = current.parent
        
        return path
    
    def summarize(self) -> str:
        """總結思考過程"""
        if not self.thoughts:
            return "無思考記錄"
        
        lines = ["思考過程:"]
        for t in self.thoughts:
            icon = {
                ThoughtType.REASONING: "🤔",
                ThoughtType.OBSERVATION: "👀",
                ThoughtType.HYPOTHESIS: "💡",
                ThoughtType.PLAN: "📋",
                ThoughtType.CHECK: "✅",
                ThoughtType.CORRECTION: "🔄",
                ThoughtType.CONCLUSION: "🎯"
            }.get(t.type, "💭")
            
            revised = " [已修正]" if t.metadata.get("revised") else ""
            lines.append(f"  {icon} {t.content}{revised}")
        
        return "\n".join(lines)


class Reasoner:
    """
    推理鏈管理器
    
    用法:
        result = await think("這個問題") do:
            .because("A是正确的")
            .but("B也可能是對的")
            .therefore("答案是X")
    """
    
    def __init__(self, problem: str):
        self.problem = problem
        self.premises: List[str] = []
        self.contradictions: List[str] = []
        self.conclusions: List[str] = []
        self.stream = ThinkStream()
    
    def because(self, premise: str):
        """因為..."""
        self.premises.append(premise)
        self.stream.reason(f"因為: {premise}")
        return self
    
    def but(self, contradiction: str):
        """但是..."""
        self.contradictions.append(contradiction)
        self.stream.observe(f"但是: {contradiction}")
        return self
    
    def therefore(self, conclusion: str, confidence: float = 0.8):
        """因此..."""
        self.conclusions.append(conclusion)
        self.stream.conclude(f"因此: {conclusion}", confidence)
        return self
    
    def verify(self, check: str):
        """驗證"""
        self.stream.check(f"驗證: {check}")
        return self
    
    def get_result(self) -> dict:
        """取得推理結果"""
        return {
            "problem": self.problem,
            "premises": self.premises,
            "contradictions": self.contradictions,
            "conclusions": self.conclusions,
            "thought_path": self.stream.get_path()
        }


# 裝飾器版：邊思考邊執行
def thinking(enabled: bool = True):
    """
    裝飾器：自動記錄思考過程
    
    用法:
        @thinking()
        async def solve_problem():
            # 自動記錄每一步
            step1 = await do_something()
            step2 = await do_another()
            return step2
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not enabled:
                return await func(*args, **kwargs)
            
            stream = ThinkStream()
            stream.reason(f"開始執行: {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                stream.conclude(f"完成: {func.__name__}")
                return result
            except Exception as e:
                stream.correct(f"發生錯誤: {e}")
                raise
        
        return wrapper
    return decorator


# 便捷函數
def think(problem: str) -> Reasoner:
    """
    開始一個思考鏈
    
    用法:
        result = think("這個問題") \
            .because("...") \
            .but("...") \
            .therefore("...")
    """
    return Reasoner(problem)


async def observe_and_adjust(observation: str, adjust_fn: Callable):
    """
    觀察並調整模式
    
    用法:
        result = await observe_and_adjust("結果不如預期", 
            lambda: 調整策略())
    """
    stream = ThinkStream()
    stream.observe(f"觀察: {observation}")
    
    adjustment = adjust_fn()
    if asyncio.iscoroutine(adjustment):
        adjustment = await adjustment
    
    stream.correct(f"調整: {adjustment}")
    return adjustment
