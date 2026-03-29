"""
AIExecutor - AI 执行器
负责生成代码/内容
"""

from .agent import OllamaAgent
from .acl import ACL_SPEC


class AIExecutor:
    """
    AI 执行器
    - 根据任务生成代码/内容
    - 用 ACL 格式输出
    """
    
    def __init__(self, model: str = "minimax-m2.5:cloud"):
        self.agent = OllamaAgent(model)
        self.system_prompt = f"""你是 AIExecutor，根据任务生成代码。

## ACL 规格
{ACL_SPEC}

## 重要规则
1. 如果需要更多信息，用 <ask> 询问
2. 如果信息足够，用 <write> 生成代码
3. 用繁体中文"""
    
    async def respond(self, message: str) -> str:
        """响应消息"""
        return await self.agent(message, self.system_prompt)
    
    async def execute_task(self, task: str) -> str:
        """执行任务"""
        prompt = f"""任務: {task}

請根據任務生成代碼。用 <write> 標籤輸出。"""
        return await self.agent(prompt, self.system_prompt)
