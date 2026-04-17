#!/usr/bin/env python3
# session.py - Session and SessionManager classes

import uuid
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from agents import Guard, Executor, Evaluator, Planner


class Session:
    """A session represents a thread of work with its own planner, executors, and evaluators"""

    def __init__(self, name: str, guard: "Guard", model: str):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.model = model
        self.guard = guard
        from agents import Planner, Executor, Evaluator

        self.planner = Planner(guard, f"Planner[{name}]")
        self.executors: list["Executor"] = []
        self.evaluators: list["Evaluator"] = []
        self.max_turns: int = 5
        self.memory: str = ""

    def create_executor(self, task: str = "") -> "Executor":
        """Create a new executor for a task"""
        from agents import Executor

        idx = len(self.executors) + 1
        exec = Executor(self.guard, f"Executor[{self.name}-{idx}]")
        exec.assigned_task = task
        self.executors.append(exec)
        exec.start()
        return exec

    def create_evaluator(self, *targets: "Executor") -> "Evaluator":
        """Create a new evaluator, optionally following specific executors"""
        from agents import Evaluator

        idx = len(self.evaluators) + 1
        eval = Evaluator(self.guard, f"Evaluator[{self.name}-{idx}]")
        for exec in targets:
            eval.follow(exec)
        self.evaluators.append(eval)
        eval.start()
        return eval

    def get_executors(
        self, filter_fn: Optional[Callable[["Executor"], bool]] = None
    ) -> list["Executor"]:
        """Get executors, optionally filtered by a function"""
        if filter_fn is None:
            return self.executors.copy()
        return [e for e in self.executors if filter_fn(e)]

    def get_evaluator(self, identifier: str) -> Optional["Evaluator"]:
        """Get evaluator by name or partial name"""
        for ev in self.evaluators:
            if identifier in ev.name:
                return ev
        return None

    def get_executor(self, identifier: str) -> Optional["Executor"]:
        """Get executor by name or partial name"""
        for e in self.executors:
            if identifier in e.name:
                return e
        return None

    def list_agents(self) -> str:
        lines = [
            f"Session: {self.name} (id={self.id})",
            f"  Planner: {self.planner.name}",
            f"  Executors ({len(self.executors)}):",
        ]
        for e in self.executors:
            lines.append(f"    - {e.name}")
        lines.append(f"  Evaluators ({len(self.evaluators)}):")
        for ev in self.evaluators:
            if ev.target_executors:
                targets = ", ".join(e.name for e in ev.target_executors)
                lines.append(f"    - {ev.name} → [{targets}]")
            else:
                lines.append(f"    - {ev.name} (following all)")
        return "\n".join(lines)

    def shutdown(self):
        """Stop all agents in this session"""
        self.planner.stop()
        for e in self.executors:
            e.stop()
        for ev in self.evaluators:
            ev.stop()


class SessionManager:
    """Manages multiple sessions"""

    def __init__(self, model: str):
        self.model = model
        self.sessions: dict[str, Session] = {}
        self.current_session: Optional[Session] = None
        from agents import Guard

        self.guard = Guard()
        self._session_counter: int = 0

    def create_session(self, name: Optional[str] = None) -> Session:
        """Create a new session"""
        self._session_counter += 1
        if name is None:
            name = f"session{self._session_counter}"

        if name in self.sessions:
            name = f"{name}_{self._session_counter}"

        session = Session(name, self.guard, self.model)
        self.sessions[name] = session
        self.sessions[session.id] = session
        session.planner.start()
        self.current_session = session
        return session

    def switch_session(self, identifier: str) -> Optional[Session]:
        """Switch to a session by name or id"""
        if identifier in self.sessions:
            self.current_session = self.sessions[identifier]
            return self.current_session
        return None

    def list_sessions(self) -> str:
        if not self.sessions:
            return "目前沒有任何 session"
        lines = ["所有 Session:"]
        lines.append(f"{'ID':<12} {'Name':<20} {'Executor':<10} {'Evaluator':<10}")
        lines.append("-" * 55)
        for name, session in self.sessions.items():
            if name == session.id:
                continue
            marker = " ← 目前" if session == self.current_session else ""
            lines.append(
                f"{session.id:<12} {session.name:<20} {len(session.executors):<10} {len(session.evaluators):<10}{marker}"
            )
        return "\n".join(lines)

    def get_current(self) -> Optional[Session]:
        return self.current_session

    def shutdown_all(self):
        """Stop all sessions"""
        for session in self.sessions.values():
            session.shutdown()
        self.sessions.clear()
        self.current_session = None
