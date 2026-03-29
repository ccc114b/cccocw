#!/usr/bin/env python3
"""
ACLCoder CLI - 命令行入口
"""

import argparse
import asyncio
import sys
from pathlib import Path


async def run_task(task: str, output_dir: str = ".", model: str = "minimax-m2.5:cloud", debug: bool = False):
    """运行任务"""
    from aclcoder import AIExecutor
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    executor = AIExecutor(root_dir=str(output_path), model=model, debug=debug)
    await executor.run(task)


def main():
    parser = argparse.ArgumentParser(
        description="ACLCoder - 使用 ACL 协议的 AI 代码生成工具"
    )
    parser.add_argument("task", nargs="?", help="任务描述")
    parser.add_argument("-o", "--output", default="./output", help="输出目录")
    parser.add_argument("-m", "--model", default="minimax-m2.5:cloud", help="Ollama 模型")
    parser.add_argument("-d", "--debug", action="store_true", help="调试模式")
    
    args = parser.parse_args()
    
    if not args.task:
        parser.print_help()
        return
    
    asyncio.run(run_task(args.task, args.output, args.model, args.debug))


if __name__ == "__main__":
    main()
