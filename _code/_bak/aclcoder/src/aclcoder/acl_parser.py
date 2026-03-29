"""
ACL Parser - ACL 通讯协议解析器
"""

import re
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple


class ACLHandler(ABC):
    """ACL 消息处理器（抽象类）"""
    
    @abstractmethod
    async def on_write(self, file_path: str, content: str) -> str:
        """处理写入"""
        pass
    
    @abstractmethod
    async def on_shell(self, command: str) -> str:
        """处理命令执行"""
        pass
    
    @abstractmethod
    async def on_read(self, file_path: str) -> str:
        """处理读取"""
        pass
    
    @abstractmethod
    async def on_ask(self, question: str) -> str:
        """处理询问"""
        pass


class ACLConsoleHandler(ACLHandler):
    """命令行模式处理器"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
    
    async def on_write(self, file_path: str, content: str) -> str:
        """写入文件"""
        path = self.root_dir / file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"✓ 已写入: {file_path}"
    
    async def on_shell(self, command: str) -> str:
        """执行命令"""
        try:
            result = subprocess.run(
                command, shell=True, cwd=str(self.root_dir),
                capture_output=True, text=True, timeout=60
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"Error: {e}"
    
    async def on_read(self, file_path: str) -> str:
        """读取文件"""
        path = self.root_dir / file_path
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error: {e}"
    
    async def on_ask(self, question: str) -> str:
        """询问（交互模式）"""
        print(f"\n❓ AI 询问: {question}")
        return input("➤ 你的回复: ")


class ACLParser:
    """ACL 指令解析器"""
    
    def __init__(self, handler: ACLHandler, debug: bool = False):
        self.handler = handler
        self.debug = debug
    
    def log(self, direction: str, message: str):
        """记录消息"""
        if self.debug:
            arrow = "→" if direction == "→" else "←"
            print(f"\nACL {arrow} AI:")
            print("-" * 40)
            print(message[:500] + "..." if len(message) > 500 else message)
    
    async def execute(self, xml_content: str) -> str:
        """执行 ACL 指令"""
        self.log("←", xml_content)
        
        # 移除思考过程
        xml_content = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', xml_content)
        
        results = []
        
        # 找所有 write 指令
        write_pattern = r'<write file="([^"]+)">\s*(.+?)\s*</write>'
        for match in re.finditer(write_pattern, xml_content, re.DOTALL):
            file_path = match.group(1).strip()
            content = match.group(2).strip()
            result = await self.handler.on_write(file_path, content)
            self.log("→", f"<write file=\"{file_path}\">...内容...</write>")
            results.append(f"📝 写入: {file_path}\n{result}")
        
        # 找所有 shell 指令
        shell_pattern = r'<shell>\s*(.+?)\s*</shell>'
        for match in re.finditer(shell_pattern, xml_content, re.DOTALL):
            command = match.group(1).strip()
            if command and len(command) > 1:
                result = await self.handler.on_shell(command)
                results.append(f"⚡ 执行: {command}\n{result[:500]}")
        
        # 找所有 read 指令
        read_pattern = r'<read file="([^"]+)">\s*</read>'
        for match in re.finditer(read_pattern, xml_content):
            file_path = match.group(1).strip()
            result = await self.handler.on_read(file_path)
            results.append(f"📄 读取: {file_path}\n{result[:500]}")
        
        return "\n\n".join(results) if results else "没有执行任何指令"
    
    def extract_asks(self, xml_content: str) -> List[str]:
        """提取所有 ask 指令的问题"""
        # 移除思考过程
        xml_content = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', xml_content)
        
        ask_pattern = r'<ask>\s*(.+?)\s*</ask>'
        questions = re.findall(ask_pattern, xml_content, re.DOTALL)
        return [q.strip() for q in questions]


async def parse_and_execute(xml_content: str, root_dir: str = ".") -> str:
    """解析并执行 ACL 指令"""
    handler = ACLConsoleHandler(root_dir)
    parser = ACLParser(handler)
    return await parser.execute(xml_content)
