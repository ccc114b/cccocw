"""
MiniCode - 純 Python 版本的 AI 程式碼生成器
不使用 AIL 框架，直接用 Ollama API
"""

import asyncio
import subprocess
import aiohttp
import json
from pathlib import Path


class Ollama:
    """Ollama API 客戶端"""
    
    def __init__(self, model: str = "minimax-m2.5:cloud"):
        self.model = model
        self.base_url = "http://localhost:11434"
    
    async def chat(self, message: str, system: str = "") -> str:
        """發送聊天請求"""
        import subprocess
        
        full_prompt = f"{system}\n\n{message}" if system else message
        
        proc = await asyncio.create_subprocess_exec(
            "ollama", "run", self.model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate(input=full_prompt.encode())
        
        if proc.returncode != 0:
            return f"Error: {stderr.decode()}"
        
        return stdout.decode()


class MiniCode:
    """
    純 Python 版本的 MiniCode
    
    用法:
        agent = MiniCode()
        await agent.run("建立一個 hello world 網頁")
    """
    
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        self.ollama = Ollama()
        self.system_prompt = """你是一個專業的程式設計師，擅長根據用戶需求生成程式碼。

使用工具完成任務：
- 讀取檔案: `read:路徑`
- 寫入檔案: `write:路徑|內容`
- 執行命令: `run:命令`
- 列出檔案: `ls:pattern`

重要：
1. 先了解現有檔案結構
2. 規劃需要哪些檔案
3. 逐步建立程式碼
4. 測試執行結果
5. 只輸出指令，不要解釋"""
    
    async def run(self, task: str) -> str:
        """執行任務"""
        print(f"\n🎯 任務: {task}")
        print("="*50)
        
        # 列出現有檔案
        files = self._list_files()
        print(f"📁 現有檔案:\n{files}")
        
        # 發送任務給 AI
        prompt = f"""
現有檔案:
{files}

任務: {task}

請規劃需要建立哪些檔案，並開始實作。
"""
        
        result = await self.ollama.chat(prompt, self.system_prompt)
        print(f"\n📝 執行結果:\n{result}")
        
        # 解析並執行 AI 的指令
        await self._execute_commands(result)
        
        return result
    
    def _list_files(self, pattern: str = "*") -> str:
        """列出檔案"""
        files = list(self.root.rglob(pattern))
        return "\n".join(str(f.relative_to(self.root)) for f in files[:20])
    
    async def _execute_commands(self, result: str):
        """解析並執行 AI 的指令"""
        lines = result.split("\n")
        for line in lines:
            line = line.strip()
            
            # 解析指令
            if line.startswith("read:"):
                path = line[5:].strip()
                print(f"\n📄 讀取: {path}")
                content = self.read(path)
                print(content[:200])
            
            elif line.startswith("write:"):
                # 格式: write:路徑|內容
                if "|" in line:
                    parts = line[6:].split("|", 1)
                    path, content = parts[0].strip(), parts[1].strip()
                    print(f"\n📝 寫入: {path}")
                    print(self.write(path, content))
            
            elif line.startswith("run:"):
                command = line[4:].strip()
                print(f"\n⚡ 執行: {command}")
                result = self.run_shell(command)
                print(result[:200])
    
    def read(self, path: str) -> str:
        """讀取檔案"""
        try:
            return (self.root / path).read_text(encoding="utf-8")
        except Exception as e:
            return f"Error: {e}"
    
    def write(self, path: str, content: str) -> str:
        """寫入檔案"""
        try:
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text(content, encoding="utf-8")
            return f"✓ 已寫入: {path}"
        except Exception as e:
            return f"Error: {e}"
    
    def run_shell(self, command: str) -> str:
        """執行命令"""
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
    print("✓ MiniCode 初始化成功")
    
    agent = MiniCode(root_dir="./generated")
    await agent.run("建立一個簡單的 Hello World HTML 網頁")


if __name__ == "__main__":
    asyncio.run(demo())
