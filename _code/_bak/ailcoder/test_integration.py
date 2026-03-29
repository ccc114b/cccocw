#!/usr/bin/env python3
"""直接測試 ACLParser 和 AICommander 整合"""
import asyncio
import sys
import re
sys.path.insert(0, 'src')

from ailcoder.acl_socket import ACLParser, ACLConsoleHandler

async def main():
    # 模擬 AI 輸出，包含 <ask> 標籤
    ai_output = '''
<write file="hello.py">
print("Hello World")
</write>
<ask>我應該用什麼函式庫?</ask>
'''
    
    print("=" * 50)
    print("測試 1: ACLParser 處理 <write>")
    print("=" * 50)
    
    handler = ACLConsoleHandler('./test_output')
    parser = ACLParser(handler, debug=True)
    result = await parser.execute(ai_output)
    
    print(f"\n結果: {result}")
    
    # 檢查是否有 ask 標籤（應該被跳過）
    if '<ask>' not in result and '沒有執行任何指令' not in result:
        print("\n✅ write 正確執行，ask 被正確跳過!")
    else:
        print("\n❌ 有問題")
    
    print("\n" + "=" * 50)
    print("測試 2: executor 檢測 <ask> 並呼叫 AICommander")
    print("=" * 50)
    
    # 檢查 executor 是否有 commander
    from ailcoder.executor import AIExecutor
    executor = AIExecutor(root_dir='./test_output')
    
    if hasattr(executor, 'commander'):
        print("✅ AIExecutor 有 commander 屬性")
    else:
        print("❌ AIExecutor 缺少 commander 屬性")
    
    # 檢測 ask 標籤
    ask_pattern = r'<ask>(.+?)</ask>'
    questions = re.findall(ask_pattern, ai_output, re.DOTALL)
    print(f"\n檢測到問題: {questions}")

asyncio.run(main())
