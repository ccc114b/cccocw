#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, 'src')

from ailcoder import AIExecutor
from ailang import init_ollama

init_ollama(model='minimax-m2.5:cloud')

async def main():
    executor = AIExecutor(root_dir='./generated', debug=True)
    await executor.run('''建立一個 hello.py
如果規格不清楚，用 <ask> 詢問。''')

asyncio.run(main())
