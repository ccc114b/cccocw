"""
AICommander - AI 指挥官
负责审核消息，决定是否执行 ACL 指令
"""

from .agent import OllamaAgent
from .acl import ACL_SPEC


class AICommander:
    """
    AI 指挥官
    - 记住项目特性
    - 回答 Executor 的问题
    - 审核代码决定是否执行
    """
    
    def __init__(self, model: str = "minimax-m2.5:cloud"):
        self.agent = OllamaAgent(model)
        self.memory = ""  # 记住的项目特性
        self.system_prompt = f"""你是 AICommander，一个专业的技术经理。

## ACL 规格
{ACL_SPEC}

## 角色
1. 记住项目需求
2. 回答 Executor 的问题
3. 审核生成的代码

## 重要规则
1. 用繁体中文
2. 根据记忆的项目特性回答问题"""
    
    def remember(self, info: str):
        """记住项目特性"""
        self.memory = info
        print(f"\n[Commander 記住]: {info}")
    
    async def answer(self, question: str) -> str:
        """根据记忆回答问题"""
        prompt = f"""## 項目記憶
{self.memory}

## Executor 問題
{question}

請根據項目記憶回答問題。"""
        return await self.agent(prompt, self.system_prompt)
    
    async def review(self, executor_output: str) -> str:
        """审核 Executor 的输出，给出下一步指示"""
        import re
        
        # 检查是否有 write - 直接返回包含 write 的部分
        if "<write" in executor_output:
            # 提取所有 <write> 标签
            write_matches = re.findall(r'<write file="([^"]+)">(.*?)</write>', executor_output, re.DOTALL)
            if write_matches:
                # 返回完整的 write 标签
                result = ""
                for file_path, content in write_matches:
                    result += f'<write file="{file_path}">\n{content}\n</write>\n'
                return result
        
        # 检查是否有 ask
        if "<ask>" in executor_output:
            # 在问问题，用记忆回答
            answer = await self.answer(executor_output)
            return f"{answer}\n\n請根據以上回答生成代碼，用 <write> 標籤輸出。"
        
        return "請繼續生成代碼，用 <write> 標籤輸出。"
