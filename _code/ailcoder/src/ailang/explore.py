"""
AIL Explore - 並行探索多解法
讓 AI 同時嘗試多種方法，選擇最佳結果
"""

import asyncio
from typing import List, Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import random


class VoteStrategy(Enum):
    """投票策略"""
    CONFIDENCE = "confidence"      # 根據信心度
    MAJORITY = "majority"          # 多數投票
    RANDOM = "random"             # 隨機選擇
    FIRST = "first"               # 選第一個


@dataclass
class ExplorationResult:
    """探索結果"""
    result: Any
    confidence: float
    method_name: str
    metadata: Dict = field(default_factory=dict)


class Explorer:
    """
    並行探索器
    
    用法:
        result = await explore([
            lambda: await solve_method_a(),
            lambda: await solve_method_b(),
            lambda: await solve_method_c(),
        ]).vote()
    """
    
    def __init__(self, methods: List[Callable]):
        self.methods = methods
        self.results: List[ExplorationResult] = []
        self._llm_client = None
    
    def with_llm(self, client):
        """設置 LLM 客戶端用於評估"""
        self._llm_client = client
        return self
    
    async def run_all(self, timeout: float = 30.0) -> List[ExplorationResult]:
        """並行執行所有方法"""
        tasks = [self._run_method(m, i) for i, m in enumerate(self.methods)]
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
            
            for r in results:
                if isinstance(r, Exception):
                    print(f"方法執行錯誤: {r}")
                elif r is not None:
                    self.results.append(r)
                    
        except asyncio.TimeoutError:
            print(f"探索超時 ({timeout}秒)")
        
        return self.results
    
    async def _run_method(self, method: Callable, index: int) -> Optional[ExplorationResult]:
        """執行單個方法"""
        try:
            result = method()
            
            # 如果是協程則等待
            if asyncio.iscoroutine(result):
                result = await result
            
            # 嘗試提取信心度
            confidence = 0.5  # 預設
            if hasattr(result, 'confidence'):
                confidence = result.confidence
            elif isinstance(result, dict) and 'confidence' in result:
                confidence = result['confidence']
            
            method_name = getattr(method, '__name__', f'method_{index}')
            
            return ExplorationResult(
                result=result,
                confidence=confidence,
                method_name=method_name
            )
            
        except Exception as e:
            print(f"方法 {index} 錯誤: {e}")
            return None
    
    async def vote(
        self, 
        strategy: VoteStrategy = VoteStrategy.CONFIDENCE,
        llm_judge_prompt: str = None
    ) -> ExplorationResult:
        """投票選擇最佳結果"""
        if not self.results:
            raise ValueError("沒有可用的結果")
        
        if len(self.results) == 1:
            return self.results[0]
        
        # 策略 1: 信心度
        if strategy == VoteStrategy.CONFIDENCE:
            best = max(self.results, key=lambda x: x.confidence)
            print(f"選擇: {best.method_name} (信心度: {best.confidence:.2f})")
            return best
        
        # 策略 2: 多數投票（需要 LLM）
        elif strategy == VoteStrategy.MAJORITY:
            if not self._llm_client and not llm_judge_prompt:
                # 退回到信心度
                return await self.vote(VoteStrategy.CONFIDENCE)
            
            return await self._llm_judge(llm_judge_prompt)
        
        # 策略 3: 隨機
        elif strategy == VoteStrategy.RANDOM:
            return random.choice(self.results)
        
        # 策略 4: 第一個
        else:
            return self.results[0]
    
    async def _llm_judge(self, prompt: str) -> ExplorationResult:
        """用 LLM 判斷哪個結果最好"""
        results_text = "\n".join([
            f"{i+1}. [{r.method_name}] {r.result} (信心度: {r.confidence})"
            for i, r in enumerate(self.results)
        ])
        
        full_prompt = f"{prompt}\n\n結果:\n{results_text}\n\n請選擇最佳結果並說明原因。"
        
        # 這裡調用 LLM
        # decision = await self._llm_client.chat(full_prompt)
        
        # 暫時用信心度
        return await self.vote(VoteStrategy.CONFIDENCE)
    
    def get_all(self) -> List[ExplorationResult]:
        """取得所有結果"""
        return self.results
    
    def describe(self) -> str:
        """描述探索結果"""
        if not self.results:
            return "無結果"
        
        lines = ["探索結果:"]
        for i, r in enumerate(self.results):
            lines.append(f"  {i+1}. {r.method_name}: {r.result} (置信度: {r.confidence:.2f})")
        
        return "\n".join(lines)


async def explore(
    methods: List[Callable],
    *,
    timeout: float = 30.0,
    vote_strategy: VoteStrategy = VoteStrategy.CONFIDENCE,
    llm_client = None
) -> ExplorationResult:
    """
    並行探索多個解法
    
    用法:
        result = await explore([
            lambda: solution_a(),
            lambda: solution_b(),
            lambda: solution_c(),
        ])
        
        # 或带投票
        result = await explore(methods, vote_strategy=VoteStrategy.MAJORITY)
    """
    explorer = Explorer(methods)
    
    if llm_client:
        explorer.with_llm(llm_client)
    
    await explorer.run_all(timeout=timeout)
    return await explorer.vote(strategy=vote_strategy)


async def explore_all(
    methods: List[Callable],
    timeout: float = 30.0
) -> List[ExplorationResult]:
    """
    並行探索，返回所有結果
    
    用法:
        results = await explore_all([
            lambda: solution_a(),
            lambda: solution_b(),
        ])
        
        for r in results:
            print(f"{r.method_name}: {r.result}")
    """
    explorer = Explorer(methods)
    return await explorer.run_all(timeout=timeout)
