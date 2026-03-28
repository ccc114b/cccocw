"""
MiniCode - 使用 AIL 框架的 AI 程式碼生成器
支援 ACL 詢問機制 (v0.4)
"""

import asyncio
import re
from pathlib import Path
from ailang import OllamaAgent, init_ollama
from ailang.acl_socket import ACLMessageType, ACLMessage


class MiniCode:
    """
    使用 AIL 框架的 MiniCode
    
    用法:
        agent = MiniCode()
        await agent.run("建立一個 hello world 網頁")
    """
    
    def __init__(self, root_dir: str = ".", interactive: bool = True):
        self.root = Path(root_dir)
        self.interactive = interactive
        
        # 使用 AIL 的 OllamaAgent - 內建記憶、歷史
        self.agent = OllamaAgent(
            "minicode",
            system_prompt="""你是 minicode 程式碼生成器。你**沒有檔案系統權限**，只能輸出文字。

你必須輸出以下 XML 格式，讓我（minicode.py）幫你寫入檔案：

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
4. 後端程式用 Flask + SQLite
5. 前端用 HTML + JavaScript"""
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

請規劃並執行。如果有任何不清楚的地方，請使用 <ask> 詢問。
"""
            
            result = await self.agent(prompt)
            print(f"\n📝 AI 輸出:\n{result[:500]}...")
            
            # 解析並執行指令
            execution_result = await self._execute(result)
            print(f"\n執行結果:\n{execution_result}")
            
            # 檢查是否有詢問
            if '<ask>' not in result:
                break
            
            # 如果有詢問但不是互動模式，只執行一次
            if not self.interactive:
                print("⚠️ 有詢問但非互動模式，停止執行")
                break
        
        return result
    
    def _list_files(self, pattern: str = "*") -> str:
        files = list(self.root.rglob(pattern))
        return "\n".join(str(f.relative_to(self.root)) for f in files[:20])
    
    async def _execute(self, result: str) -> str:
        """解析 AI 的指令並執行"""
        # 移除思考過程
        result = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', result, flags=re.IGNORECASE)
        result = re.sub(r'\[2K\[2J\[H', '', result)  # 清除 ANSI
        
        results = []
        
        # 找所有 write 指令 - 更寬鬆的匹配
        write_pattern = r'<write\s+file="([^"]+)">(.+?)</write>'
        for match in re.finditer(write_pattern, result, re.DOTALL | re.IGNORECASE):
            file_path = match.group(1).strip()
            content = match.group(2).strip()
            if content:
                r = self.write(file_path, content)
                results.append(f"📝 寫入: {file_path}\n{r}")
        
        # 找所有 shell 指令
        shell_pattern = r'<shell>(.+?)</shell>'
        for match in re.finditer(shell_pattern, result, re.DOTALL):
            command = match.group(1).strip()
            if command and len(command) > 1:
                r = self.run_shell(command)
                results.append(f"⚡ 執行: {command}\n{r[:500]}")
        
        # 找所有 ask 指令
        ask_pattern = r'<ask>(.+?)</ask>'
        for match in re.finditer(ask_pattern, result, re.DOTALL):
            question = match.group(1).strip()
            if self.interactive:
                print(f"\n❓ AI 詢問: {question}")
                answer = input("➤ 你的回覆: ")
                results.append(f"❓ 詢問: {question}\n➤ 回覆: {answer}")
            else:
                results.append(f"❓ 詢問: {question} (非互動模式，跳過)")
        
        # 如果沒有找到 ACL 指令，嘗試直接解析程式碼
        if not results:
            results = self._parse_plain_code(result)
        
        return "\n\n".join(results) if results else "沒有執行任何指令"
    
    def _parse_plain_code(self, result: str) -> list:
        """直接解析 AI 输出的程式碼"""
        results = []
        
        # 移除思考過程
        result = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', result, flags=re.IGNORECASE)
        
        # 找 Python 程式碼（from flask 開始到結尾）
        python_patterns = [
            r'(from flask.+?if __name__ == ["\']__main__["\'])',
            r'(from flask.+?app\.run\()',
            r'(import sqlite3.+?conn\.close\(\))',
        ]
        
        for pattern in python_patterns:
            match = re.search(pattern, result, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                if len(content) > 100:  # 確保是真正的程式碼
                    self.write("backend.py", content)
                    results.append("📝 寫入: backend.py")
                    break
        
        # 找 HTML 程式碼
        html_patterns = [
            r'(<!DOCTYPE html>[\s\S]*?</html>)',
            r'(<html[\s\S]*?</html>)',
        ]
        
        for pattern in html_patterns:
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                content = match.group(1)
                if len(content) > 100:
                    self.write("templates/index.html", content)
                    results.append("📝 寫入: templates/index.html")
                    # 確保目錄存在
                    (self.root / "templates").mkdir(exist_ok=True)
                    break
        
        # 執行 mkdir 確保 templates 目錄存在
        if any("templates" in r for r in results):
            self.run_shell("mkdir -p templates")
        
        return results
    
    def read(self, path: str) -> str:
        try:
            return (self.root / path).read_text(encoding="utf-8")
        except Exception as e:
            return f"Error: {e}"
    
    def write(self, path: str, content: str) -> str:
        try:
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text(content, encoding="utf-8")
            return f"✓ 已寫入: {path}"
        except Exception as e:
            return f"Error: {e}"
    
    def run_shell(self, command: str) -> str:
        import subprocess
        try:
            result = subprocess.run(
                command, shell=True, cwd=str(self.root),
                capture_output=True, text=True, timeout=60
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"Error: {e}"


async def demo():
    """示範"""
    init_ollama(model="minimax-m2.5:cloud")
    print("✓ Ollama 初始化成功")
    
    agent = MiniCode(root_dir="./generated", interactive=True)
    await agent.run("建立 SQLite TODO 應用：backend.py + templates/index.html")


if __name__ == "__main__":
    asyncio.run(demo())
