#!/usr/bin/env python3
# tests/test_agents.py - pytest tests for Agent classes

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAgentBase:
    """Tests for Agent base class"""

    def test_agent_creation(self):
        from agents import Agent

        agent = Agent("TestAgent", "Test system prompt")
        assert agent.name == "TestAgent"
        assert agent.system == "Test system prompt"
        assert agent.memory == ""
        assert agent.messages == []
        assert agent.max_turns == 5

    def test_agent_read_write(self):
        from agents import Agent

        agent = Agent("TestAgent")
        agent.read("<user>hello</user>")
        agent.write("<assistant>hi</assistant>")
        assert len(agent.messages) == 2
        assert "<user>hello</user>" in agent.messages
        assert "<assistant>hi</assistant>" in agent.messages

    def test_agent_record(self):
        from agents import Agent

        agent = Agent("TestAgent")
        agent.record("user msg", "assistant msg")
        assert len(agent.messages) == 2
        assert "  <user>user msg</user>" in agent.messages
        assert "  <assistant>assistant msg</assistant>" in agent.messages

    def test_agent_memory(self):
        from agents import Agent

        agent = Agent("TestAgent")
        agent.memory = "<item>important info</item>"
        context = agent.get_context()
        assert "<memory>" in context
        assert "important info" in context

    def test_agent_get_context(self):
        from agents import Agent

        agent = Agent("TestAgent")
        agent.memory = "<item>memory</item>"
        agent.messages = ["  <user>hello</user>"]
        context = agent.get_context()
        assert "<memory>" in context
        assert "<history>" in context


class TestGuard:
    """Tests for Guard class"""

    def test_guard_creation(self):
        from agents import Guard

        guard = Guard()
        assert guard.allowed_paths == set()

    def test_guard_add_path(self):
        from agents import Guard

        guard = Guard()
        guard.allowed_paths.add("/tmp/test")
        assert "/tmp/test" in guard.allowed_paths

    def test_check_outside_access_integration(self):
        from agents import check_outside_access

        cwd = "/home/user/project"
        needs, path = check_outside_access("ls /tmp", cwd)
        assert needs is True
        assert path == "/tmp"


class TestPlanner:
    """Tests for Planner class"""

    def test_planner_creation(self):
        from agents import Guard, Planner

        guard = Guard()
        planner = Planner(guard, "TestPlanner")
        assert planner.name == "TestPlanner"
        assert planner.guard is guard
        assert planner.memory == ""
        assert planner.messages == []

    def test_planner_system_prompt(self):
        from agents import Guard, Planner

        guard = Guard()
        planner = Planner(guard)
        assert "Planner" in planner.system
        assert "<shell>" in planner.system


class TestExecutor:
    """Tests for Executor class"""

    def test_executor_creation(self):
        from agents import Guard, Executor

        guard = Guard()
        executor = Executor(guard, "TestExecutor")
        assert executor.name == "TestExecutor"
        assert executor.guard is guard
        assert executor.assigned_task == ""

    def test_executor_with_task(self):
        from agents import Guard, Executor

        guard = Guard()
        executor = Executor(guard, "TaskExecutor")
        executor.assigned_task = "Build a blog system"
        assert executor.assigned_task == "Build a blog system"

    def test_executor_system_prompt(self):
        from agents import Guard, Executor

        guard = Guard()
        executor = Executor(guard)
        assert "Executor" in executor.system
        assert "Planner" in executor.system


class TestEvaluator:
    """Tests for Evaluator class"""

    def test_evaluator_creation(self):
        from agents import Guard, Evaluator

        guard = Guard()
        evaluator = Evaluator(guard, "TestEvaluator")
        assert evaluator.name == "TestEvaluator"
        assert evaluator.guard is guard
        assert evaluator.target_executors == []

    def test_evaluator_with_target(self):
        from agents import Guard, Executor, Evaluator

        guard = Guard()
        executor = Executor(guard, "TaskExec")
        evaluator = Evaluator(guard, "TaskEval")
        evaluator.follow(executor)
        assert executor in evaluator.target_executors

    def test_evaluator_follow_multiple(self):
        from agents import Guard, Executor, Evaluator

        guard = Guard()
        e1 = Executor(guard, "Exec1")
        e2 = Executor(guard, "Exec2")
        evaluator = Evaluator(guard, "TaskEval")
        evaluator.follow(e1, e2)
        assert len(evaluator.target_executors) == 2
        assert e1 in evaluator.target_executors
        assert e2 in evaluator.target_executors

    def test_evaluator_system_prompt(self):
        from agents import Guard, Evaluator

        guard = Guard()
        evaluator = Evaluator(guard)
        assert "Evaluator" in evaluator.system
        assert "Executor" in evaluator.system
