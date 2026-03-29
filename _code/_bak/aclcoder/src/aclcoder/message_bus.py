"""
Message Bus - 通用消息总线
负责消息的路由、订阅、发布
"""

import asyncio
from typing import List, Callable, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import asyncio


class MessageType(Enum):
    """通用消息类型"""
    TEXT = "text"
    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class Message:
    """消息"""
    type: MessageType
    content: str
    sender: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageHandler(ABC):
    """消息处理器接口"""
    
    @abstractmethod
    async def handle(self, message: Message) -> Optional[Message]:
        """处理消息，返回响应消息（可选）"""
        pass


class MessageBus:
    """
    通用消息总线
    
    负责：
    - 消息路由
    - 订阅/发布
    - 消息队列管理
    
    不包含任何协议特定的处理逻辑
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self._handlers: Dict[MessageType, List[MessageHandler]] = {
            MessageType.TEXT: [],
            MessageType.COMMAND: [],
            MessageType.QUERY: [],
            MessageType.RESPONSE: [],
            MessageType.ERROR: [],
        }
        self._subscribers: Dict[str, List[Callable]] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    def register_handler(self, message_type: MessageType, handler: MessageHandler):
        """注册消息处理器"""
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
    
    def subscribe(self, event: str, callback: Callable):
        """订阅事件"""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)
    
    def _publish(self, event: str, data: Any):
        """发布事件"""
        for callback in self._subscribers.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(data))
                else:
                    callback(data)
            except Exception as e:
                if self.debug:
                    print(f"Callback error: {e}")
    
    async def send(self, message: Message):
        """发送消息"""
        self._publish("on_message", message)
        
        # 查找对应的处理器
        handlers = self._handlers.get(message.type, [])
        
        for handler in handlers:
            try:
                response = await handler.handle(message)
                if response:
                    self._publish("on_response", response)
            except Exception as e:
                if self.debug:
                    print(f"Handler error: {e}")
                error_msg = Message(
                    type=MessageType.ERROR,
                    content=str(e),
                    sender="message_bus"
                )
                self._publish("on_error", error_msg)
    
    async def publish(self, topic: str, data: Any):
        """发布主题消息"""
        self._publish(topic, data)
    
    def subscribe_topic(self, topic: str, callback: Callable):
        """订阅主题"""
        self.subscribe(f"topic:{topic}", callback)
