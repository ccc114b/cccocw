"""
AIL 旅遊規劃代理示範
使用 AIL 框架實現智能旅遊規劃系統
"""

import asyncio
import os
from ailang import Agent, goal, get_tracker, init_openrouter, init_ollama


# 優先使用本地 Ollama
try:
    init_ollama(model="minimax-m2.5:cloud")
    print("✓ Ollama 初始化成功 (MiniMax M2.5 雲端)")
except Exception as e:
    print(f"⚠️ Ollama 連接失敗: {e}")
    # 備用 OpenRouter
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        init_openrouter(api_key, model="openrouter/free")
        print("✓ OpenRouter 初始化成功")
    else:
        print("⚠️ 未找到 OPENROUTER_API_KEY，使用模擬模式")


class TravelPlanner:
    """
    旅遊規劃代理
    
    功能：
    - 搜尋景點
    - 規劃行程
    - 計算預算
    - 生成報告
    """
    
    def __init__(self, destination: str, days: int, budget: float):
        self.destination = destination
        self.days = days
        self.budget = budget
        
        # 專業代理
        self.researcher = Agent("researcher")
        self.planner = Agent("planner")
        self.budget_manager = Agent("budget_manager")
    
    @goal()
    async def plan(self):
        """主規劃流程"""
        
        print(f"\n{'='*50}")
        print(f"  旅遊規劃系統: {self.destination}")
        print(f"{'='*50}")
        
        # 1. 研究當地資訊
        print(f"\n[1/4] 🔍 研究當地資訊...")
        attractions = await self._research_attractions()
        
        # 2. 規劃行程
        print(f"\n[2/4] 📋 規劃行程...")
        itinerary = await self._plan_itinerary(attractions)
        
        # 3. 計算預算
        print(f"\n[3/4] 💰 計算預算...")
        budget_plan = await self._calculate_budget(itinerary)
        
        # 4. 生成報告
        print(f"\n[4/4] 📄 生成報告...")
        report = self._generate_report(itinerary, budget_plan)
        
        return report
    
    async def _research_attractions(self):
        """研究當地景點"""
        task = f"搜尋 {self.destination} 的熱門景點"
        return await self.researcher(task=task)
    
    async def _plan_itinerary(self, attractions):
        """規劃每日行程"""
        task = f"為 {self.destination} 規劃 {self.days} 天行程"
        return await self.planner(task=task)
    
    async def _calculate_budget(self, itinerary):
        """計算預算"""
        task = f"計算 {self.days} 天旅遊預算，目標 ${self.budget}"
        return await self.budget_manager(task=task)
    
    def _generate_report(self, itinerary, budget_plan):
        """生成最終報告"""
        return f"""
{'='*50}
     旅遊規劃報告: {self.destination}
{'='*50}

📅  天數: {self.days} 天
💰  預算: ${self.budget}

📍  景點研究:
{itinerary}

💵  預算規劃:
{budget_plan}

{'='*50}
        """


async def demo():
    """演示"""
    print("\n" + "🎬"*25)
    print("   AIL 旅遊規劃代理")
    print("🎬"*25)
    
    planner = TravelPlanner(
        destination="日本東京",
        days=5,
        budget=3000
    )
    
    report = await planner.plan()
    print(report)
    
    tracker = get_tracker()
    print("\n📊 任務統計:")
    print(tracker.summary())


if __name__ == "__main__":
    asyncio.run(demo())
