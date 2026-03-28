"""
AIL (AI Language) - 為 AI 設計的 Python 擴充套件
讓人類與 AI 的互動更自然
"""

from .core import intent, agent, tool, remember, recall, maybe, Uncertain, Agent
from .memory import Memory
from .vector import Vector, cosine_similarity
from .llm import init_minimax, init_openrouter, chat, MiniMaxClient
from .explore import explore, explore_all, Explorer, VoteStrategy, ExplorationResult
from .think import think, ThinkStream, Thought, ThoughtType, Reasoner
from .goal import goal, GoalContext, GoalTracker, Goal, GoalStatus, Priority, get_tracker

__version__ = "0.1.0"
__all__ = [
    # Core
    "intent",
    "agent",
    "tool",
    "remember", 
    "recall",
    "maybe",
    "Uncertain",
    "Agent",
    # Memory & Vector
    "Memory",
    "Vector",
    "cosine_similarity",
    # LLM
    "init_minimax",
    "init_openrouter",
    "chat",
    "MiniMaxClient",
    # Explore
    "explore",
    "explore_all",
    "Explorer",
    "VoteStrategy",
    "ExplorationResult",
    # Think
    "think",
    "ThinkStream",
    "Thought",
    "ThoughtType",
    "Reasoner",
    # Goal
    "goal",
    "GoalContext",
    "GoalTracker",
    "Goal",
    "GoalStatus",
    "Priority",
    "get_tracker",
]
