#!/usr/bin/env python3
"""
Client for agtw server
"""

import json
import socket
from typing import Optional


class Client:
    """TCP Client for connecting to agtw server"""

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8765

    def __init__(self, host: str = None, port: int = None):
        self.host = host or self.DEFAULT_HOST
        self.port = port or self.DEFAULT_PORT

    def send(self, command: str, *args, **kwargs) -> dict:
        """Send a request to the server"""
        request = {
            "command": command,
            "args": list(args),
            "kwargs": kwargs,
        }

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(30)
                sock.connect((self.host, self.port))
                sock.sendall((json.dumps(request) + "\n").encode("utf-8"))

                data = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if chunk.endswith(b"\n"):
                        break

                return json.loads(data.decode("utf-8"))
        except ConnectionRefusedError:
            return {
                "status": "error",
                "message": "無法連線到 agtw server，請先執行 agtw server",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def session_new(self, name: str = None) -> dict:
        """Create a new session"""
        return self.send("session.new", name)

    def session_list(self) -> dict:
        """List all sessions"""
        return self.send("session.list")

    def session_switch(self, identifier: str) -> dict:
        """Switch to a session"""
        return self.send("session.switch", identifier)

    def session_delete(self, identifier: str) -> dict:
        """Delete a session"""
        return self.send("session.delete", identifier)

    def agent_list(self) -> dict:
        """List agents in current session"""
        return self.send("agent.list")

    def agent_exec(self, task: str) -> dict:
        """Create and run an executor"""
        return self.send("agent.exec", task)

    def agent_eval(self, desc: str) -> dict:
        """Create an evaluator"""
        return self.send("agent.eval", desc)

    def planner_run(self, prompt: str) -> dict:
        """Run planner with a prompt"""
        return self.send("planner.run", prompt)

    def status(self) -> dict:
        """Get server status"""
        return self.send("status")
