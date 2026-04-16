# AGENTS.md - v4-agent-context Project

## Overview

This directory contains a Python-based AI agent (`agent0.py`) that uses Ollama API for natural language processing. The agent has memory management capabilities and command safety review features.

**Dependencies:** aiohttp, asyncio (stdlib)

## Build & Test Commands

### Running Python Files

```bash
# Run agent0.py (interactive CLI agent)
python agent0.py

# Run hello.py
python hello.py
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_context.py -v
python -m pytest tests/test_reviewer.py -v

# Run only unit tests (skip Ollama integration)
python -m pytest tests/ -v -m "not asyncio"
```

### Dependencies Installation

```bash
# Install aiohttp if not present
pip install aiohttp
```

## Code Style Guidelines

### General Principles

- Write clear, readable code with helpful comments
- Keep functions focused and small (< 50 lines)
- Use descriptive variable and function names
- Use `async/await` for I/O operations

### Imports

Standard order (PEP 8):
1. Standard library (`import os`, `import re`, `import asyncio`)
2. Third-party (`import aiohttp`)
3. Local (`from . import module`)

```python
import subprocess
import os
import asyncio
import re

import aiohttp
```

### Formatting

- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use blank lines to separate major sections (Configuration, Memory, Functions, etc.)
- Use `---` style section separators for documentation

### Type Annotations

Use type hints for function signatures:

```python
async def call_ollama(prompt: str, system: str = "") -> str:
    ...

def check_outside_access(cmd: str, cwd: str) -> tuple[bool, str]:
    ...
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `conversation_history`, `key_info` |
| Functions | snake_case | `call_ollama`, `review_command` |
| Classes | PascalCase | `DataProcessor` |
| Constants | UPPER_SNAKE | `MAX_TURNS`, `MODEL` |
| Files | snake_case | `agent0.py`, `test_reviewer.py` |

### Section Organization Pattern

Use these section headers in Python files:

```python
#!/usr/bin/env python3
# Script description

# ─── Configuration ───
# Constants and configuration

# ─── Memory ───
# Memory-related variables

# ─── Functions ───
# Helper functions

# ─── Main ───
# Main execution logic

if __name__ == "__main__":
    main()
```

### Error Handling

Use try/except with specific exception types:

```python
try:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
except Exception as e:
    print(f"錯誤：{e}")
```

## Project-Specific Patterns

### Shell Command Review Pattern

The agent uses a safety review system before executing shell commands:

```python
async def review_command(cmd: str) -> tuple[bool, str]:
    # Returns (is_safe, reason)
```

### Memory Management Pattern

Use XML-style tags for structured memory:

```python
conversation_history.append(f"  <user>{user_input}</user>")
conversation_history.append(f"  <assistant>{assistant_response}</assistant>")
```

### Ollama API Pattern

Always include timeout and error handling:

```python
async with aiohttp.ClientSession() as session:
    async with session.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=aiohttp.ClientTimeout(total=120)
    ) as resp:
        result = await resp.json()
        return result.get("response", "").strip()
```

### User Interaction Pattern

For interactive prompts, handle EOFError and KeyboardInterrupt gracefully:

```python
try:
    user_input = input("你：").strip()
except (EOFError, KeyboardInterrupt):
    print("\n再見！")
    break
```

## File Structure

```
v4-agent-context/
├── agent0.py          # Main AI agent with memory
├── hello.py           # Simple test file
├── test_reviewer.py   # Security reviewer tests
├── test_reviewer.sh   # Bash test runner
├── test.sh            # Integration test script
├── test.md            # Test specification
├── blog/              # Generated blog output
└── _doc/              # Documentation and session logs
```

## Important Notes

- The agent requires Ollama running at `http://localhost:11434`
- Default model: `minimax-m2.5:cloud`
- Commands that access directories outside the workspace require user confirmation
- Shell commands are reviewed for safety before execution
