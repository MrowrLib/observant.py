# Types

This section documents the various types used throughout the Observant library. These types define the structure of data and events in the library.

## ObservableCollectionChangeType

An enum that represents the type of change that occurred in a collection:

- `ADD`: An item was added to the collection
- `REMOVE`: An item was removed from the collection
- `UPDATE`: An item was updated in the collection
- `CLEAR`: The collection was cleared

```python
from observant import ObservableCollectionChangeType

# Example usage
if change.type == ObservableCollectionChangeType.ADD:
    print("Item added")
elif change.type == ObservableCollectionChangeType.REMOVE:
    print("Item removed")
elif change.type == ObservableCollectionChangeType.UPDATE:
    print("Item updated")
elif change.type == ObservableCollectionChangeType.CLEAR:
    print("Collection cleared")
```

## ObservableListChange

A class that represents a change to an observable list. It contains:

- `type`: The type of change (ADD, REMOVE, CLEAR)
- `index`: The index where the change occurred (for ADD and REMOVE)
- `item`: The item that was added or removed (for single-item changes)
- `items`: The items that were added or removed (for multi-item changes)

```python
from observant import ObservableList, ObservableListChange

# Create an observable list
tasks = ObservableList[str](["Task 1"])

# Register a callback
def on_tasks_change(change: ObservableListChange[str]):
    print(f"Change type: {change.type}")
    if hasattr(change, "index"):
        print(f"Index: {change.index}")
    if hasattr(change, "item"):
        print(f"Item: {change.item}")
    if hasattr(change, "items"):
        print(f"Items: {change.items}")

tasks.on_change(on_tasks_change)
```

## ObservableDictChange

A class that represents a change to an observable dictionary. It contains:

- `type`: The type of change (ADD, UPDATE, REMOVE, CLEAR)
- `key`: The key that was added, updated, or removed (for single-item changes)
- `value`: The value that was added or updated (for single-item changes)
- `items`: The items that were added, updated, or removed (for multi-item changes)

```python
from observant import ObservableDict, ObservableDictChange

# Create an observable dictionary
settings = ObservableDict[str, str]({"theme": "dark"})

# Register a callback
def on_settings_change(change: ObservableDictChange[str, str]):
    print(f"Change type: {change.type}")
    if hasattr(change, "key"):
        print(f"Key: {change.key}")
    if hasattr(change, "value"):
        print(f"Value: {change.value}")
    if hasattr(change, "items"):
        print(f"Items: {change.items}")

settings.on_change(on_settings_change)
```

## ProxyFieldKey

A class that represents a field key in an `ObservableProxy`. It's used internally to track fields.

```python
from observant.types import ProxyFieldKey

# This is typically used internally by ObservableProxy
field_key = ProxyFieldKey("name")
```

## UndoConfig

A class that represents the configuration for undo/redo functionality. It contains:

- `enabled`: Whether undo is enabled
- `undo_max`: Maximum number of undo steps to store
- `undo_debounce_ms`: Time in milliseconds to wait before recording a new undo step

```python
from observant.types import UndoConfig

# Create an undo configuration
config = UndoConfig(
    enabled=True,
    undo_max=10,
    undo_debounce_ms=500
)

# This is typically used internally by ObservableProxy
proxy.set_undo_config("name", enabled=config.enabled, undo_max=config.undo_max, undo_debounce_ms=config.undo_debounce_ms)
```

## Auto-Generated Documentation

For more detailed information about each type, refer to the auto-generated documentation:

- ObservableCollectionChangeType
- ObservableListChange
- ObservableDictChange
- ProxyFieldKey
- UndoConfig
