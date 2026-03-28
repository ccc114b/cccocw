"""
MiniCode - 使用 AIL 框架的 AI 程式碼生成器
類似 OpenCode，但更輕量
"""

import asyncio
from pathlib import Path
from ailang import OllamaAgent, init_ollama


class MiniCode:
    """
    使用 AIL 框架的 MiniCode
    
    用法:
        agent = MiniCode()
        await agent.run("建立一個 hello world 網頁")
    """
    
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        
        # 使用 AIL 的 OllamaAgent - 內建記憶、歷史
        self.agent = OllamaAgent(
            "minicode",
            system_prompt="""你是一個專業的程式設計師，擅长创建完整的应用程序。

当你完成任务时，必须按照以下 XML 格式输出指令：

<shell>ls</shell>
<write file="main.py">
from flask import Flask
app = Flask(__name__)
</write>
<read file="config.json"></read>

重要规则：
1. 每个指令单独放在一行标签中
2. <write file="..."> 和 </write> 之间是完整的文件内容
3. 立即开始写文件，不要询问
4. 先创建 backend.py，然后创建 templates/index.html
5. 必须包含所有代码，不能省略"""
        )
    
    async def run(self, task: str) -> str:
        """執行任務"""
        print(f"\n🎯 任務: {task}")
        print("="*50)
        
        # 列出現有檔案
        files = self._list_files()
        print(f"📁 現有檔案:\n{files}")
        
        # 讓 AI 執行任務
        prompt = f"""
現有檔案:
{files}

任務: {task}

請規劃並執行。
"""
        
        result = await self.agent(prompt)
        print(f"\n📝 執行結果:\n{result}")
        
        # 解析並執行指令
        await self._execute(result)
        
        return result
    
    def _list_files(self, pattern: str = "*") -> str:
        files = list(self.root.rglob(pattern))
        return "\n".join(str(f.relative_to(self.root)) for f in files[:20])
    
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
    
    async def _execute(self, result: str):
        """解析 AI 的指令並執行"""
        import re
        
        # 移除思考過程
        result = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', result)
        
        # 解析 <write file="path">content</write>
        write_pattern = r'<write file="([^"]+)">\s*(.+?)\s*</write>'
        for match in re.finditer(write_pattern, result, re.DOTALL):
            path = match.group(1).strip()
            content = match.group(2).strip()
            print(f"\n📝 寫入: {path}")
            print(self.write(path, content))
        
        # 解析 <shell>command</shell>
        shell_pattern = r'<shell>\s*(.+?)\s*</shell>'
        for match in re.finditer(shell_pattern, result, re.DOTALL):
            cmd = match.group(1).strip()
            if cmd and len(cmd) > 1:
                print(f"\n⚡ 執行: {cmd}")
                print(self.run_shell(cmd))
        
        # 解析 <read file="path"></read>
        read_pattern = r'<read file="([^"]+)">\s*</read>'
        for match in re.finditer(read_pattern, result):
            path = match.group(1).strip()
            print(f"\n📄 讀取: {path}")
            print(self.read(path)[:500])


async def demo():
    """示範"""
    init_ollama(model="minimax-m2.5:cloud")
    print("✓ Ollama 初始化成功")
    
    agent = MiniCode(root_dir="./generated")
    await agent.run("建立 SQLite TODO 應用：backend.py + templates/index.html")


if __name__ == "__main__":
    asyncio.run(demo())
