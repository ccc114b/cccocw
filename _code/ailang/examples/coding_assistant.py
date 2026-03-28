"""
AIL 程式開發助手示範
類似 OpenCode 的 AI 程式開發系統
"""

import asyncio
import os
from ailang import Agent, goal, get_tracker, init_openrouter


# 初始化 OpenRouter
api_key = os.environ.get("OPENROUTER_API_KEY")
if api_key:
    init_openrouter(api_key, model="openrouter/free")
    print("✓ OpenRouter 初始化成功")
else:
    print("⚠️ 未找到 OPENROUTER_API_KEY，使用模擬模式")


class CodeAssistant:
    """
    類似 OpenCode 的 AI 程式開發助手
    
    功能：
    - 理解需求
    - 搜尋資料
    - 編寫程式碼
    - 執行測試
    - 審查代碼
    """
    
    def __init__(self):
        # 專業代理
        self.requirement_analyzer = Agent("requirement_analyzer")
        self.researcher = Agent("researcher")
        self.coder = Agent("coder")
        self.tester = Agent("tester")
        self.reviewer = Agent("reviewer")
    
    @goal()
    async def develop(self, task: str):
        """開發流程"""
        
        print(f"\n{'='*50}")
        print(f"  程式開發助手")
        print(f"{'='*50}")
        print(f"\n任務: {task}")
        
        # 1. 分析需求
        print(f"\n[1/5] 📝 分析需求...")
        requirements = await self._analyze_requirement(task)
        
        # 2. 搜尋相關資訊
        print(f"\n[2/5] 🔍 搜尋資訊...")
        research = await self._do_research(requirements)
        
        # 3. 編寫程式碼
        print(f"\n[3/5] 💻 編寫程式碼...")
        code = await self._write_code(requirements, research)
        
        # 4. 執行測試
        print(f"\n[4/5] 🧪 執行測試...")
        tests = await self._run_tests(code)
        
        # 5. 審查代碼
        print(f"\n[5/5] 👀 審查代碼...")
        review = await self._review_code(code, tests)
        
        # 生成報告
        report = self._generate_report(task, code, tests, review)
        
        return report
    
    async def _analyze_requirement(self, task: str):
        """分析需求"""
        result = await self.requirement_analyzer(task=f"分析這個需求: {task}")
        return result
    
    async def _do_research(self, requirements: str):
        """搜尋相關資訊"""
        result = await self.researcher(task=f"搜尋相關技術資料: {requirements}")
        return result
    
    async def _write_code(self, requirements: str, research: str):
        """編寫程式碼"""
        result = await self.coder(task=f"""
            根據以下需求編寫程式碼：
            
            需求: {requirements}
            
            參考資料: {research}
        """)
        return result
    
    async def _run_tests(self, code: str):
        """執行測試"""
        result = await self.tester(task=f"為以下程式碼設計測試: {code[:200]}...")
        return result
    
    async def _review_code(self, code: str, tests: str):
        """審查代碼"""
        result = await self.reviewer(task=f"審查程式碼: {code[:200]}...")
        return result
    
    def _generate_report(self, task, code, tests, review):
        """生成報告"""
        return f"""
{'='*50}
     程式開發報告
{'='*50}

📋 任務: {task}

💻 程式碼:
{code}

🧪 測試:
{tests}

👀 審查意見:
{review}

{'='*50}
        """


class DebugAssistant:
    """
    AI 除錯助手
    類似 AI 程式碼修復功能
    """
    
    def __init__(self):
        self.analyzer = Agent("error_analyzer")
        self.fixer = Agent("code_fixer")
        self.validator = Agent("validator")
    
    @goal()
    async def debug(self, error: str, code: str):
        """除錯流程"""
        
        print(f"\n{'='*50}")
        print(f"  AI 除錯助手")
        print(f"{'='*50}")
        print(f"\n錯誤: {error}")
        
        # 1. 分析錯誤
        print(f"\n[1/3] 🔎 分析錯誤...")
        analysis = await self.analyzer(task=f"分析這個錯誤: {error}")
        
        # 2. 修復程式碼
        print(f"\n[2/3] 🔧 修復程式碼...")
        fixed = await self.fixer(task=f"修復這段程式碼: {code}")
        
        # 3. 驗證修復
        print(f"\n[3/3] ✅ 驗證修復...")
        result = await self.validator(task=f"驗證修復: {fixed}")
        
        return {
            "error": error,
            "analysis": analysis,
            "fixed_code": fixed,
            "validation": result
        }


async def demo():
    """演示"""
    print("\n" + "⌨️"*25)
    print("   AIL 程式開發助手 (類似 OpenCode)")
    print("⌨️"*25)
    
    assistant = CodeAssistant()
    
    result = await assistant.develop(
        task="建立一個天氣查詢應用程式，需要顯示未來7天的天氣"
    )
    
    print(result)
    
    tracker = get_tracker()
    print("\n📊 任務統計:")
    print(tracker.summary())


async def demo_debug():
    """除錯助手演示"""
    print("\n" + "🔧"*25)
    print("   AIL AI 除錯助手")
    print("🔧"*25)
    
    debugger = DebugAssistant()
    
    result = await debugger.debug(
        error="TypeError: Cannot read property 'name' of undefined",
        code="const user = users.find(u => u.id === id); console.log(user.name);"
    )
    
    print(f"\n錯誤分析: {result['analysis']}")
    print(f"修復後程式碼: {result['fixed_code']}")
    print(f"驗證結果: {result['validation']}")


async def main():
    await demo()
    await demo_debug()


if __name__ == "__main__":
    asyncio.run(main())
