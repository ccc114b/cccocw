#!/usr/bin/env python3
"""
CLI for agtw - Agent Team Work

Git-style commands:
  agtw server              - Start the agtw server
  agtw session new [name]  - Create a new session
  agtw session list        - List all sessions
  agtw session switch <id> - Switch to a session
  agtw session delete <id> - Delete a session
  agtw agent list          - List agents in current session
  agtw agent exec <task>   - Create and run an executor
  agtw agent eval <desc>   - Create an evaluator
  agtw planner <prompt>    - Run planner with prompt
  agtw status              - Show server status
"""

import argparse
import sys

from .client import Client
from .server import Server


def cmd_server(args):
    """Start the server"""
    server = Server(host=args.host, port=args.port, model=args.model)
    server.start()


def cmd_session_new(args):
    """Create a new session"""
    client = Client(host=args.host, port=args.port)
    result = client.session_new(args.identifier)
    if result["status"] == "ok":
        print(
            f"已建立 session: {result['session']['name']} (id={result['session']['id']})"
        )
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_session_list(args):
    """List all sessions"""
    client = Client(host=args.host, port=args.port)
    result = client.session_list()
    if result["status"] == "ok":
        print("所有 Session:")
        print(f"{'ID':<12} {'Name':<20}")
        print("-" * 35)
        for s in result["sessions"]:
            marker = " ← 目前" if s["id"] == result.get("current") else ""
            print(f"{s['id']:<12} {s['name']:<20}{marker}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_session_switch(args):
    """Switch to a session"""
    client = Client(host=args.host, port=args.port)
    result = client.session_switch(args.identifier)
    if result["status"] == "ok":
        print(
            f"已切換至 session: {result['session']['name']} (id={result['session']['id']})"
        )
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_session_delete(args):
    """Delete a session"""
    client = Client(host=args.host, port=args.port)
    result = client.session_delete(args.identifier)
    if result["status"] == "ok":
        print(f"已刪除 session: {args.identifier}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_agent_list(args):
    """List agents"""
    client = Client(host=args.host, port=args.port)
    result = client.agent_list()
    if result["status"] == "ok":
        print(result["agents"])
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_agent_exec(args):
    """Create and run executor"""
    client = Client(host=args.host, port=args.port)
    result = client.agent_exec(args.content)
    if result["status"] == "ok":
        print(f"已啟動 Executor: {result['executor']['name']}")
        print(f"任務：{result['executor']['task']}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_agent_eval(args):
    """Create evaluator"""
    client = Client(host=args.host, port=args.port)
    result = client.agent_eval(args.content)
    if result["status"] == "ok":
        print(f"已啟動 Evaluator: {result['evaluator']['name']}")
        print(f"描述：{result['evaluator']['desc']}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_planner(args):
    """Run planner"""
    client = Client(host=args.host, port=args.port)
    result = client.planner_run(args.prompt)
    if result["status"] == "ok":
        print(result["response"])
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args):
    """Show status"""
    client = Client(host=args.host, port=args.port)
    result = client.status()
    if result["status"] == "ok":
        print(f"模型：{result.get('model', 'N/A')}")
        if result.get("current_session"):
            print(
                f"目前 Session：{result['current_session']['name']} (id={result['current_session']['id']})"
            )
        else:
            print("目前 Session：無")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="agtw - Agent Team Work",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  agtw server                      # 啟動伺服器
  agtw session new myproject        # 建立新 session
  agtw session list                 # 列出所有 session
  agtw session switch abc123        # 切換至指定 session
  agtw agent list                  # 列出目前 session 的 agents
  agtw agent exec 寫一個 hello.py  # 建立並執行 executor
  agtw planner 分析這個專案         # 執行 planner
  agtw status                      # 顯示狀態
        """,
    )

    parser.add_argument(
        "--host", default="localhost", help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Server port (default: 8765)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    p_server = subparsers.add_parser("server", help="Start the agtw server")
    p_server.add_argument("--host", help="Server host")
    p_server.add_argument("--port", type=int, help="Server port")
    p_server.add_argument("--model", default="minimax-m2.5:cloud", help="Ollama model")

    p_session_new = subparsers.add_parser("session", help="Session commands")
    p_session_new.add_argument(
        "action", choices=["new", "list", "switch", "delete"], help="Action"
    )
    p_session_new.add_argument("identifier", nargs="?", help="Session name or ID")

    p_agent = subparsers.add_parser("agent", help="Agent commands")
    p_agent.add_argument("action", choices=["list", "exec", "eval"], help="Action")
    p_agent.add_argument("content", nargs="?", help="Task or description")

    p_planner = subparsers.add_parser("planner", help="Run planner")
    p_planner.add_argument("prompt", help="Prompt for planner")

    p_status = subparsers.add_parser("status", help="Show server status")

    args = parser.parse_args()

    if args.command == "server":
        cmd_server(args)
    elif args.command == "session":
        if args.action == "new":
            cmd_session_new(args)
        elif args.action == "list":
            cmd_session_list(args)
        elif args.action == "switch":
            if not args.identifier:
                print("錯誤：請提供 session ID 或名稱", file=sys.stderr)
                sys.exit(1)
            cmd_session_switch(args)
        elif args.action == "delete":
            if not args.identifier:
                print("錯誤：請提供 session ID", file=sys.stderr)
                sys.exit(1)
            cmd_session_delete(args)
    elif args.command == "agent":
        if args.action == "list":
            cmd_agent_list(args)
        elif args.action == "exec":
            if not args.content:
                print("錯誤：請提供任務描述", file=sys.stderr)
                sys.exit(1)
            cmd_agent_exec(args)
        elif args.action == "eval":
            if not args.content:
                print("錯誤：請提供描述", file=sys.stderr)
                sys.exit(1)
            cmd_agent_eval(args)
    elif args.command == "planner":
        cmd_planner(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
