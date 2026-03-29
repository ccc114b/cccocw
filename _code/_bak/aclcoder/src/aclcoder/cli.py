#!/usr/bin/env python3
"""
ACLCoder CLI - 命令行入口
"""

import argparse
import asyncio
from pathlib import Path

from aclcoder import AIExecutor, AICommander, MessageBus, ACLParser, ACLFileHandler, MessageType
from aclcoder.acl import ACL_SPEC


async def send(sender: str, receiver: str, message: str):
    """发送消息"""
    print(f"\n{'='*60}")
    print(f"{sender} -> {receiver}:")
    print(f"{'='*60}")
    print(message)
    return message


async def human_mode(root_dir: str = ".", model: str = "minimax-m2.5:cloud"):
    """人类模式 - 人类扮演 Commander"""
    
    commander = AICommander(model=model)
    executor = AIExecutor(model=model)
    
    message_bus = MessageBus()
    acl_handler = ACLFileHandler(root_dir=root_dir)
    acl_parser = ACLParser()
    
    message_bus.register_handler(MessageType.COMMAND, acl_handler)
    message_bus.register_handler(MessageType.QUERY, acl_handler)
    
    print("=" * 60)
    print("ACLCoder - Human Mode")
    print("=" * 60)
    print("你扮演 Commander，AI 扮演 Executor")
    print("輸入你的指令，或輸入 'quit' 離開")
    print("=" * 60)
    
    task = input("\n請輸入任務: ").strip()
    if not task:
        print("任務不能為空")
        return
    
    commander.remember(task)
    
    prompt = task
    
    while True:
        response = await executor.respond(prompt)
        await send("Executor", "Commander", response)
        
        messages = acl_parser.parse(response)
        print(f"\n[DEBUG] root_dir={root_dir}, 解析到 {len(messages)} 個訊息")
        
        for i, msg in enumerate(messages):
            file_path = msg.metadata.get('file_path')
            print(f"  [{i}] type={msg.type}, file={file_path}")
            if file_path:
                full_path = Path(root_dir) / file_path
                print(f"       -> 完整路徑: {full_path}")
        
        write_count = sum(1 for m in messages if m.metadata.get('file_path'))
        
        if write_count > 0:
            # 执行写入
            for msg in messages:
                await message_bus.send(msg)
            print(f"\n✅ 已写入 {write_count} 个文件到 {root_dir}")
        else:
            print(f"\n⚠️ 沒有 write 指令")
        
        print("\n" + "=" * 60)
        user_input = input("你的回覆 (Enter 繼續, quit 離開, 或直接下指令): ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input:
            prompt = user_input
        else:
            prompt = "請繼續"


async def ai_mode(prompt_file: str, loops: int, root_dir: str, model: str):
    """AI 模式 - AI 扮演 Commander"""
    
    # 读取 prompt 文件
    prompt_path = Path(prompt_file)
    if not prompt_path.exists():
        print(f"錯誤: 找不到檔案 {prompt_file}")
        return
    
    task = prompt_path.read_text().strip()
    
    commander = AICommander(model=model)
    executor = AIExecutor(model=model)
    
    message_bus = MessageBus()
    acl_handler = ACLFileHandler(root_dir=root_dir)
    acl_parser = ACLParser()
    
    message_bus.register_handler(MessageType.COMMAND, acl_handler)
    message_bus.register_handler(MessageType.QUERY, acl_handler)
    
    print("=" * 60)
    print("ACLCoder - AI Mode")
    print("=" * 60)
    print(f"執行 {loops} 輪對話")
    print("=" * 60)
    
    commander.remember(task)
    prompt = task
    
    for i in range(loops):
        print(f"\n{'='*60}")
        print(f"對話回合 {i+1}/{loops}")
        print(f"{'='*60}")
        
        # Executor 生成
        response = await executor.respond(prompt)
        await send("Executor", "Commander", response)
        
        # Commander 审核
        review = await commander.review(response)
        await send("Commander", "Executor", review)
        
        # 检查是否有 write
        messages = acl_parser.parse(review)
        write_count = sum(1 for m in messages if m.metadata.get('file_path'))
        
        if write_count > 0:
            print(f"\n✅ 已写入 {write_count} 个文件")
        
        # 继续对话
        prompt = review
    
    print(f"\n{'='*60}")
    print(f"完成 {loops} 輪對話")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="ACLCoder - AI Code Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  aclcoder --human -o ./output           # 人類模式，輸出到 ./output
  aclcoder --ai prompt.md -o ./output   # AI 模式，執行 5 輪
  aclcoder --human -o ./output -m llama3 # 指定模型
"""
    )
    parser.add_argument("--human", action="store_true", help="人類模式 - 人類扮演 Commander")
    parser.add_argument("--ai", metavar="FILE", help="AI 模式 - AI 扮演 Commander (從檔案讀取任務)")
    parser.add_argument("--loops", type=int, default=5, help="AI 模式迴圈次數 (預設: 5)")
    parser.add_argument("-o", "--output", required=True, help="輸出目錄 (必要)")
    parser.add_argument("-m", "--model", default="minimax-m2.5:cloud", help="Ollama 模型 (預設: minimax-m2.5:cloud)")
    
    args = parser.parse_args()
    
    # 创建输出目录
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    if args.human:
        asyncio.run(human_mode(args.output, args.model))
    elif args.ai:
        asyncio.run(ai_mode(args.ai, args.loops, args.output, args.model))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
