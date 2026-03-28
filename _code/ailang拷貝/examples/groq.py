"""
AIL + Groq (免費 LLM API) 使用範例
"""

import asyncio
from ailang import init_minimax, chat, Agent, intent


async def main():
    """使用 Groq 免費 API"""
    
    # 從環境變數讀取 API Key
    import os
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        print("⚠️  請到 https://console.groq.com 申請免費 API Key")
        print("   Groq 免費額度足夠開發測試使用")
        print()
        print("=== 模擬模式 ===")
        
        agent = Agent("researcher", use_minimax=False)
        result = await agent(task="介紹 AI 是什麼")
        print(f"Agent: {result}")
        return
    
    # Groq 使用 OpenAI 兼容格式
    from ailang.llm import init_minimax
    init_minimax(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant"
    )
    print("✓ Groq 初始化成功")
    print("模型: llama-3.1-8b-instant")
    
    # 聊天測試
    print("\n=== 聊天測試 ===")
    response = await chat("你好，請用中文自我介紹")
    print(f"Groq: {response}")
    
    # Agent 測試
    print("\n=== Agent 測試 ===")
    researcher = Agent("researcher")
    result = await researcher(task="用三句話介紹人工智慧")
    print(f"Agent: {result}")


if __name__ == "__main__":
    asyncio.run(main())
