# Change Tracking

At the core of Observant is the ability to track changes to your data and react to those changes. This page explains how change tracking works in Observant.

## Overview

Observant provides three main types of observable objects:

1. **Observable**: For tracking changes to scalar values (strings, numbers, booleans, etc.)
2. **ObservableList**: For tracking changes to lists
3. **ObservableDict**: For tracking changes to dictionaries

Each of these objects allows you to register callbacks that are called when the value changes.

## Scalar Observables

The `Observable` class is the simplest form of change tracking in Observant. It wraps a single value and notifies listeners when that value changes.

```python
from observant import Observable

# Create an observable with an initial value
counter = Observable[int](0)

# Register a callback to be notified when the value changes
counter.on_change(lambda value: print(f"Counter changed to: {value}"))

# Change the value
counter.set(1)  # Prints: "Counter changed to: 1"

# Get the current value
current_value = counter.get()  # Returns: 1
```

### Multiple Callbacks

You can register multiple callbacks for the same observable:

```python
counter = Observable[int](0)

# Register multiple callbacks
counter.on_change(lambda value: print(f"Callback 1: {value}"))
counter.on_change(lambda value: print(f"Callback 2: {value}"))

# Change the value
counter.set(1)  # Prints both callback messages
```

### Suppressing Notifications

Sometimes you may want to update a value without triggering callbacks. You can do this by setting `notify=False`:

```python
counter = Observable[int](0)
counter.on_change(lambda value: print(f"Counter changed to: {value}"))

# Update without notification
counter.set(1, notify=False)  # No callback is triggered

# The value is still updated
print(counter.get())  # Prints: 1
```

## List Observables

The `ObservableList` class tracks changes to a list, including additions, removals, and modifications.

```python
from observant import ObservableList, ObservableCollectionChangeType

# Create an observable list
tasks = ObservableList[str](["Task 1"])

# Register a callback
def on_tasks_change(change):
    if change.type == ObservableCollectionChangeType.ADD:
        if hasattr(change, "item"):
            print(f"Added task: {change.item}")
        else:
            print(f"Added tasks: {change.items}")
    elif change.type == ObservableCollectionChangeType.REMOVE:
        if hasattr(change, "item"):
            print(f"Removed task: {change.item}")
        else:
            print(f"Removed tasks: {change.items}")
    elif change.type == ObservableCollectionChangeType.CLEAR:
        print(f"Cleared tasks: {change.items}")

tasks.on_change(on_tasks_change)

# Add an item
tasks.append("Task 2")  # Prints: "Added task: Task 2"

# Add multiple items
tasks.extend(["Task 3", "Task 4"])  # Prints: "Added tasks: ['Task 3', 'Task 4']"

# Remove an item
tasks.remove("Task 1")  # Prints: "Removed task: Task 1"

# Clear the list
tasks.clear()  # Prints: "Cleared tasks: ['Task 2', 'Task 3', 'Task 4']"
```

### List Change Information

When a list changes, the callback receives a `ObservableListChange` object with the following properties:

- `type`: The type of change (ADD, REMOVE, CLEAR)
- `index`: The index where the change occurred (for ADD and REMOVE)
- `item`: The item that was added or removed (for single-item changes)
- `items`: The items that were added or removed (for multi-item changes)

### List Operations

`ObservableList` supports all standard Python list operations, including:

- `append(item)`: Add an item to the end of the list
- `extend(items)`: Add multiple items to the end of the list
- `insert(index, item)`: Insert an item at a specific index
- `remove(item)`: Remove an item from the list
- `pop([index])`: Remove and return an item at a specific index (or the last item if no index is provided)
- `clear()`: Remove all items from the list
- `sort()`: Sort the list in place
- `reverse()`: Reverse the list in place
- `__getitem__(index)`: Access an item by index (`list[index]`)
- `__setitem__(index, value)`: Set an item by index (`list[index] = value`)
- `__delitem__(index)`: Delete an item by index (`del list[index]`)

## Dict Observables

The `ObservableDict` class tracks changes to a dictionary, including additions, updates, and removals.

```python
from observant import ObservableDict, ObservableCollectionChangeType

# Create an observable dictionary
settings = ObservableDict[str, str]({"theme": "dark"})

# Register a callback
def on_settings_change(change):
    if change.type == ObservableCollectionChangeType.ADD:
        if hasattr(change, "key"):
            print(f"Added setting: {change.key} = {change.value}")
        else:
            print(f"Added settings: {change.items}")
    elif change.type == ObservableCollectionChangeType.UPDATE:
        if hasattr(change, "key"):
            print(f"Updated setting: {change.key} = {change.value}")
        else:
            print(f"Updated settings: {change.items}")
    elif change.type == ObservableCollectionChangeType.REMOVE:
        if hasattr(change, "key"):
            print(f"Removed setting: {change.key}")
        else:
            print(f"Removed settings: {change.items}")
    elif change.type == ObservableCollectionChangeType.CLEAR:
        print(f"Cleared settings: {change.items}")

settings.on_change(on_settings_change)

# Add a new key
settings["language"] = "en"  # Prints: "Added setting: language = en"

# Update an existing key
settings["theme"] = "light"  # Prints: "Updated setting: theme = light"

# Remove a key
del settings["theme"]  # Prints: "Removed setting: theme"

# Update multiple keys at once
settings.update({"theme": "dark", "font": "Arial"})  # Prints appropriate messages

# Clear the dictionary
settings.clear()  # Prints: "Cleared settings: {'language': 'en'}"
```

### Dict Change Information

When a dictionary changes, the callback receives a `ObservableDictChange` object with the following properties:

- `type`: The type of change (ADD, UPDATE, REMOVE, CLEAR)
- `key`: The key that was added, updated, or removed (for single-item changes)
- `value`: The value that was added or updated (for single-item changes)
- `items`: The items that were added, updated, or removed (for multi-item changes)

### Dict Operations

`ObservableDict` supports all standard Python dictionary operations, including:

- `__getitem__(key)`: Access a value by key (`dict[key]`)
- `__setitem__(key, value)`: Set a value by key (`dict[key] = value`)
- `__delitem__(key)`: Delete a key-value pair (`del dict[key]`)
- `get(key, [default])`: Get a value by key, with an optional default value
- `setdefault(key, [default])`: Get a value by key, or set it to a default value if the key doesn't exist
- `pop(key, [default])`: Remove and return a value by key, with an optional default value
- `popitem()`: Remove and return an arbitrary key-value pair
- `clear()`: Remove all items from the dictionary
- `update(other)`: Update the dictionary with key-value pairs from another dictionary

## on_change Callbacks

The `on_change` method is used to register callbacks that are called when the value changes. The callback function receives different arguments depending on the type of observable:

- For `Observable`, the callback receives the new value.
- For `ObservableList`, the callback receives a `ObservableListChange` object.
- For `ObservableDict`, the callback receives a `ObservableDictChange` object.

### Callback Behavior

Callbacks are called immediately after the value changes. If multiple callbacks are registered, they are called in the order they were registered.

```python
counter = Observable[int](0)

# Register callbacks
counter.on_change(lambda value: print(f"First callback: {value}"))
counter.on_change(lambda value: print(f"Second callback: {value}"))

# Change the value
counter.set(1)
# Prints:
# First callback: 1
# Second callback: 1
```

### Reentrant Callbacks

Callbacks can trigger other changes, which can in turn trigger other callbacks. This is known as "reentrant" behavior.

```python
name = Observable[str]("Alice")
greeting = Observable[str]("Hello, Alice!")

# Update greeting when name changes
name.on_change(lambda value: greeting.set(f"Hello, {value}!"))

# Register callbacks
name.on_change(lambda value: print(f"Name changed to: {value}"))
greeting.on_change(lambda value: print(f"Greeting changed to: {value}"))

# Change the name
name.set("Bob")
# Prints:
# Name changed to: Bob
# Greeting changed to: Hello, Bob!
```

## Notes on Performance

While observables are powerful, they do come with some overhead. Here are some tips for optimizing performance:

- **Minimize the number of observables**: Create observables only for values that need to be tracked.
- **Use batch updates**: When making multiple changes, consider using batch operations like `extend()` for lists or `update()` for dictionaries, rather than individual operations.
- **Be careful with reentrant callbacks**: Complex chains of callbacks can lead to performance issues and hard-to-debug behavior.
- **Use `notify=False` when appropriate**: If you're making multiple changes and only care about the final state, consider using `notify=False` for intermediate changes.

```python
# Instead of this:
tasks.append("Task 1")
tasks.append("Task 2")
tasks.append("Task 3")

# Consider this:
tasks.extend(["Task 1", "Task 2", "Task 3"])
```

## Next Steps

Now that you understand how change tracking works in Observant, you might want to explore:

- [Validation](validation.md): Add validation to your models
- [Computed Properties](computed.md): Create properties that depend on other fields
- [Undo and Redo](undo.md): Implement undo/redo functionality
