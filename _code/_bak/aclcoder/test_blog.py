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
    print(message)
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
4. 等對方做出第一版後，進行測試，有錯就讓他修改
""")
    
    # ACL 处理
    message_bus = MessageBus()
    acl_handler = ACLFileHandler(root_dir="./test_output")
    acl_parser = ACLParser()
    
    # ========================
    # 对话流程
    # ========================
    
    # 1. Commander 下达任务
    task = "我要建立一個 blog 系統，使用 python，請先用 <ask> 問我詳細的細節"
    await send("Commander", "Executor", f"任務: {task}")
    
    # 2. 循环对话
    prompt = task
    max_rounds = 5
    round_num = 0
    
    while round_num < max_rounds:
        round_num += 1
        print(f"\n--- 對話回合 {round_num} ---")
        
        # Executor 生成
        response = await executor.respond(prompt)
        await send("Executor", "Commander", response)
        
        # Commander 审核/回答
        review_result = await commander.review(response)
        await send("Commander", "Executor", review_result)
        
        # 检查是否需要继续
        if "<write" in review_result:
            # 审核通过，执行 ACL
            messages = acl_parser.parse(review_result)
            for msg in messages:
                await message_bus.send(msg)
            print(f"\n✅ 審核通過，已執行 ACL 指令")
        
        # 将 Commander 的回答传给 Executor 继续
        prompt = review_result
        
        # 检查审核结果是否有 write
        print(f"\n[DEBUG] 檢查 review_result 是否包含 <write>: {'<write' in review_result}")
        if "<write" in review_result:
            # 审核通过，执行 ACL
            print(f"[DEBUG] review_result 前 200 字: {review_result[:200]}")
            messages = acl_parser.parse(review_result)
            print(f"\n[DEBUG] 解析到 {len(messages)} 個訊息")
            for i, msg in enumerate(messages):
                print(f"  - 訊息 {i+1}: {msg.type}, file: {msg.metadata.get('file_path', 'N/A')}")
                await message_bus.send(msg)
            print(f"\n✅ 審核通過，已執行 ACL 指令")

asyncio.run(main())
