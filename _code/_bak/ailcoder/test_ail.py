#!/usr/bin/env python3
"""使用 AIL 框架測試完整流程"""
import asyncio
import sys
sys.path.insert(0, 'src')

from ailang.llm import OllamaClient

async def main():
    print("測試 AIL OllamaClient...")
    
    client = OllamaClient(model="minimax-m2.5:cloud")
    
    # 測試問問題
    result = await client.chat(
        "用繁體中文說 '你好，請幫我建立一個 hello.py'",
        system_prompt="你是 AIExecutor，直接輸出程式碼"
    )
    print(f"結果: {result[:200]}...")

asyncio.run(main())
