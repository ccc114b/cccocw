"""
MiniCode - 使用 AIL 框架的 AI 程式碼生成器
使用 ACL (AI Communication Language) 與 AI 溝通
"""

import asyncio
import re
from pathlib import Path
from ailang import OllamaAgent, init_ollama
from ailang.acl_socket import ACLParser, ACLConsoleHandler


class MiniCode:
    """
    使用 AIL + ACL 框架的 MiniCode
    
    用法:
        agent = MiniCode()
        await agent.run("建立一個 hello world 網頁")
    """
    
    def __init__(self, root_dir: str = ".", interactive: bool = True, debug: bool = False):
        self.root = Path(root_dir)
        self.interactive = interactive
        self.debug = debug
        
        # ACL 處理器
        self.acl_handler = ACLConsoleHandler(root_dir)
        
        # 使用 AIL 的 OllamaAgent
        self.agent = OllamaAgent(
            "minicode",
            system_prompt="""你是 minicode 程式碼生成器。你**沒有檔案系統權限**，只能輸出文字。

你必須輸出以下 ACL XML 格式：

```
<write file="backend.py">
from flask import Flask, render_template, request, jsonify
import sqlite3
app = Flask(__name__)
# ... 完整程式碼 ...
</write>

<write file="templates/index.html">
<!DOCTYPE html>
<html>
<!-- ... 完整 HTML ... -->
</html>
```

**嚴格規則**：
1. 用 <write file="檔名"> 包裹程式碼
2. 用 </write> 結束
3. 不要解釋，直接寫
4. 後端用 Flask + SQLite
5. 前端用 HTML + JavaScript
6. 如果有不清楚的，用 <ask> 詢問"""
        )
    
    async def run(self, task: str) -> str:
        """執行任務"""
        print(f"\n🎯 任務: {task}")
        print("="*50)
        
        # 列出現有檔案
        files = self._list_files()
        print(f"📁 現有檔案:\n{files}")
        
        # 迴圈處理，直到沒有詢問
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # 讓 AI 執行任務
            prompt = f"""
現有檔案:
{files}

任務: {task}

請直接寫出程式碼。如果有不清楚的，用 <ask> 詢問。
"""
            
            if self.debug:
                print(f"\n{'='*50}")
                print("🔵 ACL → AI (prompt):")
                print(f"{'='*50}")
                print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
            
            result = await self.agent(prompt)
            print(f"\n📝 AI 輸出:\n{result[:300]}...")
            
            # 使用 ACLParser 解析並執行
            parser = ACLParser(self.acl_handler, debug=self.debug)
            execution_result = await parser.execute(result)
            print(f"\n執行結果:\n{execution_result}")
            
            # 檢查是否有詢問
            if '<ask>' not in result:
                break
            
            # 如果有詢問但不是互動模式，停止
            if not self.interactive:
                print("⚠️ 有詢問但非互動模式，停止執行")
                break
        
        return result
    
    def _list_files(self, pattern: str = "*") -> str:
        files = list(self.root.rglob(pattern))
        return "\n".join(str(f.relative_to(self.root)) for f in files[:20])
    
    def read(self, path: str) -> str:
        return self.acl_handler.on_read(path)
    
    def write(self, path: str, content: str) -> str:
        return asyncio.run(self.acl_handler.on_write(path, content))
    
    def run_shell(self, command: str) -> str:
        return asyncio.run(self.acl_handler.on_shell(command))


async def demo():
    """示範"""
    init_ollama(model="minimax-m2.5:cloud")
    print("✓ Ollama 初始化成功")
    
    agent = MiniCode(root_dir="./generated", interactive=False, debug=True)
    await agent.run("""建立 SQLite TODO：
- 後端 Flask + SQLite
- 首頁 /
- API: GET/POST /api/todos
- 欄位: id, title, completed
- 前端 HTML + JS
- 功能: 新增、刪除、完成""")


if __name__ == "__main__":
    asyncio.run(demo())
