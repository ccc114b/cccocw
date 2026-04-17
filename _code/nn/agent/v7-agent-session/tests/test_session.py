#!/usr/bin/env python3
# tests/test_session.py - pytest tests for Session classes

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSession:
    """Tests for Session class"""

    def test_session_creation(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test-session", guard, "test-model")
        assert session.name == "test-session"
        assert session.id is not None
        assert len(session.id) == 8
        assert session.model == "test-model"
        assert session.guard is guard
        assert session.memory == ""
        assert session.executors == []
        assert session.evaluators == []

    def test_session_id_unique(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        s1 = Session("s1", guard, "model")
        s2 = Session("s2", guard, "model")
        assert s1.id != s2.id

    def test_create_executor(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        executor = session.create_executor("build blog")
        assert executor is not None
        assert len(session.executors) == 1
        assert executor.assigned_task == "build blog"

    def test_create_multiple_executors(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        e1 = session.create_executor("task 1")
        e2 = session.create_executor("task 2")
        assert len(session.executors) == 2
        assert e1.name != e2.name
        assert "Executor[test-1]" in e1.name
        assert "Executor[test-2]" in e2.name

    def test_create_evaluator_no_targets(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        evaluator = session.create_evaluator()
        assert evaluator is not None
        assert len(session.evaluators) == 1
        assert evaluator.target_executors == []

    def test_create_evaluator_with_targets(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        executor = session.create_executor("task")
        evaluator = session.create_evaluator(executor)
        assert evaluator is not None
        assert len(session.evaluators) == 1
        assert executor in evaluator.target_executors

    def test_create_evaluator_multiple_targets(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        e1 = session.create_executor("task 1")
        e2 = session.create_executor("task 2")
        evaluator = session.create_evaluator(e1, e2)
        assert len(evaluator.target_executors) == 2

    def test_get_executors_no_filter(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        session.create_executor("task 1")
        session.create_executor("task 2")
        result = session.get_executors()
        assert len(result) == 2

    def test_get_executors_with_filter(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        e1 = session.create_executor("task 1")
        session.create_executor("task 2")
        result = session.get_executors(lambda e: "1" in e.name)
        assert len(result) == 1
        assert e1 in result

    def test_get_executor_by_name(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        e1 = session.create_executor("task 1")
        result = session.get_executor("Executor[test-1]")
        assert result is e1

    def test_get_evaluator_by_name(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        ev = session.create_evaluator()
        result = session.get_evaluator("Evaluator[test-1]")
        assert result is ev

    def test_list_agents(self):
        from agents import Guard
        from session import Session

        guard = Guard()
        session = Session("test", guard, "model")
        e1 = session.create_executor("task 1")
        session.create_evaluator(e1)
        session.create_executor("task 2")
        listing = session.list_agents()
        assert "Session: test" in listing
        assert "Planner: Planner[test]" in listing
        assert "Executor[test-1]" in listing
        assert "Executor[test-2]" in listing
        assert "Evaluator[test-1] → [Executor[test-1]]" in listing


class TestSessionManager:
    """Tests for SessionManager class"""

    def test_session_manager_creation(self):
        from session import SessionManager

        sm = SessionManager("test-model")
        assert sm.model == "test-model"
        assert sm.sessions == {}
        assert sm.current_session is None

    def test_create_session(self):
        from session import SessionManager

        sm = SessionManager("model")
        session = sm.create_session("my-project")
        assert session is not None
        assert session.name == "my-project"
        assert sm.get_current() is session
        assert "my-project" in sm.sessions
        assert session.id in sm.sessions

    def test_create_multiple_sessions(self):
        from session import SessionManager

        sm = SessionManager("model")
        s1 = sm.create_session("proj1")
        s2 = sm.create_session("proj2")
        assert len(sm.sessions) >= 4
        assert s1 is not s2

    def test_create_session_auto_name(self):
        from session import SessionManager

        sm = SessionManager("model")
        s1 = sm.create_session()
        s2 = sm.create_session()
        assert s1.name.startswith("session")
        assert s2.name.startswith("session")

    def test_switch_session_by_name(self):
        from session import SessionManager

        sm = SessionManager("model")
        s1 = sm.create_session("proj1")
        sm.create_session("proj2")
        result = sm.switch_session("proj1")
        assert result is s1
        assert sm.get_current() is s1

    def test_switch_session_by_id(self):
        from session import SessionManager

        sm = SessionManager("model")
        s1 = sm.create_session("proj1")
        s2 = sm.create_session("proj2")
        result = sm.switch_session(s1.id)
        assert result is s1
        assert sm.get_current() is s1

    def test_switch_session_invalid(self):
        from session import SessionManager

        sm = SessionManager("model")
        sm.create_session("proj1")
        result = sm.switch_session("nonexistent")
        assert result is None

    def test_list_sessions(self):
        from session import SessionManager

        sm = SessionManager("model")
        sm.create_session("proj1")
        sm.create_session("proj2")
        listing = sm.list_sessions()
        assert "proj1" in listing
        assert "proj2" in listing
        assert "ID" in listing
        assert "Name" in listing
        assert "Executor" in listing
        assert "Evaluator" in listing

    def test_list_sessions_empty(self):
        from session import SessionManager

        sm = SessionManager("model")
        listing = sm.list_sessions()
        assert "沒有任何 session" in listing
