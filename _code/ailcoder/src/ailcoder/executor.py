"""
ailcoder - AI Code Generator
使用 AIL 框架 + ACL 通訊協定的程式碼生成器
"""

import asyncio
import re
from pathlib import Path


class OllamaAgentWrapper:
    """Ollama Agent 包裝器"""
    
    def __init__(self, name: str, system_prompt: str = ""):
        self.name = name
        self.system_prompt = system_prompt
        self._history = []
    
    async def __call__(self, prompt: str) -> str:
        """執行任務"""
        try:
            from ailang import OllamaAgent
            agent = OllamaAgent(self.name, system_prompt=self.system_prompt)
            result = await agent(prompt)
            return result
        except Exception as e:
            # 如果沒有 AIL，用 subprocess 直接呼叫
            return await self._call_ollama(prompt)
    
    async def _call_ollama(self, prompt: str) -> str:
        """直接呼叫 Ollama"""
        import subprocess
        proc = await asyncio.create_subprocess_exec(
            "ollama", "run", "minimax-m2.5:cloud",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate(input=prompt.encode())
        if proc.returncode != 0:
            return f"Error: {stderr.decode()}"
        return stdout.decode()


class AICommander:
    """AI 指揮官 - 自動回答執行者問題"""
    
    def __init__(self):
        self.agent = OllamaAgentWrapper(
            "ai-commander",
            system_prompt="""你是 AICommander，一個專業的 AI 專案管理員。

你了解以下架構：
- AIL (AI Language): 目標導向的 Python AI 框架
- ACL (AI Communication Language): 結構化溝通格式

## ACL 指令集
- <write file="...">: 寫入檔案
- <shell>: 執行命令
- <read file="...">: 讀取檔案
- <ask>: 詢問
- <answer>: 回覆
- <result>: 結果回報

## 重要規則
1. 執行者沒有檔案系統權限
2. 所有檔案操作必須透過 ACL
3. 根據專案目標給出明確建議
4. 用繁體中文回覆"""
        )
        self.project_context = ""
    
    def set_project(self, task: str):
        """設定專案目標"""
        self.project_context = task
    
    async def answer(self, question: str) -> str:
        """回答執行者的問題"""
        prompt = f"""
## 專案目標
{self.project_context}

## 執行者詢問
{question}

請根據專案目標直接回答。如果需要做決定，請給出最合適的建議。
"""
        return await self.agent(prompt)


class AIExecutor:
    """
    AI 執行器 - 使用 AIL/ACL 框架
    
    用法:
        executor = AIExecutor()
        await executor.run("建立一個 hello world 網頁")
    """
    
    def __init__(self, root_dir: str = ".", debug: bool = False):
        self.root = Path(root_dir)
        self.debug = debug
        
        # ACL 處理器（延遲載入避免循環依賴）
        self._acl_handler = None
        
        # AI 執行者
        self.agent = OllamaAgentWrapper(
            "executor",
            system_prompt="""你是 AIExecutor，專門執行 ACL 指令。

**你沒有檔案系統權限**，只能輸出文字。

用以下格式輸出：
<write file="檔名">程式碼</write>
<shell>命令</shell>

如果有不清楚的，用 <ask> 詢問。"""
        )
    
    @property
    def acl_handler(self):
        if self._acl_handler is None:
            from ailang.acl_socket import ACLConsoleHandler
            self._acl_handler = ACLConsoleHandler(str(self.root))
        return self._acl_handler
    
    async def run(self, task: str) -> str:
        """執行任務"""
        print(f"\n🎯 任務: {task}")
        print("="*50)
        
        files = self._list_files()
        print(f"📁 現有檔案:\n{files}")
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            prompt = f"""
現有檔案:
{files}

任務: {task}

直接寫出程式碼，用以下格式：
<write file="backend.py">
程式碼
</write>
<write file="templates/index.html">
HTML
</write>

有問題用 <ask> 詢問。
"""
            
            if self.debug:
                print(f"\n{'='*50}")
                print("🔵 ACL → AI (prompt):")
                print(f"{'='*50}")
                print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
            
            result = await self.agent(prompt)
            
            if self.debug:
                print(f"\n📝 AI 輸出:\n{result[:500]}...")
            
            # 使用 ACLParser 解析並執行
            from ailang.acl_socket import ACLParser
            parser = ACLParser(self.acl_handler, debug=self.debug)
            execution_result = await parser.execute(result)
            
            if self.debug:
                print(f"\n執行結果:\n{execution_result}")
            else:
                print(f"\n執行結果: {execution_result[:200]}...")
            
            # 檢查是否有詢問
            if '<ask>' not in result:
                break
            
            # TODO: 使用 AICommander 自動回答
            print(f"\n⚠️ 有詢問: (暫時忽略)")
            break
        
        return result
    
    def _list_files(self, pattern: str = "*") -> str:
        files = list(self.root.rglob(pattern))
        return "\n".join(str(f.relative_to(self.root)) for f in files[:20])
