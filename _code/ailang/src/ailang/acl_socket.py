"""
ACL WebSocket 通訊模組
支援雙向溝通，執行者可以向指揮官詢問
"""

import asyncio
import json
import re
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class ACLMessageType(Enum):
    """ACL 訊息類型"""
    WRITE = "write"
    SHELL = "shell"
    READ = "read"
    ASK = "ask"
    ANSWER = "answer"
    RESULT = "result"
    ERROR = "error"
    CONFIRM = "confirm"


@dataclass
class ACLMessage:
    """ACL 訊息"""
    type: ACLMessageType
    content: str
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_xml(self) -> str:
        """轉換為 XML 格式"""
        if self.type == ACLMessageType.WRITE:
            return f'<write file="{self.metadata.get("file", "")}">\n{self.content}\n</write>'
        elif self.type == ACLMessageType.READ:
            return f'<read file="{self.metadata.get("file", "")}"></read>'
        elif self.type == ACLMessageType.ASK:
            return f'<ask>{self.content}</ask>'
        elif self.type == ACLMessageType.ANSWER:
            return f'<answer>{self.content}</answer>'
        elif self.type == ACLMessageType.RESULT:
            return f'<result>{self.content}</result>'
        elif self.type == ACLMessageType.ERROR:
            return f'<error>{self.content}</error>'
        elif self.type == ACLMessageType.SHELL:
            return f'<shell>{self.content}</shell>'
        return self.content
    
    @staticmethod
    def from_xml(xml_str: str) -> Optional['ACLMessage']:
        """從 XML 解析"""
        # 解析 write
        match = re.search(r'<write file="([^"]+)">\s*(.+?)\s*</write>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.WRITE, match.group(2).strip(), {"file": match.group(1)})
        
        # 解析 read
        match = re.search(r'<read file="([^"]+)">\s*</read>', xml_str)
        if match:
            return ACLMessage(ACLMessageType.READ, "", {"file": match.group(1)})
        
        # 解析 ask
        match = re.search(r'<ask>(.+?)</ask>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.ASK, match.group(1).strip())
        
        # 解析 answer
        match = re.search(r'<answer>(.+?)</answer>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.ANSWER, match.group(1).strip())
        
        # 解析 result
        match = re.search(r'<result>(.+?)</result>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.RESULT, match.group(1).strip())
        
        # 解析 error
        match = re.search(r'<error>(.+?)</error>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.ERROR, match.group(1).strip())
        
        # 解析 shell
        match = re.search(r'<shell>(.+?)</shell>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.SHELL, match.group(1).strip())
        
        return None


class ACLHandler(ABC):
    """ACL 訊息處理器（抽象類）"""
    
    @abstractmethod
    async def on_ask(self, question: str) -> str:
        """處理詢問"""
        pass
    
    @abstractmethod
    async def on_write(self, file_path: str, content: str) -> str:
        """處理寫入"""
        pass
    
    @abstractmethod
    async def on_shell(self, command: str) -> str:
        """處理命令執行"""
        pass
    
    @abstractmethod
    async def on_read(self, file_path: str) -> str:
        """處理讀取"""
        pass


class ACLConsoleHandler(ACLHandler):
    """命令列模式處理器（不需要 WebSocket）"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
    
    async def on_ask(self, question: str) -> str:
        """詢問人類使用者"""
        print(f"\n❓ AI 詢問: {question}")
        answer = input("➤ 你的回覆: ")
        return answer
    
    async def on_write(self, file_path: str, content: str) -> str:
        """寫入檔案"""
        from pathlib import Path
        path = Path(self.root_dir) / file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"✓ 已寫入: {file_path}"
    
    async def on_shell(self, command: str) -> str:
        """執行命令"""
        import subprocess
        try:
            result = subprocess.run(
                command, shell=True, cwd=self.root_dir,
                capture_output=True, text=True, timeout=60
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"Error: {e}"
    
    async def on_read(self, file_path: str) -> str:
        """讀取檔案"""
        from pathlib import Path
        path = Path(self.root_dir) / file_path
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error: {e}"


class ACLParser:
    """ACL 指令解析器"""
    
    def __init__(self, handler: ACLHandler):
        self.handler = handler
    
    async def execute(self, xml_content: str) -> str:
        """執行 ACL 指令"""
        # 移除思考過程
        xml_content = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', xml_content)
        
        results = []
        
        # 找所有 write 指令
        write_pattern = r'<write file="([^"]+)">\s*(.+?)\s*</write>'
        for match in re.finditer(write_pattern, xml_content, re.DOTALL):
            file_path = match.group(1).strip()
            content = match.group(2).strip()
            result = await self.handler.on_write(file_path, content)
            results.append(f"📝 寫入: {file_path}\n{result}")
        
        # 找所有 shell 指令
        shell_pattern = r'<shell>\s*(.+?)\s*</shell>'
        for match in re.finditer(shell_pattern, xml_content, re.DOTALL):
            command = match.group(1).strip()
            if command and len(command) > 1:
                result = await self.handler.on_shell(command)
                results.append(f"⚡ 執行: {command}\n{result[:500]}")
        
        # 找所有 read 指令
        read_pattern = r'<read file="([^"]+)">\s*</read>'
        for match in re.finditer(read_pattern, xml_content):
            file_path = match.group(1).strip()
            result = await self.handler.on_read(file_path)
            results.append(f"📄 讀取: {file_path}\n{result[:500]}")
        
        # 找所有 ask 指令（需要詢問）
        ask_pattern = r'<ask>\s*(.+?)\s*</ask>'
        for match in re.finditer(ask_pattern, xml_content, re.DOTALL):
            question = match.group(1).strip()
            answer = await self.handler.on_ask(question)
            results.append(f"❓ 詢問: {question}\n➤ 回覆: {answer}")
        
        return "\n\n".join(results) if results else "沒有執行任何指令"


# 方便使用的函數
async def parse_and_execute(xml_content: str, root_dir: str = ".") -> str:
    """解析並執行 ACL 指令"""
    handler = ACLConsoleHandler(root_dir)
    parser = ACLParser(handler)
    return await parser.execute(xml_content)
