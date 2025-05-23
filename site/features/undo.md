# Undo and Redo

Observant provides built-in undo and redo functionality, allowing you to track changes to your data and revert them if needed. This page explains how the undo/redo system works in Observant.

## Overview

The undo/redo system in Observant is field-based, meaning you can undo changes to individual fields independently. This gives you fine-grained control over which changes to revert.

Key features of the undo/redo system:

- Per-field undo/redo
- Configurable undo stack size
- Debounce support for rapid changes
- Integration with validation and dirty tracking

## Enabling Undo

To enable undo functionality, you can either:

1. Enable it globally when creating the proxy
2. Enable it for specific fields after creating the proxy

### Global Undo

To enable undo globally, set `undo=True` when creating the proxy:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

user = User(name="Alice", age=30)
proxy = ObservableProxy(user, undo=True)  # Enable undo for all fields
```

### Per-Field Undo

To enable undo for specific fields, use the `set_undo_config` method:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int
    email: str

user = User(name="Alice", age=30, email="alice@example.com")
proxy = ObservableProxy(user)  # Undo disabled by default

# Enable undo for specific fields
proxy.set_undo_config("name", enabled=True)
proxy.set_undo_config("age", enabled=True)
# email field will not have undo enabled
```

## Undo Configuration

The undo system can be configured with several options:

- `enabled`: Whether undo is enabled for a field
- `undo_max`: Maximum number of undo steps to store
- `undo_debounce_ms`: Time in milliseconds to wait before recording a new undo step

### undo_max

The `undo_max` option limits the number of undo steps that are stored for a field. This prevents the undo stack from growing too large and consuming too much memory.

```python
# Limit to 10 undo steps
proxy.set_undo_config("name", enabled=True, undo_max=10)
```

### undo_debounce_ms

The `undo_debounce_ms` option adds debounce behavior to the undo system. If multiple changes are made to a field within the debounce time, only the last change is recorded as an undo step.

This is useful for fields that change rapidly, such as text fields during typing:

```python
# Debounce undo steps by 500ms
proxy.set_undo_config("name", enabled=True, undo_debounce_ms=500)

# These rapid changes will be combined into a single undo step
proxy.observable(str, "name").set("A")
proxy.observable(str, "name").set("Al")
proxy.observable(str, "name").set("Ali")
proxy.observable(str, "name").set("Alic")
proxy.observable(str, "name").set("Alice")

# Only one undo step is created
proxy.undo("name")  # Reverts directly to the original value
```

## Undo/Redo API

Once undo is enabled, you can use the following methods to undo and redo changes:

- `undo(field)`: Undo the last change to a field
- `redo(field)`: Redo the last undone change to a field
- `can_undo(field)`: Check if there are any undo steps available for a field
- `can_redo(field)`: Check if there are any redo steps available for a field

### Basic Undo/Redo

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

user = User(name="Alice", age=30)
proxy = ObservableProxy(user, undo=True)

# Make some changes
proxy.observable(str, "name").set("Bob")
proxy.observable(int, "age").set(25)

# Undo changes
proxy.undo("name")  # Reverts name to "Alice"
proxy.undo("age")   # Reverts age to 30

# Redo changes
proxy.redo("name")  # Sets name back to "Bob"
proxy.redo("age")   # Sets age back to 25
```

### Checking Undo/Redo Availability

You can check if undo or redo is available for a field using the `can_undo` and `can_redo` methods:

```python
# Check if undo is available
if proxy.can_undo("name"):
    proxy.undo("name")

# Check if redo is available
if proxy.can_redo("name"):
    proxy.redo("name")
```

These methods return observables, so you can also listen for changes:

```python
# Listen for changes to undo availability
proxy.can_undo("name").on_change(lambda can_undo: 
    print(f"Undo available for name: {can_undo}"))

# Listen for changes to redo availability
proxy.can_redo("name").on_change(lambda can_redo: 
    print(f"Redo available for name: {can_redo}"))
```

## Per-Field vs Global Undo

Observant's undo system is field-based, meaning each field has its own undo stack. This allows you to undo changes to one field without affecting others.

```python
# Make changes to multiple fields
proxy.observable(str, "name").set("Bob")
proxy.observable(int, "age").set(25)

# Undo only the name change
proxy.undo("name")  # Reverts name to "Alice"

# Age remains changed
print(proxy.observable(int, "age").get())  # 25
```

This field-based approach gives you more control over which changes to undo, but it also means you need to undo each field separately if you want to undo all changes.

If you need to undo all changes at once, you can iterate over the fields:

```python
# Undo all fields
for field in ["name", "age", "email"]:
    if proxy.can_undo(field).get():
        proxy.undo(field)
```

## Limitations and Gotchas

### Sync and Undo

The `sync` and `undo` options can be used together, but this can lead to unexpected behavior. When `sync=True`, changes are immediately applied to the underlying model, which means that undo operations will not affect the model until you call `save_to`.

```python
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=True, undo=True)

# Make a change
proxy.observable(str, "name").set("Bob")
print(user.name)  # "Bob" (sync=True applies changes immediately)

# Undo the change
proxy.undo("name")
print(proxy.observable(str, "name").get())  # "Alice"
print(user.name)  # Still "Bob" until save_to is called

# Save changes back to the model
proxy.save_to(user)
print(user.name)  # Now "Alice"
```

For this reason, it's generally recommended to use `sync=False` when using undo functionality.

### Collection Fields

For list and dictionary fields, undo/redo works on the entire collection, not individual elements. This means that if you make multiple changes to a collection, undoing will revert all of those changes at once.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class TodoList:
    tasks: list[str]

todo_list = TodoList(tasks=["Buy milk"])
proxy = ObservableProxy(todo_list, undo=True)

# Get the observable list
tasks = proxy.observable_list(str, "tasks")

# Make multiple changes
tasks.append("Write docs")
tasks.append("Fix bugs")
tasks.remove("Buy milk")

# Undo all changes at once
proxy.undo("tasks")  # Reverts to ["Buy milk"]
```

### Computed Fields

Computed fields are not directly undoable, since their values are derived from other fields. However, when you undo changes to a field that a computed field depends on, the computed field will update accordingly.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    first_name: str
    last_name: str

user = User(first_name="Alice", last_name="Smith")
proxy = ObservableProxy(user, undo=True)

# Register a computed property
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
    dependencies=["first_name", "last_name"]
)

# Make a change
proxy.observable(str, "first_name").set("Bob")
print(proxy.computed(str, "full_name").get())  # "Bob Smith"

# Undo the change
proxy.undo("first_name")
print(proxy.computed(str, "full_name").get())  # "Alice Smith"
```

### Validation and Undo

When you undo a change, validation is automatically re-run for the affected field. This means that if you undo a change that makes a field invalid, the validation errors will be updated accordingly.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    username: str

user = User(username="")
proxy = ObservableProxy(user, undo=True)

# Add a validator
proxy.add_validator("username", lambda v: "Username required" if not v else None)

# Set a valid value
proxy.observable(str, "username").set("alice")
print(proxy.is_valid())  # True

# Undo the change
proxy.undo("username")
print(proxy.is_valid())  # False
print(proxy.validation_for("username").get())  # ["Username required"]
```

## Next Steps

Now that you understand how undo and redo work in Observant, you might want to explore:

- [Computed Properties](computed.md): Create properties that depend on other fields
- [Dirty Tracking](dirty.md): Track unsaved changes
- [Sync vs Non-Sync](sync.md): Understand immediate vs. deferred updates
