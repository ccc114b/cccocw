#!/usr/bin/env python3
# main.py - Entry point for Agent system

import os
import asyncio
import re
import datetime

from agents import Agent, Guard, Planner, Executor, Evaluator, MODEL
from session import Session, SessionManager

WORKSPACE = os.path.expanduser("~/.agent0")


class UserCli:
    """CLI interface for Agent system with session management"""

    def __init__(self, model: str = MODEL, workspace: str = WORKSPACE):
        self.model = model
        self.workspace = workspace
        self.session_manager = SessionManager(model)
        self.session_manager.create_session("main")

    def _get_help(self) -> str:
        return """可用指令：
  /help           - 顯示此幫助
  /session.new <name>  - 建立新 session
  /session.list   - 列出所有 session
  /session <id/name> - 切換至指定 session
  /agents         - 列出目前 session 的所有 agent
  /exec <task>    - 建立新 Executor 執行任務
  /eval <desc>    - 建立新 Evaluator 評估當前任務
  /memory         - 顯示長期記憶
  /export         - 匯出 transcript
  /init [dir]     - 初始化專案理解
  /quit           - 結束"""

    def _export_transcript(self) -> str:
        session = self.session_manager.get_current()
        if not session:
            return "沒有目前的 session"

        lines = [
            f"# Session Transcript - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Session: {session.name} (id={session.id})",
            f"",
            f"## Memory",
            f"{session.memory}" if session.memory else "(empty)",
            f"",
            f"## Planner History",
        ]
        for msg in session.planner.messages:
            lines.append(msg)
        return "\n".join(lines)

    def _scan_project(self, cwd: str) -> str:
        key_files = [
            "README.md",
            "README.txt",
            "README",
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Makefile",
            "CMakeLists.txt",
            "AGENTS.md",
            "CLAUDE.md",
        ]

        lines = [f"專案路徑：{cwd}", "", "=== 目錄結構 ==="]

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
        session = self.session_manager.get_current()
        if not session:
            return "錯誤：沒有目前的 session"

        scan_result = self._scan_project(target_dir)

        prompt = f"""請分析以下專案結構，建立對該專案的理解：

{scan_result}

請用 <project> 標籤輸出：
1. 專案類型（網站、CLI工具、函式庫等）
2. 主要語言和框架
3. 測試方式
4. 建置/執行方式
5. 重要約定或規範"""

        try:
            response = await session.planner.think(prompt)
            project_match = re.search(r"<project>(.+?)</project>", response, re.DOTALL)
            project_info = project_match.group(1).strip() if project_match else response
            session.memory = (
                f"<project>\n{project_info}\n</project>\n<dir>{target_dir}</dir>"
            )
            return f"已分析專案：{target_dir}\n\n{project_info}"
        except Exception as e:
            return f"初始化失敗：{e}"

    async def _plan_mode(self, user_input: str) -> str:
        session = self.session_manager.get_current()
        if not session:
            return "錯誤：沒有目前的 session"

        context = session.planner.get_context()
        full_prompt = (
            f"{context}\n\n<user>{user_input}</user>"
            if context
            else f"<user>{user_input}</user>"
        )

        try:
            response = await session.planner.think(full_prompt)
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
                    output = await session.planner.execute(cmd, os.getcwd())
                    print(f"\n=== Planner 讀取 ===\n{cmd}\n\n結果：{output}\n")
                    all_outputs.append(f"$ {cmd}\n{output}")

                follow_up = f"""<context>{context}</context>

<user>{user_input}</user>
<assistant>{current_response}</assistant>
<output>
{chr(10).join(all_outputs)}
</output>

如果需要更多資訊就輸出 <shell>。如果已完成規劃，輸出 <end/>："""
                current_response = await session.planner.think(follow_up)

            session.planner.record(user_input, response)
            await session.planner.remember(user_input, response)
            return response
        except Exception as e:
            return f"Planner 錯誤：{e}"

    async def _exec_mode(self, user_input: str, task: str = "") -> str:
        session = self.session_manager.get_current()
        if not session:
            return "錯誤：沒有目前的 session"

        executor = session.create_executor(task)
        context = executor.get_context()
        full_prompt = (
            f"{context}\n\n<user>{user_input}</user>"
            if context
            else f"<user>{user_input}</user>"
        )

        try:
            response = await executor.think(full_prompt)
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
                    output = await executor.execute_shell(cmd, os.getcwd())
                    print(f"\n=== 執行命令 ===\n{cmd}\n\n結果：{output}\n")
                    all_outputs.append(f"$ {cmd}\n{output}")

                follow_up = f"""<context>{context}</context>

<user>{user_input}</user>
<assistant>{current_response}</assistant>
<output>
{chr(10).join(all_outputs)}
</output>

如果需要更多命令就輸出 <shell>。否則，輸出 <end/> 表示結束："""
                current_response = await executor.think(follow_up)

            executor.record(user_input, response)
            return response
        except Exception as e:
            return f"Executor 錯誤：{e}"

    async def _eval_mode(self, user_input: str) -> str:
        session = self.session_manager.get_current()
        if not session:
            return "錯誤：沒有目前的 session"

        if not session.current_executor:
            unevaluated = session.get_unevaluated_executors()
            if unevaluated:
                session.current_executor = unevaluated[0]
            else:
                return "錯誤：沒有可評估的 Executor。請先用 /exec 執行任務。"

        evaluator = session.create_evaluator(session.current_executor)
        context = evaluator.get_context()
        target_info = f"(評估目標: {session.current_executor.name}, 任務: {session.current_executor.assigned_task})"
        full_prompt = (
            f"{context}\n\n<user>{user_input} {target_info}</user>"
            if context
            else f"<user>{user_input} {target_info}</user>"
        )

        try:
            response = await evaluator.think(full_prompt)
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
                    output = await evaluator.execute_shell(cmd, os.getcwd())
                    print(f"\n=== 驗證 ===\n{cmd}\n\n結果：{output}\n")
                    all_outputs.append(f"$ {cmd}\n{output}")

                follow_up = f"""<context>{context}</context>

<user>{user_input}</user>
<assistant>{current_response}</assistant>
<output>
{chr(10).join(all_outputs)}
</output>

如果需要更多驗證就輸出 <shell>。否則，輸出 <end/> 表示結束："""
                current_response = await evaluator.think(follow_up)

            evaluator.record(user_input, response)
            return response
        except Exception as e:
            return f"Evaluator 錯誤：{e}"

    def run(self):
        os.makedirs(self.workspace, exist_ok=True)

        print(f"UserCli - {self.model}")
        print(f"工作區：{self.workspace}")
        session = self.session_manager.get_current()
        print(f"Session: {session.name} (id={session.id})")
        print("輸入 /help 查看所有指令\n")

        while True:
            try:
                user_input = input("你：").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再見！")
                break

            if not user_input:
                continue

            cmd_lower = user_input.lower()

            if cmd_lower in ["/quit", "/exit", "/q"]:
                print("再見！")
                self.session_manager.shutdown_all()
                break

            if cmd_lower == "/help":
                print(f"\n{self._get_help()}\n")
                continue

            if cmd_lower == "/session.list":
                print(f"\n{self.session_manager.list_sessions()}\n")
                continue

            if cmd_lower.startswith("/session.new"):
                parts = user_input.split(maxsplit=1)
                name = parts[1].strip() if len(parts) > 1 else None
                session = self.session_manager.create_session(name)
                print(f"\n已建立新 session: {session.name} (id={session.id})\n")
                continue

            if cmd_lower.startswith("/session ") or cmd_lower.startswith("/session."):
                identifier = user_input.split(maxsplit=1)[1].strip()
                session = self.session_manager.switch_session(identifier)
                if session:
                    print(f"\n已切換至 session: {session.name} (id={session.id})\n")
                else:
                    print(f"\n找不到 session: {identifier}\n")
                continue

            if cmd_lower == "/agents":
                session = self.session_manager.get_current()
                if session:
                    print(f"\n{session.list_agents()}\n")
                continue

            if cmd_lower == "/memory":
                session = self.session_manager.get_current()
                if session:
                    print(
                        f"\n長期記憶：{session.memory if session.memory else '(empty)'}\n"
                    )
                continue

            if cmd_lower == "/export":
                print(f"\n{self._export_transcript()}\n")
                continue

            if cmd_lower.startswith("/init"):
                parts = user_input.split(maxsplit=1)
                target_dir = parts[1].strip() if len(parts) > 1 else os.getcwd()
                try:
                    result = asyncio.run(self._init_project(target_dir))
                    print(f"\n{result}\n")
                except Exception as e:
                    print(f"\n⚠️  錯誤：{e}\n")
                continue

            if cmd_lower.startswith("/exec "):
                task = user_input[5:].strip()
                try:
                    result = asyncio.run(self._exec_mode(task, task))
                    print(f"\n🤖 [EXEC] {result}\n")
                except Exception as e:
                    print(f"\n⚠️  錯誤：{e}\n")
                continue

            if cmd_lower.startswith("/eval "):
                desc = user_input[5:].strip()
                try:
                    result = asyncio.run(self._eval_mode(desc))
                    print(f"\n🤖 [EVAL] {result}\n")
                except Exception as e:
                    print(f"\n⚠️  錯誤：{e}\n")
                continue

            if cmd_lower in ["/exec", "/eval", "/plan"]:
                print(f"\n請提供描述：{cmd_lower} <描述>\n")
                continue

            try:
                result = asyncio.run(self._plan_mode(user_input))
                print(f"\n🤖 [PLAN] {result}\n")
            except Exception as e:
                print(f"\n⚠️  錯誤：{e}\n")


def main():
    cli = UserCli()
    cli.run()


if __name__ == "__main__":
    main()
