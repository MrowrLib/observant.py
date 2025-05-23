<img alt="Observant.py" src="https://mrowrlib.github.io/observant.py/assets/images/observant-py.png" width="300" />

# Observant.py

**Reactive state management for Python.**  
Track changes, validate data, implement undo/redo, and build reactive UIs with ease.

📚 **Full documentation**: [https://mrowrlib.github.io/observant.py](https://mrowrlib.github.io/observant.py)

[![PyPI version](https://badge.fury.io/py/observant.svg)](https://badge.fury.io/py/observant)
[![License: 0BSD](https://img.shields.io/badge/License-0BSD-990099.svg)](https://opensource.org/license/0BSD)
[![License: 0BSD](https://img.shields.io/badge/python-3.12-008026.svg)](https://www.python.org/)

## Installation

```bash
pip install observant
```

## Core Types

Observant.py provides a set of observable primitives:

- `Observable[T]`: Wraps a scalar value and notifies listeners on change
- `ObservableList[T]`: Observable wrapper around a list
- `ObservableDict[K, V]`: Observable wrapper around a dictionary
- `ObservableProxy[T]`: Wraps a dataclass or object and exposes its fields as observables

## Quick Examples

### Observable

```python
from observant import Observable

count = Observable(0)
count.on_change(lambda v: print(f"Count is now {v}"))
count.set(1)  # → Count is now 1
```

### ObservableList

```python
from observant import ObservableList

items = ObservableList(["a", "b"])
items.on_change(lambda change: print(f"List changed: {change.type.name}"))
items.append("c")  # → List changed: ADD
```

### ObservableDict

```python
from observant import ObservableDict

settings = ObservableDict({"theme": "dark"})
settings.on_change(lambda change: print(f"Settings changed: {change.key}"))
settings["theme"] = "light"  # → Settings changed: theme
```

### ObservableProxy

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

user = User(name="Ada", age=36)
proxy = ObservableProxy(user)

name = proxy.observable(str, "name")
name.on_change(lambda v: print(f"Name changed to {v}"))
name.set("Grace")  # → Name changed to Grace

# Save changes back to the original object
proxy.save_to(user)
print(user.name)  # → Grace
```

## Features

- ✅ **Type-safe observables**: Full type hints and generics support
- 🔁 **Undo/Redo support**: Track and revert changes
- 🧠 **Computed properties**: Create derived values that update automatically
- 🧪 **Validation**: Add validators to ensure data integrity
- 🔄 **Dirty state tracking**: Know which fields have been modified
- 🔗 **Sync back to original objects**: Optionally sync changes immediately

## Advanced Example: MVVM Pattern

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List

@dataclass
class TodoItem:
    text: str
    completed: bool

@dataclass
class TodoListModel:
    items: List[TodoItem]

class TodoListViewModel:
    def __init__(self, model: TodoListModel):
        self.model = model
        self.proxy = ObservableProxy(model)
        
        # Get observable list of items
        self.items = self.proxy.observable_list(TodoItem, "items")
        
        # Register computed properties
        self.proxy.register_computed(
            "completed_count",
            lambda: sum(1 for item in self.items if item.completed),
            ["items"]
        )
    
    def add_item(self, text: str):
        self.items.append(TodoItem(text=text, completed=False))
    
    def toggle_item(self, index: int):
        item = self.items[index]
        item_proxy = ObservableProxy(item)
        completed_obs = item_proxy.observable(bool, "completed")
        completed_obs.set(not completed_obs.get())
        item_proxy.save_to(item)
    
    def save(self):
        self.proxy.save_to(self.model)

# Usage
model = TodoListModel(items=[])
view_model = TodoListViewModel(model)

# Listen for changes
view_model.proxy.computed(int, "completed_count").on_change(
    lambda count: print(f"Completed: {count}")
)

# Add and toggle items
view_model.add_item("Learn Python")
view_model.add_item("Learn Observant.py")
view_model.toggle_item(0)  # → Completed: 1
```

## Learn More

Check out the full documentation and examples at [https://mrowrlib.github.io/observant.py](https://mrowrlib.github.io/observant.py)
