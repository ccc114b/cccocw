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
    def __init__(self, guard: Guard):
        system = """你是 Planner，負責規劃任務步驟並獲取資訊。
當用戶提出需求時，分析需求並規劃執行步驟。
你可以用 <shell> 標籤包住 shell 命令來讀取檔案、目錄等資訊，但不要寫程式。
用 <plan> 標籤包住規劃內容。"""
        super().__init__("Planner", system)
        self.guard = guard

    async def execute(self, command: str, cwd: str) -> str:
        """Execute a shell command through Guard for reading/info gathering"""
        output, error = await self.guard.check_and_execute(command, cwd)
        return output if output else error

    async def plan(self, user_input: str) -> str:
        context = f"<user>{user_input}</user>\n\n請分析並規劃執行步驟："
        return await self.think(context)


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
    def __init__(self, guard: Guard):
        system = """你是 Evaluator，負責評估執行結果並驗證。
檢查命令輸出是否正確完成任務。如需驗證，可執行 shell 命令。
用 <shell> 標籤包住要執行的驗證命令。"""
        super().__init__("Evaluator", system)
        self.guard = guard

    async def execute(self, command: str, cwd: str) -> str:
        """Execute a shell command through Guard for verification"""
        output, error = await self.guard.check_and_execute(command, cwd)
        return output if output else error

    async def evaluate(self, task: str, result: str) -> str:
        context = (
            f"<task>{task}</task>\n<result>{result}</result>\n\n評估結果是否正確："
        )
        return await self.think(context)


class UserAgent(Agent):
    MODE_PLAN = "plan"
    MODE_EXEC = "exec"
    MODE_EVAL = "eval"

    def __init__(self, model: str = MODEL, workspace: str = WORKSPACE):
        super().__init__("UserAgent", "")
        self.model = model
        self.workspace = workspace
        self.guard = Guard()
        self.planner = Planner(self.guard)
        self.executor = Executor(self.guard)
        self.evaluator = Evaluator(self.guard)
        self.mode = self.MODE_PLAN
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

    async def handle_shell_commands(
        self, response: str, cwd: str, agent: Agent
    ) -> tuple[str, str]:
        """Execute shell commands in response and return tool_result"""
        shell_matches = re.findall(r"<shell>(.+?)</shell>", response, re.DOTALL)
        if not shell_matches:
            return "", response

        all_outputs = []
        for cmd in shell_matches:
            cmd = cmd.strip()
            output = await agent.execute(cmd, cwd)
            print(f"\n=== 執行命令 ===\n{cmd}\n\n結果：{output}\n")
            all_outputs.append(f"$ {cmd}\n{output}")

        tool_result = "\n".join(all_outputs)
        remaining = re.sub(r"<shell>.+?</shell>", "", response, flags=re.DOTALL).strip()
        return tool_result, remaining

    async def chat(self, user_input: str) -> str:
        import os

        cwd = os.getcwd()
        context = self.get_context()

        if self.mode == self.MODE_PLAN:
            return await self._plan_mode(user_input, context, cwd)
        elif self.mode == self.MODE_EXEC:
            return await self._exec_mode(user_input, context, cwd)
        elif self.mode == self.MODE_EVAL:
            return await self._eval_mode(user_input, context, cwd)
        return ""

    async def _plan_mode(self, user_input: str, context: str, cwd: str) -> str:
        full_prompt = (
            f"{context}\n\n<user>{user_input}</user>"
            if context
            else f"<user>{user_input}</user>"
        )
        response = await self.planner.think(full_prompt)

        tool_result, response = await self.handle_shell_commands(
            response, cwd, self.planner
        )

        self.record(user_input, response, tool_result)
        await self.remember(user_input, response)
        return response

    async def _exec_mode(self, user_input: str, context: str, cwd: str) -> str:
        full_prompt = (
            f"{context}\n\n<user>{user_input}</user>"
            if context
            else f"<user>{user_input}</user>"
        )
        response = await self.executor.think(full_prompt)

        tool_result, response = await self.handle_shell_commands(
            response, cwd, self.executor
        )

        self.record(user_input, response, tool_result)
        await self.remember(user_input, response)
        return response

    async def _eval_mode(self, user_input: str, context: str, cwd: str) -> str:
        full_prompt = (
            f"{context}\n\n<user>{user_input}</user>"
            if context
            else f"<user>{user_input}</user>"
        )
        response = await self.evaluator.think(full_prompt)

        tool_result, response = await self.handle_shell_commands(
            response, cwd, self.evaluator
        )

        self.record(user_input, response, tool_result)
        await self.remember(user_input, response)
        return response

    def _get_help(self) -> str:
        return """可用指令：
  /help     - 顯示此幫助
  /plan     - 切換至 Plan Mode（規劃任務）
  /exec     - 切換至 Exec Mode（執行命令）
  /eval     - 切換至 Eval Mode（驗證結果）
  /memory   - 顯示長期記憶
  /new      - 新建 session（清除對話歷史）
  /export   - 匯出 session transcript
  /init     - 初始化 AGENTS.md
  /quit     - 結束"""

    def _export_transcript(self) -> str:
        import datetime

        lines = [
            f"# Session Transcript - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"## Memory",
            f"{self.memory}" if self.memory else "(empty)",
            f"",
            f"## Conversation",
        ]
        for msg in self.messages:
            lines.append(msg)
        return "\n".join(lines)

    def _scan_project(self, cwd: str) -> str:
        """Scan project directory and return file listing"""
        import os

        key_files = [
            "README.md",
            "README.txt",
            "README",
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Cargo.toml",
            "Makefile",
            "CMakeLists.txt",
            "AGENTS.md",
            "CLAUDE.md",
            "test.sh",
            "tests/",
            "test_*.py",
            "*_test.py",
            "src/",
            "lib/",
            "app/",
        ]

        lines = [f"專案路徑：{cwd}", ""]
        lines.append("=== 目錄結構 ===")

        try:
            for root, dirs, files in os.walk(cwd):
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["__pycache__", "node_modules", "target", "bin", "obj"]
                ]
                level = root.replace(cwd, "").count(os.sep)
                indent = "  " * level
                lines.append(f"{indent}{os.path.basename(root)}/")
                sub_indent = "  " * (level + 1)
                for f in sorted(files)[:20]:
                    lines.append(f"{sub_indent}{f}")
                if len(files) > 20:
                    lines.append(f"{sub_indent}... ({len(files) - 20} more files)")
        except Exception as e:
            lines.append(f"掃描錯誤：{e}")

        lines.append("")
        lines.append("=== 關鍵檔案內容 ===")

        for key_file in [
            "README.md",
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Makefile",
        ]:
            fpath = os.path.join(cwd, key_file)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()[:2000]
                        lines.append(f"\n--- {key_file} ---")
                        lines.append(content)
                except:
                    pass

        return "\n".join(lines)

    async def _init_project(self, target_dir: str) -> str:
        """Use Planner to understand the project"""
        scan_result = self._scan_project(target_dir)

        prompt = f"""請分析以下專案結構，建立對該專案的理解：

{scan_result}

請用 <project> 標籤輸出：
1. 專案類型（網站、CLI工具、函式庫等）
2. 主要語言和框架
3. 測試方式
4. 建置/執行方式
5. 重要約定或規範"""

        response = await self.planner.think(prompt)
        project_match = re.search(r"<project>(.+?)</project>", response, re.DOTALL)
        project_info = project_match.group(1).strip() if project_match else response

        self.memory = f"<project>\n{project_info}\n</project>\n<dir>{target_dir}</dir>"

        return f"已分析專案：{target_dir}\n\n{project_info}"

    def _init_agents_md(self, cwd: str) -> str:
        """Initialize project understanding (async, returns message)"""
        return f"請稍候，正在掃描專案...\n(使用 /init 觸發 Planner 分析)"

    def _new_session(self):
        self.messages = []
        self.memory = ""
        self.mode = self.MODE_PLAN
        return "已新建 session"

    def run(self):
        import os

        os.makedirs(self.workspace, exist_ok=True)
        cwd = os.getcwd()

        print(f"UserAgent - {self.model}")
        print(f"工作區：{self.workspace}")
        print("模式：Plan Mode")
        print("輸入 /help 查看所有指令\n")

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
            if user_input.lower() == "/help":
                print(f"\n{self._get_help()}\n")
                continue
            if user_input.lower() == "/memory":
                print(f"\n長期記憶：{self.memory if self.memory else '(empty)'}\n")
                continue
            if user_input.lower() == "/export":
                transcript = self._export_transcript()
                print(f"\n{transcript}\n")
                continue
            if user_input.lower().startswith("/init"):
                parts = user_input.split(maxsplit=1)
                target_dir = parts[1].strip() if len(parts) > 1 else cwd
                result = asyncio.run(self._init_project(target_dir))
                print(f"\n{result}\n")
                continue
            if user_input.lower() == "/new":
                print(f"\n{self._new_session()}\n")
                continue
            if user_input.lower() == "/exec":
                self.mode = self.MODE_EXEC
                print(">>> 切換至 Exec Mode\n")
                continue
            if user_input.lower() == "/eval":
                self.mode = self.MODE_EVAL
                print(">>> 切換至 Eval Mode\n")
                continue
            if user_input.lower() == "/plan":
                self.mode = self.MODE_PLAN
                print(">>> 切換至 Plan Mode\n")
                continue

            response = asyncio.run(self.chat(user_input))
            print(f"\n🤖 [{self.mode.upper()}] {response}\n")
