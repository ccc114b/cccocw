"""
AIL + OpenRouter (MiniMax M2.5 Free) 使用範例
"""

import asyncio
from ailang import init_openrouter, chat, Agent, intent


async def main():
    """使用 OpenRouter 上的免費 MiniMax M2.5"""
    
    print("=== AIL + OpenRouter (免費模型) ===")
    print()
    
    # 從環境變數讀取 API Key
    import os
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        print("⚠️  請到 https://openrouter.ai 申請免費 API Key")
        print("   目前使用模擬模式")
        print()
        print("=== 模擬模式 ===")
        
        agent = Agent("researcher", use_minimax=False)
        result = await agent(task="介紹 AI 是什麼")
        print(f"Agent: {result}")
        return
    
    # 初始化 OpenRouter - 使用免費路由模型
    # "openrouter/free" 會自動選擇最佳的免費模型
    init_openrouter(api_key, model="openrouter/free")
    print("✓ OpenRouter 初始化成功")
    print("模型: openrouter/free (自動選擇最佳免費模型)")
    
    # 直接聊天
    print("\n=== 聊天測試 ===")
    response = await chat("你好，請用中文自我介紹")
    print(f"MiniMax: {response}")
    
    # 使用 Agent
    print("\n=== Agent 測試 ===")
    researcher = Agent("researcher")
    result = await researcher(task="用三句話介紹人工智慧")
    print(f"Agent: {result}")


if __name__ == "__main__":
    asyncio.run(main())
