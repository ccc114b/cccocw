"""
AIL Examples - 使用範例
"""

import asyncio
from ailang import (
    intent, agent, tool, remember, recall,
    maybe, Uncertain,
    Memory, Vector, cosine_similarity
)


# ============ 1. Intent 意圖宣告 ============

@intent("翻譯用戶輸入的文字")
async def translate(text: str, to_lang: str) -> str:
    """翻譯功能"""
    # 實際應該調用翻譯 API
    return f"[翻譯] {text} -> {to_lang}"


# ============ 2. Agent 代理 ============

async def demo_agent():
    """Agent 使用範例"""
    print("=== Agent Demo ===")
    
    # 創建並調用 Agent
    from ailang import Agent
    researcher = Agent("researcher")
    result = await researcher(task="用一句話介紹 AI 是什麼")
    print(f"結果: {result}")


# ============ 3. Tool 工具 ============

from ailang.core import ToolRegistry

@ToolRegistry.register("search")
async def search(query: str) -> str:
    """搜索工具"""
    return f"搜索結果: {query}"


@ToolRegistry.register("calculate")
async def calculate(expression: str) -> float:
    """計算工具"""
    return eval(expression)


async def demo_tool():
    """Tool 使用範例"""
    print("\n=== Tool Demo ===")
    
    # 調用工具
    from ailang.core import tool
    result = await tool("search", query="天氣")
    print(f"結果: {result}")
    
    # 計算
    result = await tool("calculate", expression="2+2")
    print(f"結果: {result}")


# ============ 4. Memory 記憶 ============

def demo_memory():
    """Memory 使用範例"""
    print("\n=== Memory Demo ===")
    
    memory = Memory()
    
    # 存儲記憶
    memory.remember("user_name", "Alice", tags=["user", "personal"])
    memory.remember("preferences", {"theme": "dark", "language": "zh-TW"}, tags=["user", "config"])
    
    # 回憶
    name = memory.recall("user_name")
    print(f"用戶名: {name}")
    
    # 透過標籤回憶
    user_data = memory.recall_by_tag("user")
    print(f"用戶相關記憶: {len(user_data)} 條")


# ============ 5. Vector 向量 ============

def demo_vector():
    """Vector 使用範例"""
    print("\n=== Vector Demo ===")
    
    # 創建向量
    v1 = Vector([0.1, 0.5, 0.9])
    v2 = Vector([0.2, 0.4, 0.8])
    
    # 餘弦相似度
    sim = cosine_similarity(v1, v2)
    print(f"相似度: {sim:.4f}")
    
    # 歐氏距離
    dist = v1.euclidean_distance(v2)
    print(f"距離: {dist:.4f}")


# ============ 6. Uncertain 不確定性 ============

def demo_uncertain():
    """Uncertain 使用範例"""
    print("\n=== Uncertain Demo ===")
    
    # 高置信度
    result1 = maybe("今天會下雨", confidence=0.85)
    print(f"結果: {result1.value}, 確定: {result1.is_certain}")
    
    # 低置信度
    result2 = maybe("可能是蘋果", confidence=0.4)
    print(f"結果: {result2.value}, 確定: {result2.is_uncertain}")


# ============ 主程式 ============

async def main():
    """執行所有範例"""
    print("AIL (AI Language) Python 擴充套件範例\n")
    
    # 從環境變數讀取 API Key
    import os
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        print("⚠️  請設定環境變數 OPENROUTER_API_KEY")
        print("   在 .zshrc 中加入: export OPENROUTER_API_KEY='your-key'")
        return
    
    # 初始化 OpenRouter 免費模型
    from ailang import init_openrouter
    init_openrouter(api_key, model="openrouter/free")
    
    await demo_agent()
    await demo_tool()
    demo_memory()
    demo_vector()
    demo_uncertain()
    
    print("\n=== 範例完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
