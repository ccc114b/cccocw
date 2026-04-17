#!/usr/bin/env python3
# tests/test_usercli.py - pytest tests for UserCli class

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestUserCli:
    """Tests for UserCli class"""

    def test_usercli_creation(self):
        from main import UserCli, WORKSPACE

        cli = UserCli()
        assert cli.model is not None
        assert cli.workspace == WORKSPACE
        assert cli.session_manager is not None
        assert cli.session_manager.get_current() is not None

    def test_usercli_default_model(self):
        from main import UserCli, MODEL

        cli = UserCli()
        assert cli.model == MODEL

    def test_usercli_custom_model(self):
        from main import UserCli

        cli = UserCli(model="custom-model")
        assert cli.model == "custom-model"

    def test_usercli_initial_session(self):
        from main import UserCli

        cli = UserCli()
        session = cli.session_manager.get_current()
        assert session is not None
        assert session.name == "main"

    def test_get_help(self):
        from main import UserCli

        cli = UserCli()
        help_text = cli._get_help()
        assert "/help" in help_text
        assert "/session.new" in help_text
        assert "/session.list" in help_text
        assert "/exec" in help_text
        assert "/eval" in help_text
        assert "/memory" in help_text
        assert "/export" in help_text
        assert "/quit" in help_text

    def test_export_transcript(self):
        from main import UserCli

        cli = UserCli()
        cli.session_manager.get_current().memory = "<item>test memory</item>"
        transcript = cli._export_transcript()
        assert "Session Transcript" in transcript
        assert "test memory" in transcript
        assert "Planner History" in transcript

    def test_scan_project(self):
        from main import UserCli

        cli = UserCli()
        scan_result = cli._scan_project(".")
        assert "專案路徑" in scan_result
        assert "目錄結構" in scan_result

    def test_scan_project_nonexistent(self):
        from main import UserCli

        cli = UserCli()
        scan_result = cli._scan_project("/nonexistent/path")
        assert "專案路徑" in scan_result


class TestUserCliIntegration:
    """Integration tests for UserCli with sessions"""

    def test_create_new_session(self):
        from main import UserCli

        cli = UserCli()
        session = cli.session_manager.create_session("test-proj")
        assert session.name == "test-proj"
        assert cli.session_manager.get_current() is session

    def test_session_list(self):
        from main import UserCli

        cli = UserCli()
        cli.session_manager.create_session("proj1")
        cli.session_manager.create_session("proj2")
        listing = cli.session_manager.list_sessions()
        assert "proj1" in listing
        assert "proj2" in listing

    def test_switch_session(self):
        from main import UserCli

        cli = UserCli()
        s1 = cli.session_manager.create_session("proj1")
        cli.session_manager.create_session("proj2")
        cli.session_manager.switch_session("proj1")
        assert cli.session_manager.get_current() is s1

    def test_session_agents(self):
        from main import UserCli

        cli = UserCli()
        session = cli.session_manager.get_current()
        session.create_executor("task1")
        session.create_executor("task2")
        listing = session.list_agents()
        assert "Planner" in listing
        assert "Executor" in listing
        assert "Evaluator" in listing
