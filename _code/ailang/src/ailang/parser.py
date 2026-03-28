"""
AIL Parser - 自訂語法解釋器
解析 AIL 語法並執行
"""

import re
import asyncio
import ast
from typing import Any, Dict, List, Optional
from .core import Agent, ToolRegistry, _memory_store


class AILParser:
    """
    AIL 語法解釋器
    
    用法:
        parser = AILParser()
        result = await parser.execute('''
            let message = "Hello AI"
            print message
        ''')
    """
    
    def __init__(self):
        self._variables: Dict[str, Any] = {}
        self._functions: Dict[str, callable] = {}
    
    async def execute(self, code: str) -> Any:
        """執行 AIL 代碼"""
        lines = self._preprocess(code)
        
        result = None
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("#"):
                i += 1
                continue
            
            result = await self._execute_line(line, lines, i)
            i += 1
        
        return result
    
    def _preprocess(self, code: str) -> List[str]:
        """預處理：處理縮排和多行語句"""
        lines = code.split("\n")
        processed = []
        
        for line in lines:
            stripped = line.rstrip()
            if stripped:
                processed.append(stripped)
        
        return processed
    
    async def _execute_line(self, line: str, all_lines: List[str], index: int) -> Any:
        """執行單行"""
        
        # let 變數宣告
        if match := re.match(r'let\s+(\w+)\s*=\s*(.+)$', line):
            name, value = match.groups()
            self._variables[name] = await self._eval_expr(value)
            return self._variables[name]
        
        # print
        if match := re.match(r'print\s+(.+)$', line):
            expr = match.group(1)
            value = await self._eval_expr(expr)
            print(value)
            return value
        
        # intent 宣告
        if match := re.match(r'intent\s+"(.+)"$', line):
            intent_text = match.group(1)
            return {"intent": intent_text}
        
        # use 引入模組 (模擬)
        if match := re.match(r'use\s+(\w+)$', line):
            module = match.group(1)
            return {"module": module}
        
        # function 定義 (簡化)
        if match := re.match(r'function\s+(\w+)\((.*)\)$', line):
            func_name, params = match.groups()
            body_lines = []
            j = index + 1
            while j < len(all_lines) and all_lines[j].strip() != "end":
                body_lines.append(all_lines[j])
                j += 1
            
            params_list = [p.strip() for p in params.split(",") if p.strip()]
            self._functions[func_name] = {
                "params": params_list,
                "body": body_lines
            }
            return {"function": func_name}
        
        # if 條件 (簡化)
        if match := re.match(r'if\s+(.+)\s+then$', line):
            condition = match.group(1)
            body_lines = []
            j = index + 1
            while j < len(all_lines) and all_lines[j].strip() != "end":
                body_lines.append(all_lines[j])
                j += 1
            
            if await self._eval_condition(condition):
                for bl in body_lines:
                    if bl.strip() and not bl.strip().startswith("else"):
                        await self._execute_line(bl.strip(), body_lines, 0)
            return {"if": condition}
        
        # return
        if match := re.match(r'return\s+(.+)$', line):
            return await self._eval_expr(match.group(1))
        
        # 函數調用
        if match := re.match(r'(\w+)\s*=\s*await\s+(\w+)\((.*)\)$', line):
            var_name, func_name, args = match.groups()
            result = await self._call_function(func_name, args)
            self._variables[var_name] = result
            return result
        
        # await agent
        if match := re.match(r'(\w+)\s*=\s*await\s+agent\("([^"]+)"\s*,\s*([^)]+)\)$', line):
            var_name, agent_name, kwargs_str = match.groups()
            kwargs = self._parse_kwargs(kwargs_str)
            a = Agent(agent_name)
            result = await a(task=kwargs.get("task", ""))
            self._variables[var_name] = result
            return result
        
        return None
    
    async def _eval_expr(self, expr: str) -> Any:
        """簡單表達式求值"""
        expr = expr.strip()
        
        # 字串
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        
        # 數字
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # 布林
        if expr == "true":
            return True
        if expr == "false":
            return False
        
        # 列表
        if expr.startswith("[") and expr.endswith("]"):
            items = expr[1:-1].split(",")
            return [await self._eval_expr(i.strip()) for i in items if i.strip()]
        
        # 變數
        if expr in self._variables:
            return self._variables[expr]
        
        # 簡單運算
        if "+" in expr:
            parts = expr.split("+")
            if len(parts) == 2:
                a = await self._eval_expr(parts[0])
                b = await self._eval_expr(parts[1])
                return str(a) + str(b)
        
        return expr
    
    async def _eval_condition(self, condition: str) -> bool:
        """條件求值"""
        # 簡單比較
        if ">=" in condition:
            parts = condition.split(">=")
            a = await self._eval_expr(parts[0].strip())
            b = await self._eval_expr(parts[1].strip())
            return a >= b
        
        if "==" in condition:
            parts = condition.split("==")
            a = await self._eval_expr(parts[0].strip())
            b = await self._eval_expr(parts[1].strip())
            return a == b
        
        # 布林值
        return bool(await self._eval_expr(condition))
    
    def _parse_kwargs(self, kwargs_str: str) -> Dict[str, str]:
        """解析關鍵字參數"""
        kwargs = {}
        for part in kwargs_str.split(","):
            if ":" in part:
                key, value = part.split(":", 1)
                kwargs[key.strip()] = value.strip().strip('"')
        return kwargs
    
    async def _call_function(self, func_name: str, args_str: str) -> Any:
        """調用函數"""
        # 內建函數
        if func_name == "print":
            return print
        
        # 用戶定義函數
        if func_name in self._functions:
            func_def = self._functions[func_name]
            args = [a.strip() for a in args_str.split(",") if a.strip()]
            
            # 簡單實現：直接執行 body
            for line in func_def["body"]:
                if line.strip().startswith("return"):
                    return await self._eval_expr(line.replace("return", "").strip())
        
        return None


async def run_ail(code: str) -> Any:
    """快速執行 AIL 代碼"""
    parser = AILParser()
    return await parser.execute(code)
