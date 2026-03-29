#!/usr/bin/env python3
"""使用 Ollama API 直接測試"""
import asyncio
import json

async def main():
    print("測試 Ollama API...")
    
    import aiohttp
    async with aiohttp.ClientSession() as session:
        payload = {
            "model": "minimax-m2.5:cloud",
            "prompt": "說 '你好'",
            "stream": False
        }
        async with session.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            result = await resp.json()
            print(f"結果: {result.get('response', 'No response')[:200]}")

asyncio.run(main())
