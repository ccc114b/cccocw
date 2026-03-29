"""
ACL Handler - ACL 协议消息处理器
负责解析和执行 ACL 格式的消息
"""

import re
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from .message_bus import Message, MessageHandler, MessageType


class ACLMessageType(Enum):
    """ACL 消息类型"""
    WRITE = "write"
    SHELL = "shell"
    READ = "read"
    ASK = "ask"
    ANSWER = "answer"
    RESULT = "result"
    ERROR = "error"


@dataclass
class ACLMessage:
    """ACL 消息"""
    type: ACLMessageType
    content: str
    metadata: dict = None


class ACLFileHandler(MessageHandler):
    """ACL 文件系统处理器"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
    
    async def handle(self, message: Message) -> Optional[Message]:
        """处理 ACL 消息"""
        acl_type = message.metadata.get("acl_type")
        
        if acl_type == ACLMessageType.WRITE:
            return await self._handle_write(message)
        elif acl_type == ACLMessageType.SHELL:
            return await self._handle_shell(message)
        elif acl_type == ACLMessageType.READ:
            return await self._handle_read(message)
        elif acl_type == ACLMessageType.ASK:
            return None  # 由 Executor 透過 Commander 處理
        
        return None
    
    async def _handle_write(self, message: Message) -> Message:
        """写入文件"""
        file_path = message.metadata.get("file_path", "")
        content = message.content
        
        path = self.root_dir / file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        
        return Message(
            type=MessageType.RESPONSE,
            content=f"✓ 已写入: {file_path}",
            sender="acl_handler"
        )
    
    async def _handle_shell(self, message: Message) -> Message:
        """执行命令"""
        command = message.content
        
        try:
            result = subprocess.run(
                command, shell=True, cwd=str(self.root_dir),
                capture_output=True, text=True, timeout=60
            )
            output = result.stdout or result.stderr
        except Exception as e:
            output = f"Error: {e}"
        
        return Message(
            type=MessageType.RESPONSE,
            content=output,
            sender="acl_handler"
        )
    
    async def _handle_read(self, message: Message) -> Message:
        """读取文件"""
        file_path = message.metadata.get("file_path", "")
        path = self.root_dir / file_path
        
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            content = f"Error: {e}"
        
        return Message(
            type=MessageType.RESPONSE,
            content=content,
            sender="acl_handler"
        )
    
    async def _handle_ask(self, message: Message) -> Message:
        """询问（交互模式）"""
        question = message.content
        print(f"\n❓ AI 询问: {question}")
        answer = input("➤ 你的回复: ")
        
        return Message(
            type=MessageType.RESPONSE,
            content=answer,
            sender="acl_handler"
        )


class ACLParser:
    """
    ACL 协议解析器
    
    负责：
    - 解析 ACL 格式的文本
    - 转换为 MessageBus 消息
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def parse(self, text: str) -> List[Message]:
        """解析文本为消息列表"""
        # 移除思考过程
        text = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', text)
        
        messages = []
        
        # 解析 write - 使用更宽松的正则
        pattern = r'<write file="([^"]+)">(.*?)</write>'
        for match in re.finditer(pattern, text, re.DOTALL):
            file_path = match.group(1).strip()
            content = match.group(2).strip()
            messages.append(Message(
                type=MessageType.COMMAND,
                content=content,
                metadata={
                    "acl_type": ACLMessageType.WRITE,
                    "file_path": file_path
                }
            ))
        
        # 解析 shell
        for match in re.finditer(r'<shell>\s*(.+?)\s*</shell>', text, re.DOTALL):
            cmd = match.group(1).strip()
            if cmd and len(cmd) > 1:
                messages.append(Message(
                    type=MessageType.COMMAND,
                    content=cmd,
                    metadata={"acl_type": ACLMessageType.SHELL}
                ))
        
        # 解析 read
        for match in re.finditer(r'<read file="([^"]+)">\s*</read>', text):
            messages.append(Message(
                type=MessageType.QUERY,
                content="",
                metadata={
                    "acl_type": ACLMessageType.READ,
                    "file_path": match.group(1).strip()
                }
            ))
        
        # 解析 ask
        for match in re.finditer(r'<ask>\s*(.+?)\s*</ask>', text, re.DOTALL):
            messages.append(Message(
                type=MessageType.QUERY,
                content=match.group(1).strip(),
                metadata={"acl_type": ACLMessageType.ASK}
            ))
        
        return messages
    
    def extract_asks(self, text: str) -> List[str]:
        """提取所有 ask 问题"""
        text = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', text)
        ask_pattern = r'<ask>\s*(.+?)\s*</ask>'
        questions = re.findall(ask_pattern, text, re.DOTALL)
        return [q.strip() for q in questions]
