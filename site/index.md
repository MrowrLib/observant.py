<img src="assets/images/observant-py.png" width="300" />

# Observant.py

**Reactive state management for Python**

[![PyPI version](https://badge.fury.io/py/observant.svg)](https://badge.fury.io/py/observant)
[![License: 0BSD](https://img.shields.io/badge/License-0BSD-990099.svg)](https://opensource.org/license/0BSD)
[![License: 0BSD](https://img.shields.io/badge/python-3.12-008026.svg)](https://www.python.org/)

## What is Observant.py?

Observant.py is a lightweight, type-safe library for observable state management in Python. It provides a reactive programming model that makes it easy to:

- Track changes to data
- Validate data
- Implement undo/redo functionality
- Create computed properties
- Synchronize state between models

## Key Features

- **Type-safe**: Full type hints for excellent IDE support and static analysis
- **Observable primitives**: Track changes to values, lists, and dictionaries
- **Validation**: Add validators to ensure data integrity
- **Undo/Redo**: Built-in support for tracking and reverting changes
- **Computed properties**: Define properties that automatically update based on dependencies
- **Proxy objects**: Wrap existing models with observable behavior
- **Minimal dependencies**: Pure Python with no external requirements

## Quick Example

```python
from observant import Observable, ObservableProxy
from dataclasses import dataclass

# Create a simple observable value
counter = Observable(0)
counter.on_change(lambda value: print(f"Counter changed to {value}"))
counter.set(1)  # Prints: Counter changed to 1

# Create a model with observable properties
@dataclass
class User:
    name: str
    age: int

user = User(name="Ada", age=36)
proxy = ObservableProxy(user)

# Add validation
proxy.add_validator("age", lambda age: "Age must be positive" if age <= 0 else None)

# Create a computed property
proxy.register_computed(
    "greeting", 
    lambda: f"Hello, {proxy.observable(str, 'name').get()}!",
    ["name"]
)

# Listen for changes
proxy.observable(str, "name").on_change(
    lambda name: print(f"Name changed to {name}")
)

# Update a value
proxy.observable(str, "name").set("Grace")  # Prints: Name changed to Grace

# Access computed property
print(proxy.computed(str, "greeting").get())  # Prints: Hello, Grace!
```

## Installation

```bash
pip install observant
```

## Next Steps

- Check out the [Getting Started](getting_started.md) guide
- Explore the [Reference](reference/observable.md) documentation
- See [Examples](examples/basic.md) of common patterns
