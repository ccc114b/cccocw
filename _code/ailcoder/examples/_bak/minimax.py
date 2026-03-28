"""
AIL + MiniMax M2.5 使用範例
"""

import asyncio
from ailang import init_minimax, chat, Agent, intent


async def main():
    """使用 MiniMax M2.7 API"""
    
    # 從環境變數讀取 API Key
    import os
    api_key = os.environ.get("MINIMAX_API_KEY")
    
    # 使用 OpenCode 風格的 Anthropic 兼容端點
    base_url = "https://api.minimax.io/anthropic/v1"
    
    # 初始化 MiniMax
    init_minimax(api_key, base_url=base_url, model="MiniMax-M2.7")
    print("✓ MiniMax M2.7 (OpenCode 風格) 初始化成功")
    
    # 使用 chat 函數
    # 使用 Agent
    print("\n=== Agent 模式 ===")
    researcher = Agent("researcher")
    print(f"使用真實 MiniMax API...")
    result = await researcher(task="用三句話介紹什麼是人工智慧")
    print(f"Agent: {result}")
    
    # 使用意圖宣告
    print("\n=== 意圖宣告 ===")
    @intent("翻譯成英文")
    async def translate():
        return "Artificial intelligence is changing the world"
    
    translated = await translate()
    print(f"翻譯結果: {translated}")


if __name__ == "__main__":
    asyncio.run(main())
