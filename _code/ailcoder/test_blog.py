#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, 'src')

from ailcoder import AIExecutor

async def main():
    executor = AIExecutor(root_dir='./generated', debug=True)
    await executor.run('''建立一個部落格系統
請用 <ask> 詢問我詳細規格。''')

asyncio.run(main())
