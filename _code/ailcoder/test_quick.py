#!/usr/bin/env python3
"""快速測試完整流程"""
import asyncio
import sys
sys.path.insert(0, 'src')

from ailcoder.executor import AIExecutor, AICommander

async def main():
    # 先測試 AICommander 單獨
    print("測試 AICommander...")
    commander = AICommander()
    commander.set_project("建立 hello.py")
    
    answer = await commander.answer("我應該用什麼框架?")
    print(f"💬 回答: {answer[:100]}...")
    
    print("\n測試完成!")

asyncio.run(main())
