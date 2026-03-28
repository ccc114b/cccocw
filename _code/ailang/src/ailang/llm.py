"""
AIL LLM - MiniMax M2.5 整合模組
"""

import os
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """聊天訊息"""
    role: str
    content: str


class MiniMaxClient:
    """
    MiniMax API 客戶端
    
    用法:
        client = MiniMaxClient(api_key="your-key")
        result = await client.chat("你好，請自我介紹")
    """
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.minimax.io",
        model: str = "MiniMax-M2.5",
        group_id: str = None
    ):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self.group_id = group_id
    
    async def chat(
        self,
        message: str,
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        history: List[ChatMessage] = None
    ) -> str:
        """發送聊天請求"""
        import aiohttp
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": message})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 檢測 API 類型
        if "/anthropic/" in self.base_url:
            # Anthropic 兼容格式 (OpenCode/MiniMax)
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            endpoint = f"{self.base_url}/messages"
            
        elif "/openrouter.ai" in self.base_url:
            # OpenRouter 格式 (OpenAI 兼容)
            headers["HTTP-Referer"] = "https://ailang.dev"
            headers["X-Title"] = "AIL"
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            endpoint = f"{self.base_url}/api/v1/chat/completions"
            
        else:
            # MiniMax 原生格式
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if self.group_id:
                payload["group_id"] = self.group_id
            
            endpoint = f"{self.base_url}/v1/text/chatcompletion_v2"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                json=payload,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"API Error: {error}")
                
                data = await resp.json()
                
                # 根據端點格式解析回應
                if "/anthropic/" in self.base_url:
                    if "content" in data:
                        return data["content"][0]["text"]
                elif "/openrouter.ai" in self.base_url:
                    # OpenRouter 格式
                    if "choices" in data and data["choices"]:
                        return data["choices"][0]["message"]["content"]
                    elif "error" in data:
                        raise Exception(f"API Error: {data['error']}")
                else:
                    if "choices" not in data or not data["choices"]:
                        raise Exception(f"API Error: {data}")
                    return data["choices"][0]["message"]["content"]
    
    async def chat_stream(
        self,
        message: str,
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        import aiohttp
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/text/chatcompletion_v2",
                json=payload,
                headers=headers
            ) as resp:
                async for line in resp.content:
                    if line:
                        text = line.decode().strip()
                        if text.startswith("data: "):
                            data = json.loads(text[6:])
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]


class MiniMaxAgent:
    """
    使用 MiniMax M2.5 的 Agent
    
    用法:
        agent = MiniMaxAgent("researcher", api_key="your-key")
        result = await agent(task="找AI新聞")
    """
    
    def __init__(
        self,
        name: str,
        api_key: str = None,
        model: str = "MiniMax-M2.5",
        system_prompt: str = None,
        client: MiniMaxClient = None
    ):
        self.name = name
        # 優先使用傳入的 client，其次使用全域 client
        self.client = client or get_client() or MiniMaxClient(api_key=api_key, model=model)
        self.system_prompt = system_prompt or f"You are {name}, a helpful AI assistant."
        self._history: List[ChatMessage] = []
    
    async def __call__(self, task: str, **kwargs) -> str:
        """執行任務"""
        # 構建完整 prompt
        prompt = task
        if kwargs:
            context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            prompt = f"{task}\nContext: {context}"
        
        # 調用 API
        result = await self.client.chat(
            message=prompt,
            system_prompt=self.system_prompt,
            history=self._history
        )
        
        # 記錄歷史
        self._history.append(ChatMessage(role="user", content=task))
        self._history.append(ChatMessage(role="assistant", content=result))
        
        return result
    
    def history(self) -> List[Dict]:
        """取得對話歷史"""
        return [{"role": m.role, "content": m.content} for m in self._history]
    
    def clear_history(self) -> None:
        """清除歷史"""
        self._history.clear()


# 全域客戶端
_default_client: Optional[MiniMaxClient] = None


def init_minimax(api_key: str = None, base_url: str = None, model: str = "MiniMax-M2.5", group_id: str = None):
    """初始化 MiniMax 客戶端"""
    global _default_client
    
    # 如果沒有提供 api_key，使用 OpenRouter 免費版本
    if not api_key:
        api_key = "OPENROUTER"
    
    _default_client = MiniMaxClient(
        api_key=api_key,
        base_url=base_url or "https://openrouter.ai",
        model=model,
        group_id=group_id
    )


def init_openrouter(api_key: str, model: str = "minimax/minimax-m2.5:free"):
    """初始化 OpenRouter 客戶端"""
    global _default_client
    _default_client = MiniMaxClient(
        api_key=api_key,
        base_url="https://openrouter.ai",
        model=model
    )


def get_client() -> Optional[MiniMaxClient]:
    """取得預設客戶端"""
    return _default_client


async def chat(message: str, **kwargs) -> str:
    """快速聊天"""
    if not _default_client:
        raise ValueError("請先調用 init_minimax(api_key) 初始化")
    return await _default_client.chat(message, **kwargs)
