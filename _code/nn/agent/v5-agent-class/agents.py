#!/usr/bin/env python3
# agents.py - Agent classes: Planner, Executor, Evaluator, Guard

import asyncio
import re
import subprocess
import os
import aiohttp

MODEL = "minimax-m2.5:cloud"
WORKSPACE = os.path.expanduser("~/.agent0")


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
            return result.get("response", "").strip()


class Agent:
    def __init__(self, name: str, system: str = ""):
        self.name = name
        self.system = system
        self.memory: str = ""
        self.messages: list[str] = []
        self.max_turns: int = 5

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
        return await call_ollama(full_prompt, self.system)

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


class Guard(Agent):
    def __init__(self):
        super().__init__("Guard", "")
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
    def __init__(self):
        system = """你是 Planner，負責規劃任務步驟。
當用戶提出需求時，分析需求並輸出執行步驟。
用 <plan> 標籤包住規劃內容。"""
        super().__init__("Planner", system)

    async def plan(self, user_input: str) -> str:
        context = f"<user>{user_input}</user>\n\n請分析並規劃執行步驟："
        response = await self.think(context)
        plan_match = re.search(r"<plan>(.+?)</plan>", response, re.DOTALL)
        return plan_match.group(1).strip() if plan_match else response


class Executor(Agent):
    def __init__(self, guard: Guard):
        system = """你是 Executor，負責執行 shell 命令。
用 <shell> 標籤包住要執行的命令。"""
        super().__init__("Executor", system)
        self.guard = guard

    async def execute(self, command: str, cwd: str) -> str:
        """Execute a shell command through Guard"""
        output, error = await self.guard.check_and_execute(command, cwd)
        return output if output else error


class Evaluator(Agent):
    def __init__(self):
        system = """你是 Evaluator，負責評估執行結果。
檢查命令輸出是否正確完成任務。"""
        super().__init__("Evaluator", system)

    async def evaluate(self, task: str, result: str) -> str:
        context = (
            f"<task>{task}</task>\n<result>{result}</result>\n\n評估結果是否正確："
        )
        return await self.think(context)


class UserAgent(Agent):
    SYSTEM_PROMPT = """你是 Jarvis，一個有用的 AI 助理。

重要規則：
1. 當你需要執行 shell 命令時，必須用 <shell> 標籤包住命令
2. <shell> 標籤內可以是多行命令（用反斜槓 \\ 或 && 連接）
3. 當你完成所有操作後，用 <end/> 結束你的回覆

流程：
- 如果需要執行命令，輸出 <shell>...</shell>
- 執行完後我會顯示結果
- 如果還需要更多命令，繼續輸出 <shell>
- 當完成所有操作後，輸出 <end/> 表示結束"""

    def __init__(self, model: str = MODEL, workspace: str = WORKSPACE):
        super().__init__("UserAgent", self.SYSTEM_PROMPT)
        self.model = model
        self.workspace = workspace
        self.guard = Guard()
        self.executor = Executor(self.guard)
        self.max_turns = 5

    def get_context(self) -> str:
        context_parts = []
        if self.memory:
            context_parts.append(f"<memory>{self.memory}</memory>")
        if self.messages:
            context_parts.append(
                "<history>\n"
                + "\n".join(self.messages[-self.max_turns * 2 :])
                + "\n</history>"
            )
        return "\n\n".join(context_parts)

    def record(self, user_msg: str, assistant_msg: str, extra: str = None):
        super().record(user_msg, assistant_msg)
        if extra:
            self.messages.append(f"  <extra>{extra[:500]}</extra>")
        while len(self.messages) > self.max_turns * 4:
            self.messages.pop(0)

    async def chat(self, user_input: str) -> str:
        import os

        context = self.get_context()
        full_prompt = (
            f"{context}\n\n<user>{user_input}</user>"
            if context
            else f"<user>{user_input}</user>"
        )

        response = await call_ollama(full_prompt, self.SYSTEM_PROMPT, self.model)

        tool_result = None
        current_response = response

        while True:
            if "<end/>" in current_response:
                response = current_response.split("<end/>")[0].strip()
                break

            shell_matches = re.findall(
                r"<shell>(.+?)</shell>", current_response, re.DOTALL
            )
            if not shell_matches:
                response = current_response
                break

            all_outputs = []
            for cmd in shell_matches:
                cmd = cmd.strip()
                output = await self.executor.execute(cmd, os.getcwd())
                print(f"\n=== 執行命令 ===\n{cmd}\n\n結果：{output}\n")
                all_outputs.append(f"$ {cmd}\n{output}")

            tool_result = (tool_result or "") + "\n" + "\n".join(all_outputs)

            follow_up_prompt = f"""<context>{context}</context>

<user>{user_input}</user>
<assistant>{current_response}</assistant>
<output>
{chr(10).join(all_outputs)}
</output>

如果需要更多命令就輸出 <shell>。否則，輸出 <end/> 表示結束："""
            current_response = await call_ollama(
                follow_up_prompt, self.SYSTEM_PROMPT, self.model
            )

        self.record(user_input, response, tool_result)
        await self.remember(user_input, response)

        return response

    def run(self):
        import os

        os.makedirs(self.workspace, exist_ok=True)

        print(f"UserAgent - {self.model}")
        print(f"工作區：{self.workspace}")
        print("指令：/quit、/memory（顯示關鍵資訊）\n")

        while True:
            try:
                user_input = input("你：").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再見！")
                break

            if not user_input:
                continue
            if user_input.lower() in ["/quit", "/exit", "/q"]:
                print("再見！")
                break
            if user_input.lower() == "/memory":
                print(f"長期記憶：{self.memory}")
                continue

            response = asyncio.run(self.chat(user_input))
            print(f"\n🤖 {response}\n")
