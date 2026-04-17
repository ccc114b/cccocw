#!/usr/bin/env python3
# agents.py - Agent classes: Planner, Executor, Evaluator, Guard

import asyncio
import re
import subprocess
import os
import aiohttp
import threading
import queue
from typing import Optional

MODEL = "minimax-m2.5:cloud"


def check_outside_access(cmd: str, cwd: str) -> tuple[bool, str]:
    """Check if command accesses outside current directory"""

    def extract_paths(c):
        paths = []
        patterns = [
            (r"(?:^|\s)(?:cat|ls|cd|rm|cp|mv|chmod|chown|find|grep)\s+(/[^\s]+)", 1),
            (r"(?:^|\s)\.\./[^\s]*", 0),
            (r"(?:^|\s)\.\.(?:\s|$)", 0),
        ]
        for pattern, group in patterns:
            for match in re.finditer(pattern, c, re.MULTILINE):
                path = match.group(group).strip() if group > 0 else ".."
                if path:
                    paths.append(path)
        return paths

    paths = extract_paths(cmd)
    cwd_abs = os.path.abspath(cwd)

    for path in paths:
        if path.startswith("/"):
            abs_path = path
        else:
            abs_path = os.path.abspath(os.path.join(cwd, path))

        if path == ".." or path.startswith("../"):
            return True, abs_path

        if not abs_path.startswith(cwd_abs):
            return True, abs_path

    return False, ""


async def call_ollama(prompt: str, system: str = "", model: str = MODEL) -> str:
    """Call Ollama API"""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    payload = {"model": model, "prompt": full_prompt, "stream": False}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=120),
        ) as resp:
            result = await resp.json()
            if "error" in result:
                error_msg = result.get("error", "")
                if "usage limit" in error_msg.lower():
                    raise Exception(
                        f"Ollama 使用限制已達上限：{error_msg}\n請升級或等待重置。"
                    )
                raise Exception(f"Ollama 錯誤：{error_msg}")
            return result.get("response", "").strip()


class Agent:
    def __init__(self, name: str, system: str = ""):
        self.name = name
        self.system = system
        self.memory: str = ""
        self.messages: list[str] = []
        self.max_turns: int = 5
        self.thread: Optional[threading.Thread] = None
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()

    def read(self, message: str):
        self.messages.append(message)

    def write(self, content: str) -> str:
        self.messages.append(content)
        return content

    def get_context(self) -> str:
        context_parts = []
        if self.memory:
            context_parts.append(f"<memory>{self.memory}</memory>")
        if self.messages:
            context_parts.append(
                "<history>\n" + "\n".join(self.messages) + "\n</history>"
            )
        return "\n\n".join(context_parts)

    def record(self, user_msg: str, assistant_msg: str):
        self.messages.append(f"  <user>{user_msg}</user>")
        self.messages.append(f"  <assistant>{assistant_msg}</assistant>")
        while len(self.messages) > self.max_turns * 4:
            self.messages.pop(0)

    async def think(self, context: str) -> str:
        full_context = self.get_context()
        full_prompt = f"{full_context}\n\n{context}" if full_context else context
        try:
            return await call_ollama(full_prompt, self.system)
        except Exception as e:
            raise Exception(f"[{self.name}] 思考失敗：{e}")

    async def remember(self, user_msg: str, assistant_msg: str):
        prompt = f"""根據這段對話，有沒有需要長期記憶的關鍵資訊？
如果有，用以下格式輸出（最多 2 項）。如果沒有，輸出 <memory></memory>。

<memory>
  <item>要記憶的資訊 1</item>
  <item>要記憶的資訊 2</item>
</memory>

對話：
<user>{user_msg}</user>
<assistant>{assistant_msg}</assistant>"""
        try:
            result = await call_ollama(prompt, "")
            matches = re.findall(r"<item>(.*?)</item>", result, re.DOTALL)
            for item in matches:
                item = item.strip()
                if item and item not in self.memory:
                    self.memory += f"\n  <item>{item}</item>"
        except:
            pass

    def run_thread(self):
        """Run agent in its own thread with event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            while True:
                try:
                    task = self.task_queue.get(timeout=1)
                    if task is None:
                        break
                    coroutine, future = task
                    result = loop.run_until_complete(coroutine)
                    future.put_nowait(result)
                except queue.Empty:
                    continue
                except Exception as e:
                    if future:
                        future.put_nowait(Exception(f"[{self.name}] 執行失敗：{e}"))
        finally:
            loop.close()

    def submit(self, coroutine) -> asyncio.Future:
        """Submit a coroutine to be executed in this agent's thread"""
        future: asyncio.Future = asyncio.Future()
        self.task_queue.put((coroutine, future))
        return future

    def start(self):
        """Start the agent thread"""
        self.thread = threading.Thread(target=self.run_thread, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the agent thread"""
        self.task_queue.put(None)
        if self.thread:
            self.thread.join(timeout=2)


class Guard:
    def __init__(self):
        self.allowed_paths: set[str] = set()

    async def review_command(self, cmd: str) -> tuple[bool, str]:
        """Use Ollama to review if command is safe"""
        review_prompt = f"""你是安全審查者。請判斷以下 shell 命令是否安全可以執行。

安全原則：
1. 允許讀取檔案、瀏覽目錄、搜尋程式碼
2. 允許執行無害的開發工具（git, ls, cat, grep, find, python, node 等）
3. 禁止會刪除資料的命令（rm -rf, dd, mkfs 等）
4. 禁止會修改系統的命令（sudo, chmod 777, 修改系統設定等）
5. 禁止網路相關的危险操作（curl/wget 下載並執行腳本等）
6. 禁止任何可能造成資料洩露或系統傷害的命令

要審查的命令：
{cmd}

請嚴格按照以下格式輸出：
- 如果安全，輸出：SAFE
- 如果不安全，輸出：UNSAFE - 原因

不要輸出其他內容。"""

        try:
            response = await call_ollama(review_prompt, "", MODEL)

            if response.startswith("SAFE"):
                return True, ""
            else:
                reason = response.replace("UNSAFE", "").strip(" -")
                return False, reason
        except Exception as e:
            return False, f"審查失敗: {e}"

    def ask_outside_access(self, path: str) -> bool:
        """Ask user for permission to access outside directory"""
        print(f"\n⚠️  命令嘗試存取本資料夾以外的檔案: {path}")
        print("   是否允許？（y/N）：", end=" ")
        try:
            response = input().strip().lower()
            return response in ["y", "yes"]
        except:
            return False

    async def check_and_execute(self, cmd: str, cwd: str) -> tuple[str, str]:
        """Check command safety and outside access, then execute if allowed"""
        is_safe, reason = await self.review_command(cmd)

        if not is_safe:
            return "", f"阻止：{reason}"

        needs_access, path = check_outside_access(cmd, cwd)
        if needs_access:
            if path in self.allowed_paths:
                pass
            else:
                if not self.ask_outside_access(path):
                    return "", f"拒絕：{path}"
                self.allowed_paths.add(path)

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=cwd
            )
            output = result.stdout + result.stderr
            return output if output else "（無輸出）", ""
        except Exception as e:
            return "", f"錯誤：{e}"


class Planner(Agent):
    def __init__(self, guard: Guard, name: str = "Planner"):
        system = """你是 Planner，負責規劃任務步驟並獲取資訊。

重要規則：
1. 先用 <shell> 標籤包住 shell 命令來了解現有專案結構（如 ls, cat, find 等）
2. 分析需求後，用 <plan> 標籤包住規劃內容
3. 完成所有操作後，用 <end/> 結束你的回覆

流程：
- 如果需要了解專案，用 <shell>...</shell> 讀取資訊
- 讀取完後我會顯示結果
- 如果還需要更多資訊，繼續輸出 <shell>
- 當完成分析並輸出規劃後，輸出 <end/> 表示結束"""
        super().__init__(name, system)
        self.guard = guard

    async def execute(self, command: str, cwd: str) -> str:
        """Execute a shell command through Guard for reading/info gathering"""
        output, error = await self.guard.check_and_execute(command, cwd)
        return output if output else error


class Executor(Agent):
    def __init__(self, guard: Guard, name: str = "Executor"):
        system = """你是 Executor，負責執行 shell 命令。
用 <shell> 標籤包住要執行的命令。"""
        super().__init__(name, system)
        self.guard = guard
        self.assigned_task: str = ""

    async def execute_shell(self, command: str, cwd: str) -> str:
        """Execute a shell command through Guard"""
        output, error = await self.guard.check_and_execute(command, cwd)
        return output if output else error


class Evaluator(Agent):
    def __init__(self, guard: Guard, name: str = "Evaluator"):
        system = """你是 Evaluator，負責評估執行結果並驗證。
檢查命令輸出是否正確完成任務。如需驗證，可執行 shell 命令。
用 <shell> 標籤包住要執行的驗證命令。"""
        super().__init__(name, system)
        self.guard = guard
        self.target_executor: Optional[Executor] = None

    async def execute_shell(self, command: str, cwd: str) -> str:
        """Execute a shell command through Guard for verification"""
        output, error = await self.guard.check_and_execute(command, cwd)
        return output if output else error
