#!/usr/bin/env python3
"""快速測試 AICommander 是否正常工作"""
import asyncio
import sys
sys.path.insert(0, 'src')

from ailcoder.executor import AICommander

async def main():
    commander = AICommander()
    commander.set_project("建立一個簡單的 hello.py")
    
    # 測試 commander 能否回答問題
    print("測試 AICommander...")
    answer = await commander.answer("我應該用什麼框架?")
    print(f"💬 AICommander 回覆: {answer[:200]}...")

asyncio.run(main())
