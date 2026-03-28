"""
AIL (AI Language) - 為 AI 設計的 Python 擴充套件
讓人類與 AI 的互動更自然
"""

from .core import intent, agent, tool, remember, recall, maybe, Uncertain, Agent
from .memory import Memory
from .vector import Vector, cosine_similarity
from .llm import init_minimax, init_openrouter, chat, MiniMaxClient

__version__ = "0.1.0"
__all__ = [
    "intent",
    "agent",
    "tool",
    "remember", 
    "recall",
    "maybe",
    "Uncertain",
    "Agent",
    "Memory",
    "Vector",
    "cosine_similarity",
    "init_minimax",
    "init_openrouter",
    "chat",
    "MiniMaxClient",
]
