# API Reference

This section provides detailed documentation for the Observant API. It covers all the classes, methods, and types available in the library.

## How to Read This Section

The API reference is organized by module, with each module containing related classes and functions. The main modules are:

- `observable`: The base `Observable` class for scalar values
- `observable_list`: The `ObservableList` class for lists
- `observable_dict`: The `ObservableDict` class for dictionaries
- `observable_proxy`: The `ObservableProxy` class for objects
- `undoable_observable`: The `UndoableObservable` class for undo/redo functionality
- `types`: Various types used throughout the library
- `interfaces`: Interfaces that define the contract for observable objects

## Core Classes

### Observable

The `Observable` class is the foundation of Observant. It wraps a single value and notifies listeners when that value changes.

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

### ObservableList

The `ObservableList` class tracks changes to a list, including additions, removals, and modifications.

```python
from observant import ObservableList

# Create an observable list
tasks = ObservableList[str](["Task 1"])

# Register a callback
tasks.on_change(lambda change: print(f"Tasks changed: {change}"))

# Add an item
tasks.append("Task 2")  # Notifies listeners
```

### ObservableDict

The `ObservableDict` class tracks changes to a dictionary, including additions, updates, and removals.

```python
from observant import ObservableDict

# Create an observable dictionary
settings = ObservableDict[str, str]({"theme": "dark"})

# Register a callback
settings.on_change(lambda change: print(f"Settings changed: {change}"))

# Add a new key
settings["language"] = "en"  # Notifies listeners
```

### ObservableProxy

The `ObservableProxy` class wraps an object (typically a dataclass) and provides observable access to its fields.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user and proxy
user = User(name="Alice", age=30)
proxy = ObservableProxy(user)

# Get observables for individual fields
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")

# Register change listeners
name_obs.on_change(lambda value: print(f"Name changed to: {value}"))

# Update fields
name_obs.set("Alicia")  # Notifies listeners
```

### UndoableObservable

The `UndoableObservable` class extends `Observable` with undo/redo functionality.

```python
from observant import UndoableObservable

# Create an undoable observable
counter = UndoableObservable[int](0)

# Make changes
counter.set(1)
counter.set(2)
counter.set(3)

# Undo changes
counter.undo()  # Reverts to 2
counter.undo()  # Reverts to 1

# Redo changes
counter.redo()  # Sets back to 2
```

## Types

### ObservableCollectionChangeType

An enum that represents the type of change that occurred in a collection:

- `ADD`: An item was added to the collection
- `REMOVE`: An item was removed from the collection
- `UPDATE`: An item was updated in the collection
- `CLEAR`: The collection was cleared

### ObservableListChange

A class that represents a change to an observable list. It contains:

- `type`: The type of change (ADD, REMOVE, CLEAR)
- `index`: The index where the change occurred (for ADD and REMOVE)
- `item`: The item that was added or removed (for single-item changes)
- `items`: The items that were added or removed (for multi-item changes)

### ObservableDictChange

A class that represents a change to an observable dictionary. It contains:

- `type`: The type of change (ADD, UPDATE, REMOVE, CLEAR)
- `key`: The key that was added, updated, or removed (for single-item changes)
- `value`: The value that was added or updated (for single-item changes)
- `items`: The items that were added, updated, or removed (for multi-item changes)

### ProxyFieldKey

A class that represents a field key in an `ObservableProxy`. It's used internally to track fields.

### UndoConfig

A class that represents the configuration for undo/redo functionality. It contains:

- `enabled`: Whether undo is enabled
- `undo_max`: Maximum number of undo steps to store
- `undo_debounce_ms`: Time in milliseconds to wait before recording a new undo step

## Interfaces

### IObservable

An interface that defines the contract for observable objects. It includes methods for getting and setting values, and registering change listeners.

### IObservableList

An interface that extends `IObservable` for lists. It includes methods for list operations like append, extend, insert, etc.

### IObservableDict

An interface that extends `IObservable` for dictionaries. It includes methods for dictionary operations like setting and getting items, updating, etc.

### IObservableProxy

An interface that defines the contract for observable proxies. It includes methods for accessing fields, validation, undo/redo, etc.

## Auto-Generated Documentation

For more detailed information about each class, method, and type, refer to the auto-generated documentation:

- [Observable](observable.md)
- [ObservableList](observable_list.md)
- [ObservableDict](observable_dict.md)
- [ObservableProxy](observable_proxy.md)
- [UndoableObservable](undoable_observable.md)
- [Types](types/index.md)
- [Interfaces](interfaces/index.md)
