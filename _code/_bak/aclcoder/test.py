#!/usr/bin/env python3
"""测试 ACLCoder"""
import asyncio
import sys
sys.path.insert(0, 'src')

from aclcoder import AIExecutor

async def main():
    executor = AIExecutor(root_dir='./test_output', debug=True)
    await executor.run('建立一个简单的 hello.py，输出 "Hello World"')

asyncio.run(main())
