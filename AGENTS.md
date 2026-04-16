# AGENTS.md - Agent Coding Guidelines

## Overview

This is a knowledge base and educational code repository containing:
- Wiki articles (`_wiki/`)
- Code examples (`_code/`, `_wiki/_code/`)
- Various programming projects

## Build & Test Commands

### Running Python Files

```bash
# Run a single Python file
python path/to/file.py

# Run with specific Python version
python3 path/to/file.py
```

### Running Tests

Most test files are self-contained and can be run directly:

```bash
# Run a test file directly
python path/to/test_*.py
python path/to/tests/*.py

# Run a specific test function (if pytest-style)
python -m pytest path/to/test_file.py::test_function -v
```

### Running pytest (if available)

```bash
# Run all tests
pytest

# Run specific test file
pytest path/to/test_file.py

# Run specific test function
pytest path/to/test_file.py::test_function_name -v

# Run tests matching pattern
pytest -k "pattern"
```

### Linting

```bash
# Run ruff linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Run isort for imports
isort --check .

# Run mypy for type checking
mypy .
```

## Code Style Guidelines

### General Principles

- Write clear, readable code with helpful comments
- Prefer explicit over implicit
- Keep functions focused and small (< 50 lines)
- Use descriptive variable and function names

### Imports

Standard order (PEP 8):
1. Standard library (`import os`, `import math`)
2. Third-party (`import numpy as np`, `from torch import nn`)
3. Local (`from . import module`)

```python
import os
import math
from typing import Tuple, List, Optional

import numpy as np
from dataclasses import dataclass
```

### Formatting

- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use blank lines to separate classes and major functions
- No trailing whitespace

### Type Annotations

Use type hints for function signatures:

```python
def process_data(data: List[int]) -> Tuple[int, str]:
    """Process input data and return results."""
    result: int = sum(data)
    return result, f"Processed {result} items"
```

Use `Optional[X]` instead of `X | None`:

```python
def find_item(items: List[str], target: str) -> Optional[int]:
    """Find index of target item."""
    for i, item in enumerate(items):
        if item == target:
            return i
    return None
```

### Naming Conventions

| Type | Convention | Example |
|------|-------------|--------|
| Variables | snake_case | `user_data`, `max_value` |
| Functions | snake_case | `calculate_total()` |
| Classes | PascalCase | `DataProcessor` |
| Constants | UPPER_SNAKE | `MAX_BUFFER_SIZE` |
| Files | snake_case | `data_loader.py` |

### Classes

```python
class DataProcessor:
    """Process and transform data."""
    
    def __init__(self, config: dict):
        self.config = config
        self._cache: dict = {}
    
    def process(self, data: List[int]) -> List[int]:
        """Process data with caching."""
        cache_key = tuple(data)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = self._transform(data)
        self._cache[cache_key] = result
        return result
    
    def _transform(self, data: List[int]) -> List[int]:
        """Internal transformation logic."""
        return [x * 2 for x in data]
```

### Error Handling

Use specific exceptions and meaningful messages:

```python
def load_config(path: str) -> dict:
    """Load configuration from file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")
```

### Documentation

Use docstrings for public functions and classes:

```python
def calculate_mean(values: List[float]) -> float:
    """Calculate arithmetic mean of values.
    
    Args:
        values: List of numeric values.
    
    Returns:
        Arithmetic mean of values.
    
    Raises:
        ValueError: If values list is empty.
    """
    if not values:
        raise ValueError("Cannot calculate mean of empty list")
    
    return sum(values) / len(values)
```

### Testing Guidelines

Write tests as standalone executable files:

```python
def test_example():
    """Example test function."""
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0

if __name__ == "__main__":
    test_example()
    print("All tests passed!")
```

## Project Structure

This repository uses a **flat structure**: category folders (e.g., `系統程式/`) contain only files, not nested subdirectories.

```
repository/
├── _wiki/           # Wiki articles and code
├── _code/           # Standalone code projects
├── 系統程式/         # Category: contains .py, .md files only
├── 機器學習/        # Category: contains .py, .md files only
└── 演算法/         # Category: contains .py, .md files only
```

Each category folder organizes its own index.md, code files, and documentation directly.

## Common Patterns

### Data Classes

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Result:
    """Container for computation results."""
    value: float
    iterations: int
    metadata: List[str]
```

### Property Decorators

```python
class Calculator:
    def __init__(self):
        self._history: List[float] = []
    
    @property
    def history(self) -> List[float]:
        """Read-only access to history."""
        return self._history.copy()
```

### Context Managers

```python
class Resource:
    def __init__(self, path: str):
        self.path = path
        self._file = None
    
    def __enter__(self):
        self._file = open(self.path)
        return self
    
    def __exit__(self, *args):
        if self._file:
            self._file.close()
```

## Working with This Repository

1. **Python versions**: Use Python 3.8+ (check `python3 --version`)
2. **Dependencies**: Check for `requirements.txt` or `pyproject.toml` in project subdirectories
3. **Running Makefiles**: Some projects have Makefiles - use `make target` in that directory
4. **Virtual environments**: Activate with `source venv/bin/activate` if present

## Notes

- This repository contains many independent projects
- No unified test framework across all projects
- Each subdirectory may have its own conventions
- Check for local `README.md` or `AGENTS.md` in subdirectories