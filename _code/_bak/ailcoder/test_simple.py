#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, 'src')

from ailcoder import AIExecutor

async def main():
    executor = AIExecutor(root_dir='./generated', debug=True)
    await executor.run('''直接建立一個簡單的 hello.py
輸出 "Hello World" 即可''')

asyncio.run(main())
