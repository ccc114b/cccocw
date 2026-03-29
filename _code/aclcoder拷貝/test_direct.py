#!/usr/bin/env python3
"""测试 ACLCoder - 直接测试"""
import asyncio
import sys
sys.path.insert(0, 'src')

from aclcoder import AIExecutor, ACLParser, ACLFileHandler, MessageBus, MessageType

async def main():
    executor = AIExecutor()
    message_bus = MessageBus()
    acl_handler = ACLFileHandler(root_dir="./test_output")
    acl_parser = ACLParser()
    
    # 注册处理器
    message_bus.register_handler(MessageType.COMMAND, acl_handler)
    message_bus.register_handler(MessageType.QUERY, acl_handler)
    
    # 直接用 ACL 规格的 prompt
    task = """任務：用 FastAPI + SQLite 建立一個簡單的 blog 系統。
請直接輸出 <write> 標籤生成代碼，不要問問題。
"""
    print(f"任務: 建立 blog 系統")
    
    response = await executor.respond(task)
    print(f"\nExecutor 回覆:")
    print(response[:500])
    
    # 解析
    messages = acl_parser.parse(response)
    print(f"\n解析到 {len(messages)} 個訊息")
    
    # 执行
    for msg in messages:
        file_path = msg.metadata.get('file_path')
        print(f"  - 發送: {msg.type}, file: {file_path}")
        await message_bus.send(msg)

asyncio.run(main())
