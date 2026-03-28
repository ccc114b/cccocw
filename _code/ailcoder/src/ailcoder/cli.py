"""
ailcoder CLI
命令列介面
"""

import asyncio
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="ailcoder - AI Code Generator"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="要執行的任務描述"
    )
    parser.add_argument(
        "-o", "--output",
        default="./generated",
        help="輸出目錄 (預設: ./generated)"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="顯示除錯訊息"
    )
    parser.add_argument(
        "-m", "--model",
        default="minimax-m2.5:cloud",
        help="使用的模型 (預設: minimax-m2.5:cloud)"
    )
    
    args = parser.parse_args()
    
    # 讀取 .ail 檔案
    task = args.task
    if task and task.endswith(".ail"):
        task_file = Path(task)
        if task_file.exists():
            task = task_file.read_text(encoding="utf-8")
            # 移除 ## 標題行
            lines = task.split("\n")
            task = "\n".join(line for line in lines if not line.startswith("## "))
            print(f"📄 讀取任務檔案: {task}")
        else:
            print(f"❌ 找不到檔案: {task}")
            return
    
    if not task:
        print("ailcoder - AI Code Generator")
        print("\n用法:")
        print("  ailcoder '建立一個 hello world 網頁'")
        print("  ailcoder todo.ail")
        print("  ailcoder '建立 SQLite TODO 應用' -o ./myproject")
        print("\n選項:")
        print("  -o, --output  輸出目錄")
        print("  -d, --debug  顯示除錯訊息")
        print("  -m, --model  使用的模型")
        print("\n.ail 檔案格式:")
        print("  # mytask.ail")
        print("  ## 任務")
        print("  建立一個網站")
        print("  ## 詳細需求")
        print("  1. Flask 後端")
        return
    
    # 執行任務
    asyncio.run(run_task(task, args.output, args.debug, args.model))


async def run_task(task: str, output_dir: str, debug: bool, model: str):
    """執行 AI 任務"""
    from ailang import init_ollama
    from ailcoder import AIExecutor
    
    # 初始化 Ollama
    try:
        init_ollama(model=model)
        print(f"✓ Ollama 初始化成功 ({model})")
    except Exception as e:
        print(f"⚠️ Ollama 初始化失敗: {e}")
        return
    
    # 確保輸出目錄存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 建立 AIExecutor
    executor = AIExecutor(root_dir=str(output_path), debug=debug)
    
    # 執行任務
    await executor.run(task)
    
    print("\n✅ 完成！")
    print(f"📁 檔案位置: {output_path.absolute()}")


if __name__ == "__main__":
    main()
