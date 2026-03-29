"""
AIL AI 原生功能演示
展示 explore、think、goal 三個核心功能
"""

import asyncio
from ailang import (
    explore, explore_all,
    think, ThinkStream,
    goal, get_tracker, Priority
)


# 模擬的不同解法
async def method_dfs():
    """方法 1: DFS 搜索"""
    await asyncio.sleep(0.1)  # 模擬延遲
    return "DFS 結果: [1, 2, 3]"


async def method_bfs():
    """方法 2: BFS 搜索"""
    await asyncio.sleep(0.1)
    return "BFS 結果: [1, 3, 2]"


async def method_dp():
    """方法 3: 動態規劃"""
    await asyncio.sleep(0.1)
    return "DP 結果: [2, 1, 3]"


async def demo_explore():
    """Explore: 並行探索多解法"""
    print("=== Explore: 並行探索 ===")
    
    # 方法 1: 探索並投票選擇最佳
    print("\n1. 探索並選擇最佳:")
    result = await explore([
        method_dfs,
        method_bfs,
        method_dp,
    ])
    print(f"   選擇: {result.method_name}")
    print(f"   結果: {result.result}")
    print(f"   信心度: {result.confidence}")
    
    # 方法 2: 探索所有結果
    print("\n2. 探索所有結果:")
    all_results = await explore_all([
        method_dfs,
        method_bfs,
        method_dp,
    ])
    for r in all_results:
        print(f"   - {r.method_name}: {r.result}")


async def demo_think():
    """Think: 流式思考"""
    print("\n=== Think: 流式思考 ===")
    
    # 使用 Reasoner 鏈
    print("\n1. 推理鏈:")
    result = think("今天天氣好不好") \
        .because("早上的天空是藍色的") \
        .but("現在有雲") \
        .therefore("可能是陰天，但不會下雨") \
        .get_result()
    
    for p in result["premises"]:
        print(f"   因為: {p}")
    for c in result["contradictions"]:
        print(f"   但是: {c}")
    for c in result["conclusions"]:
        print(f"   因此: {c}")
    
    # 使用 ThinkStream
    print("\n2. 思考流:")
    stream = ThinkStream()
    stream.reason("我先嘗試用這個方法")
    stream.observe("發現效果不好")
    stream.hypothesize("也許換個方法更好")
    stream.plan("決定嘗試另一個策略")
    stream.check("驗證新方法是否有效")
    stream.conclude("新方法有效，問題解決")
    
    print(stream.summarize())


async def demo_goal():
    """Goal: 目標宣告"""
    print("\n=== Goal: 目標宣告 ===")
    
    tracker = get_tracker()
    
    # 使用上下文管理器
    print("\n1. 目標上下文:")
    async with goal("翻譯文章") as g:
        tracker.track(tokens=500, cost=0.01)
        await asyncio.sleep(0.1)
        g.complete("翻譯完成")
    print(g.report())
    
    # 使用裝飾器
    print("\n2. 目標裝飾器:")
    
    @goal()
    async def analyze_data():
        await asyncio.sleep(0.1)
        return "分析結果: 數據正常"
    
    result = await analyze_data()
    print(f"   結果: {result}")
    
    # 追蹤統計
    print("\n3. 目標統計:")
    print(tracker.summary())


async def main():
    """執行所有演示"""
    print("AIL AI 原生功能演示\n")
    print("1. explore - 並行探索多解法")
    print("2. think - 流式思考")
    print("3. goal - 目標宣告")
    print()
    
    await demo_explore()
    await demo_think()
    await demo_goal()
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
