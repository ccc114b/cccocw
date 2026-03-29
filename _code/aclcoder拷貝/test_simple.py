#!/usr/bin/env python3
"""测试 ACLCoder - Blog 系统"""
import asyncio
import sys
sys.path.insert(0, 'src')

from aclcoder import AIExecutor, AICommander, MessageBus, ACLParser, ACLFileHandler

async def send(sender: str, receiver: str, message: str):
    """发送消息"""
    print(f"\n{'='*60}")
    print(f"{sender} -> {receiver}:")
    print(f"{'='*60}")
    print(message[:200] + "..." if len(message) > 200 else message)
    return message

async def main():
    # ========================
    # 建立元件
    # ========================
    commander = AICommander()
    executor = AIExecutor()
    
    # Commander 记住项目特性
    commander.remember("""
1. 用 FastAPI + SQLite
2. 專案愈簡單愈好，是學生作業等級
3. 一開始不需要登入/登出/註冊，只要能貼文就行
""")
    
    # ACL 处理
    message_bus = MessageBus()
    acl_handler = ACLFileHandler(root_dir="./test_output")
    acl_parser = ACLParser()
    
    # ========================
    # 对话流程
    # ========================
    
    # 1. Commander 下达任务 - 直接要求生成代码
    task = "我要建立一個 blog 系統，用 FastAPI + SQLite，請直接用 <write> 生成代碼"
    await send("Commander", "Executor", f"任務: {task}")
    
    # 2. Executor 生成
    response = await executor.respond(task)
    await send("Executor", "Commander", response)
    
    # 3. Commander 审核
    review_result = await commander.review(response)
    await send("Commander", "Executor (審核)", review_result)
    
    # 4. 检查是否包含 write
    print(f"\n[DEBUG] 檢查是否包含 <write>: {'<write' in review_result}")
    
    if "<write" in review_result:
        messages = acl_parser.parse(review_result)
        print(f"[DEBUG] 解析到 {len(messages)} 個訊息")
        
        for i, msg in enumerate(messages):
            print(f"  - 訊息 {i+1}: type={msg.type}, file={msg.metadata.get('file_path', 'N/A')}")
            await message_bus.send(msg)
        
        print(f"\n✅ 已執行 ACL 指令")
    else:
        print(f"\n⚠️ 沒有 write 指令")

asyncio.run(main())
