#!/usr/bin/env python3
"""
Server daemon for agtw system
Handles requests from CLI clients via JSON over TCP
"""

import asyncio
import json
import os
import socket
import threading
from typing import Optional

from .agents import call_ollama
from .session import SessionManager


class Server:
    """TCP Server for agtw agent coordination"""

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8765

    def __init__(
        self, host: str = None, port: int = None, model: str = "minimax-m2.5:cloud"
    ):
        self.host = host or self.DEFAULT_HOST
        self.port = port or self.DEFAULT_PORT
        self.model = model
        self.session_manager = SessionManager(model)
        self.session_manager.create_session("main")
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        """Start the server in a blocking manner"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True

        print(f"agtw server 啟動中...")
        print(f"  主機：{self.host}")
        print(f"  連接埠：{self.port}")
        print(f"  模型：{self.model}")
        print(f"  工作區：{os.path.expanduser('~/.agtw')}")
        print()

        try:
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    thread = threading.Thread(
                        target=self._handle_client, args=(client_socket, address)
                    )
                    thread.daemon = True
                    thread.start()
                except Exception as e:
                    if self.running:
                        print(f"接受連線錯誤：{e}")
        except KeyboardInterrupt:
            print("\n正在關閉伺服器...")
        finally:
            self.stop()

    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.session_manager.shutdown_all()
        print("伺服器已關閉")

    def _handle_client(self, client_socket: socket.socket, address):
        """Handle a client connection"""
        try:
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if chunk.endswith(b"\n"):
                    break

            if not data:
                return

            request = json.loads(data.decode("utf-8"))
            response = self._process_request(request)
            client_socket.sendall((json.dumps(response) + "\n").encode("utf-8"))
        except Exception as e:
            error_response = {"status": "error", "message": str(e)}
            try:
                client_socket.sendall(
                    (json.dumps(error_response) + "\n").encode("utf-8")
                )
            except:
                pass
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _process_request(self, request: dict) -> dict:
        """Process a request and return response"""
        cmd = request.get("command", "")
        args = request.get("args", [])
        kwargs = request.get("kwargs", {})

        try:
            with self._lock:
                if cmd == "session.new":
                    return self._cmd_session_new(args, kwargs)
                elif cmd == "session.list":
                    return self._cmd_session_list()
                elif cmd == "session.switch":
                    return self._cmd_session_switch(args)
                elif cmd == "session.delete":
                    return self._cmd_session_delete(args)
                elif cmd == "agent.list":
                    return self._cmd_agent_list()
                elif cmd == "agent.exec":
                    return self._cmd_agent_exec(args)
                elif cmd == "agent.eval":
                    return self._cmd_agent_eval(args)
                elif cmd == "planner.run":
                    return self._cmd_planner_run(args)
                elif cmd == "status":
                    return self._cmd_status()
                else:
                    return {"status": "error", "message": f"未知命令：{cmd}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _cmd_session_new(self, args, kwargs) -> dict:
        name = args[0] if args else kwargs.get("name")
        session = self.session_manager.create_session(name)
        return {
            "status": "ok",
            "session": {"id": session.id, "name": session.name},
        }

    def _cmd_session_list(self) -> dict:
        return {
            "status": "ok",
            "sessions": [
                {"id": s.id, "name": s.name}
                for name, s in self.session_manager.sessions.items()
                if name != s.id
            ],
            "current": self.session_manager.current_session.id
            if self.session_manager.current_session
            else None,
        }

    def _cmd_session_switch(self, args) -> dict:
        identifier = args[0] if args else ""
        session = self.session_manager.switch_session(identifier)
        if session:
            return {"status": "ok", "session": {"id": session.id, "name": session.name}}
        return {"status": "error", "message": f"找不到 session：{identifier}"}

    def _cmd_session_delete(self, args) -> dict:
        identifier = args[0] if args else ""
        if self.session_manager.delete_session(identifier):
            return {"status": "ok"}
        return {"status": "error", "message": f"找不到 session：{identifier}"}

    def _cmd_agent_list(self) -> dict:
        session = self.session_manager.get_current()
        if not session:
            return {"status": "error", "message": "沒有目前的 session"}
        return {
            "status": "ok",
            "agents": session.list_agents(),
        }

    def _cmd_agent_exec(self, args) -> dict:
        task = args[0] if args else ""
        session = self.session_manager.get_current()
        if not session:
            return {"status": "error", "message": "沒有目前的 session"}
        executor = session.create_executor(task)
        return {
            "status": "ok",
            "executor": {"name": executor.name, "task": task},
        }

    def _cmd_agent_eval(self, args) -> dict:
        desc = args[0] if args else ""
        session = self.session_manager.get_current()
        if not session:
            return {"status": "error", "message": "沒有目前的 session"}
        evaluator = session.create_evaluator()
        return {
            "status": "ok",
            "evaluator": {"name": evaluator.name, "desc": desc},
        }

    def _cmd_planner_run(self, args) -> dict:
        prompt = args[0] if args else ""
        session = self.session_manager.get_current()
        if not session:
            return {"status": "error", "message": "沒有目前的 session"}

        try:
            response = asyncio.run(session.planner.think(prompt))
            return {"status": "ok", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _cmd_status(self) -> dict:
        session = self.session_manager.get_current()
        return {
            "status": "ok",
            "model": self.model,
            "current_session": {
                "id": session.id,
                "name": session.name,
            }
            if session
            else None,
        }


def start_server(host: str = None, port: int = None, model: str = "minimax-m2.5:cloud"):
    """Start the agtw server"""
    server = Server(host, port, model)
    server.start()
