#!/usr/bin/env python3
"""
Tests for client and server TCP communication
"""

import json
import socket
import threading
import time
import pytest
from agtw.server import Server
from agtw.client import Client


@pytest.fixture
def server_instance():
    """Create a test server instance"""
    server = Server(host="localhost", port=19876, model="test-model")
    server.session_manager.create_session("test")
    return server


class TestClientServerConnection:
    def test_client_connection_refused(self):
        client = Client(host="localhost", port=19999)
        result = client.send("status")
        assert result["status"] == "error"
        assert "無法連線" in result["message"]

    def test_client_send_status(self, server_instance):
        server_instance.server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        server_instance.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        server_instance.server_socket.bind(("localhost", 19876))
        server_instance.server_socket.listen(1)
        server_instance.running = True

        def run_server():
            try:
                client_socket, _ = server_instance.server_socket.accept()
                data = b""
                while True:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if chunk.endswith(b"\n"):
                        break

                request = json.loads(data.decode("utf-8"))
                response = server_instance._process_request(request)
                client_socket.sendall((json.dumps(response) + "\n").encode("utf-8"))
                client_socket.close()
            except:
                pass

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        time.sleep(0.1)

        client = Client(host="localhost", port=19876)
        result = client.status()

        server_instance.running = False
        server_instance.server_socket.close()

        assert result["status"] == "ok"
        assert result["model"] == "test-model"


class TestServerCommands:
    def test_process_status_command(self, server_instance):
        request = {"command": "status", "args": [], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"
        assert response["model"] == "test-model"
        assert response["current_session"]["name"] == "test"

    def test_process_session_new(self, server_instance):
        request = {"command": "session.new", "args": ["my_session"], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"
        assert response["session"]["name"] == "my_session"
        assert "id" in response["session"]

    def test_process_session_new_auto_name(self, server_instance):
        request = {"command": "session.new", "args": [], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"
        assert response["session"]["name"].startswith("session")

    def test_process_session_list(self, server_instance):
        server_instance._process_request(
            {"command": "session.new", "args": ["s2"], "kwargs": {}}
        )

        request = {"command": "session.list", "args": [], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"
        assert len(response["sessions"]) >= 2

    def test_process_session_switch(self, server_instance):
        new_session = server_instance._process_request(
            {"command": "session.new", "args": ["to_switch"], "kwargs": {}}
        )
        session_id = new_session["session"]["id"]

        request = {"command": "session.switch", "args": [session_id], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"
        assert response["session"]["name"] == "to_switch"

    def test_process_session_switch_invalid(self, server_instance):
        request = {"command": "session.switch", "args": ["invalid_id"], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "error"
        assert "找不到" in response["message"]

    def test_process_session_delete(self, server_instance):
        new_session = server_instance._process_request(
            {"command": "session.new", "args": ["to_delete"], "kwargs": {}}
        )
        session_id = new_session["session"]["id"]

        request = {"command": "session.delete", "args": [session_id], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"

    def test_process_session_delete_invalid(self, server_instance):
        request = {"command": "session.delete", "args": ["invalid_id"], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "error"

    def test_process_agent_list(self, server_instance):
        request = {"command": "agent.list", "args": [], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"
        assert "Planner" in response["agents"]

    def test_process_agent_exec(self, server_instance):
        request = {"command": "agent.exec", "args": ["Write tests"], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"
        assert "Executor" in response["executor"]["name"]
        assert response["executor"]["task"] == "Write tests"

    def test_process_agent_eval(self, server_instance):
        request = {"command": "agent.eval", "args": ["Check output"], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "ok"
        assert "Evaluator" in response["evaluator"]["name"]

    def test_process_unknown_command(self, server_instance):
        request = {"command": "unknown.cmd", "args": [], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "error"
        assert "未知命令" in response["message"]

    def test_process_planner_run_no_session(self, server_instance):
        server_instance.session_manager.current_session = None

        request = {"command": "planner.run", "args": ["test prompt"], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "error"
        assert "沒有" in response["message"]

    def test_process_agent_list_no_session(self, server_instance):
        server_instance.session_manager.current_session = None

        request = {"command": "agent.list", "args": [], "kwargs": {}}
        response = server_instance._process_request(request)

        assert response["status"] == "error"


class TestClient:
    def test_client_default_values(self):
        client = Client()
        assert client.host == "localhost"
        assert client.port == 8765

    def test_client_custom_values(self):
        client = Client(host="127.0.0.1", port=9999)
        assert client.host == "127.0.0.1"
        assert client.port == 9999
