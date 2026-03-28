"""
AIL Goal - 目標宣告
讓 AI 程式以「目標優先」的方式運作
"""

import asyncio
from typing import Any, Callable, Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from functools import wraps


class GoalStatus(Enum):
    """目標狀態"""
    PENDING = "pending"       # 等待中
    RUNNING = "running"       # 執行中
    COMPLETED = "completed"   # 完成
    FAILED = "failed"         # 失敗
    CANCELLED = "cancelled"   # 取消


class Priority(Enum):
    """優先級"""
    CRITICAL = 3
    HIGH = 2
    NORMAL = 1
    LOW = 0


@dataclass
class Goal:
    """目標"""
    description: str
    status: GoalStatus = GoalStatus.PENDING
    priority: Priority = Priority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    subgoals: List["Goal"] = field(default_factory=list)
    
    @property
    def is_done(self) -> bool:
        return self.status in [GoalStatus.COMPLETED, GoalStatus.FAILED, GoalStatus.CANCELLED]
    
    @property
    def duration(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None


class GoalContext:
    """
    目標上下文管理器
    
    用法:
        async with goal("翻譯這篇文章") as g:
            g.priority = Priority.HIGH
            result = await translate()
            g.complete(result)
    """
    
    def __init__(self, description: str, **metadata):
        self.goal = Goal(description=description, metadata=metadata)
        self._parent: Optional[GoalContext] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.goal.status = GoalStatus.FAILED
            self.goal.error = str(exc_val)
        self.goal.completed_at = datetime.now()
        return False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)
        return False
    
    def complete(self, result: Any):
        """標記完成"""
        self.goal.result = result
        self.goal.status = GoalStatus.COMPLETED
        self.goal.completed_at = datetime.now()
    
    def fail(self, error: str):
        """標記失敗"""
        self.goal.error = error
        self.goal.status = GoalStatus.FAILED
        self.goal.completed_at = datetime.now()
    
    def add_subgoal(self, description: str) -> "GoalContext":
        """添加子目標"""
        sub = Goal(description)
        self.goal.subgoals.append(sub.goal)
        return sub
    
    def report(self) -> str:
        """報告目標狀態"""
        status_icon = {
            GoalStatus.PENDING: "⏳",
            GoalStatus.RUNNING: "🔄",
            GoalStatus.COMPLETED: "✅",
            GoalStatus.FAILED: "❌",
            GoalStatus.CANCELLED: "🚫"
        }
        
        icon = status_icon.get(self.goal.status, "❓")
        duration = f"{self.goal.duration:.2f}s" if self.goal.duration else "N/A"
        
        lines = [
            f"{icon} 目標: {self.goal.description}",
            f"   狀態: {self.goal.status.value}",
            f"   耗時: {duration}"
        ]
        
        if self.goal.subgoals:
            lines.append("   子目標:")
            for sg in self.goal.subgoals:
                lines.append(f"     - {sg.description}: {sg.status.value}")
        
        return "\n".join(lines)


class GoalTracker:
    """
    目標追蹤器
    
    用法:
        tracker = GoalTracker()
        
        # 聲明目標
        await tracker.declare("用戶想要翻譯文章")
        
        # 執行
        result = await do_work()
        
        # 追蹤結果
        tracker.track(cost=0.01, tokens=1000, tools_used=["search", "translate"])
    """
    
    def __init__(self):
        self.current_goal: Optional[Goal] = None
        self.goal_history: List[Goal] = []
        self._stats = {
            "total_goals": 0,
            "completed_goals": 0,
            "failed_goals": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "tools_used": set()
        }
    
    async def declare(
        self, 
        goal: str, 
        priority: Priority = Priority.NORMAL,
        context: Dict = None
    ) -> Goal:
        """聲明目標"""
        self.current_goal = Goal(
            description=goal,
            priority=priority,
            metadata=context or {}
        )
        self.current_goal.status = GoalStatus.RUNNING
        self._stats["total_goals"] += 1
        
        return self.current_goal
    
    def complete(self, result: Any):
        """完成目標"""
        if not self.current_goal:
            return
        
        self.current_goal.result = result
        self.current_goal.status = GoalStatus.COMPLETED
        self.current_goal.completed_at = datetime.now()
        
        self.goal_history.append(self.current_goal)
        self._stats["completed_goals"] += 1
        self.current_goal = None
    
    def fail(self, error: str):
        """目標失敗"""
        if not self.current_goal:
            return
        
        self.current_goal.error = error
        self.current_goal.status = GoalStatus.FAILED
        self.current_goal.completed_at = datetime.now()
        
        self.goal_history.append(self.current_goal)
        self._stats["failed_goals"] += 1
        self.current_goal = None
    
    def track(self, **metrics):
        """追蹤指標"""
        if "tokens" in metrics:
            self._stats["total_tokens"] += metrics["tokens"]
        if "cost" in metrics:
            self._stats["total_cost"] += metrics["cost"]
        if "tool" in metrics:
            self._stats["tools_used"].add(metrics["tool"])
    
    def get_stats(self) -> Dict:
        """取得統計"""
        return {
            **self._stats,
            "tools_used": list(self._stats["tools_used"]),
            "success_rate": (
                self._stats["completed_goals"] / self._stats["total_goals"]
                if self._stats["total_goals"] > 0 else 0
            )
        }
    
    def summary(self) -> str:
        """取得摘要"""
        stats = self.get_stats()
        return f"""
目標統計:
  總目標: {stats['total_goals']}
  完成: {stats['completed_goals']}
  失敗: {stats['failed_goals']}
  成功率: {stats['success_rate']*100:.1f}%
  消耗代幣: {stats['total_tokens']}
  消耗費用: ${stats['total_cost']:.4f}
  使用工具: {', '.join(stats['tools_used'])}
"""


# 全域追�器
_global_tracker = GoalTracker()


def goal(description: str = None, **context):
    """
    目標宣告裝飾器/上下文
    
    用法 (裝飾器):
        @goal()
        async def translate():
            ...
    
    用法 (上下文):
        async with goal("翻譯文章") as g:
            g.priority = Priority.HIGH
            result = await translate()
            g.complete(result)
    """
    # 如果是裝飾器用法 (@goal())
    if description is None:
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                func_name = getattr(func, '__name__', 'anonymous')
                async with GoalContext(description=f"執行 {func_name}", **context) as g:
                    try:
                        result = await func(*args, **kwargs)
                        g.complete(result)
                        return result
                    except Exception as e:
                        g.fail(str(e))
                        raise
            return wrapper
        return decorator
    
    # 如果是直接調用
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with GoalContext(description=description, **context) as g:
                try:
                    result = await func(*args, **kwargs)
                    g.complete(result)
                    return result
                except Exception as e:
                    g.fail(str(e))
                    raise
        return wrapper
    
    # 如果第一個參數是函數（@goal 不帶括號）
    if callable(description):
        func = description
        func_name = getattr(func, '__name__', 'anonymous')
        return decorator(func)
    
    return GoalContext(description=description, **context)


def get_tracker() -> GoalTracker:
    """取得全域追蹤器"""
    return _global_tracker


def track_metrics(**metrics):
    """快速追蹤指標"""
    _global_tracker.track(**metrics)


def goal_summary():
    """快速取得摘要"""
    return _global_tracker.summary()
