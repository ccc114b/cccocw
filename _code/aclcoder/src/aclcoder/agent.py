"""
Ollama Agent - AI 模型客户端
"""

import aiohttp
from typing import Optional


class OllamaAgent:
    """
    Ollama 模型客户端 (使用 HTTP API)
    """
    
    def __init__(self, model: str = "minimax-m2.5:cloud"):
        self.model = model
    
    async def __call__(self, prompt: str, system_prompt: str = "") -> str:
        """执行任务"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status != 200:
                        return f"Error: {await resp.text()}"
                    result = await resp.json()
                    return result.get("response", "").strip()
        except Exception as e:
            return f"Error: {e}"
