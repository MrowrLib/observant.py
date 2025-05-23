# All Types

This page provides an overview of all the types available in Observant.py, including some specialized types that aren't covered in the main documentation.

## Core Types

### Observable

The `Observable` class is the foundation of Observant.py. It wraps a value and notifies listeners when the value changes.

```python
from observant import Observable

# Create an observable with an initial value
counter = Observable(0)

# Register a callback to be notified when the value changes
counter.on_change(lambda value: print(f"Counter changed to {value}"))

# Change the value
counter.set(1)  # Prints: Counter changed to 1
```

[Learn more about Observable](observable.md)

### ObservableList

The `ObservableList` class provides an observable wrapper around a Python list. It notifies listeners when items are added, removed, or the list is cleared.

```python
from observant import ObservableList

# Create an observable list with initial values
fruits = ObservableList(["apple", "banana"])

# Register a callback to be notified when the list changes
fruits.on_change(lambda change: print(f"List changed: {change.type.name}"))

# Modify the list
fruits.append("cherry")  # Prints: List changed: ADD
```

[Learn more about ObservableList](observable_list.md)

### ObservableDict

The `ObservableDict` class provides an observable wrapper around a Python dictionary. It notifies listeners when entries are added, updated, or removed.

```python
from observant import ObservableDict

# Create an observable dictionary with initial values
settings = ObservableDict({"theme": "dark", "notifications": True})

# Register a callback to be notified when the dictionary changes
settings.on_change(lambda change: print(f"Dict changed: {change.key}"))

# Modify the dictionary
settings["theme"] = "light"  # Prints: Dict changed: theme
```

[Learn more about ObservableDict](observable_dict.md)

### ObservableProxy

The `ObservableProxy` class is the most powerful component of Observant.py. It wraps an existing object and exposes its fields as observables, allowing you to track changes, validate data, implement undo/redo, create computed properties, and synchronize state.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

# Create a user
user = User(name="Ada", age=36)

# Create a proxy
proxy = ObservableProxy(user)

# Access fields as observables
name = proxy.observable(str, "name")
name.on_change(lambda value: print(f"Name changed to {value}"))

# Modify a field
name.set("Grace")  # Prints: Name changed to Grace
```

[Learn more about ObservableProxy](proxy/index.md)
