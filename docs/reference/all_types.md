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

## Specialized Types

### UndoableObservable

The `UndoableObservable` class extends `Observable` with undo/redo functionality. It keeps track of value changes and allows you to undo and redo them.

```python
from observant import UndoableObservable

# Create an undoable observable with an initial value
counter = UndoableObservable(0)

# Register a callback to be notified when the value changes
counter.on_change(lambda value: print(f"Counter changed to {value}"))

# Change the value
counter.set(1)  # Prints: Counter changed to 1
counter.set(2)  # Prints: Counter changed to 2

# Undo the last change
counter.undo()  # Prints: Counter changed to 1

# Redo the undone change
counter.redo()  # Prints: Counter changed to 2
```

#### Constructor

```python
UndoableObservable(
    initial_value: T,
    on_change_enabled: bool = True,
    undo_max: int | None = None,
    undo_debounce_ms: int | None = None,
)
```

- `initial_value`: The initial value to store
- `on_change_enabled`: Whether to enable change notifications immediately
- `undo_max`: Maximum number of undo steps to store (None means unlimited)
- `undo_debounce_ms`: Time window in milliseconds to group changes (None means no debouncing)

#### Undo/Redo Methods

##### `undo()`

```python
def undo(self) -> None
```

Undoes the most recent change.

##### `redo()`

```python
def redo(self) -> None
```

Redoes the most recently undone change.

##### `can_undo()`

```python
def can_undo(self) -> bool
```

Checks if there are changes that can be undone.

##### `can_redo()`

```python
def can_redo(self) -> bool
```

Checks if there are changes that can be redone.

#### Example: Text Editor

```python
from observant import UndoableObservable

class TextEditor:
    def __init__(self, initial_text: str = ""):
        self.text = UndoableObservable(initial_text, undo_debounce_ms=500)
        self.text.on_change(self._on_text_changed)
    
    def _on_text_changed(self, text):
        print(f"Text changed: {text}")
        # Update UI here
    
    def set_text(self, text: str):
        self.text.set(text)
    
    def undo(self):
        if self.text.can_undo():
            self.text.undo()
            return True
        return False
    
    def redo(self):
        if self.text.can_redo():
            self.text.redo()
            return True
        return False

# Usage
editor = TextEditor("Hello, world!")
editor.set_text("Hello, Python!")  # Prints: Text changed: Hello, Python!
editor.set_text("Hello, Observant!")  # Prints: Text changed: Hello, Observant!
editor.undo()  # Prints: Text changed: Hello, Python!
editor.redo()  # Prints: Text changed: Hello, Observant!
```

### Change Types

Observant.py provides several types to represent changes to collections:

#### ObservableCollectionChangeType

An enum that represents the type of change to a collection:

```python
from observant.types.collection_change_type import ObservableCollectionChangeType

# Available change types
ADD = ObservableCollectionChangeType.ADD  # An item was added
REMOVE = ObservableCollectionChangeType.REMOVE  # An item was removed
CLEAR = ObservableCollectionChangeType.CLEAR  # The collection was cleared
SET = ObservableCollectionChangeType.SET  # A dictionary entry was set
```

#### ObservableListChange

A class that represents a change to an observable list:

```python
from observant.types.list_change import ObservableListChange

# Properties
change.type  # The type of change (ADD, REMOVE, CLEAR)
change.index  # The index where the change occurred (None for CLEAR)
change.item  # The item that was added or removed (None for CLEAR)
change.items  # For CLEAR operations, the list of items that were cleared
```

#### ObservableDictChange

A class that represents a change to an observable dictionary:

```python
from observant.types.dict_change import ObservableDictChange

# Properties
change.type  # The type of change (SET, REMOVE, CLEAR)
change.key  # The key that was changed (None for CLEAR)
change.value  # The new value for SET operations, or the removed value for REMOVE operations
change.old_value  # The previous value for SET operations (if the key existed)
change.old_items  # For CLEAR operations, the dictionary of items that were cleared
```

### Interfaces

Observant.py provides several interfaces that define the contract for observable types:

#### IObservable

The base interface for all observable types:

```python
from observant.interfaces.observable import IObservable

# Methods
observable.get()  # Get the current value
observable.set(value)  # Set a new value
observable.on_change(callback)  # Register a callback for changes
observable.enable()  # Enable change notifications
observable.disable()  # Disable change notifications
```

#### IObservableList

The interface for observable lists:

```python
from observant.interfaces.list import IObservableList

# Methods (in addition to IObservable methods)
observable_list.append(item)  # Append an item
observable_list.insert(index, item)  # Insert an item at a specific index
observable_list.pop(index)  # Remove and return an item at a specific index
observable_list.remove(item)  # Remove a specific item
observable_list.clear()  # Clear the list
```

#### IObservableDict

The interface for observable dictionaries:

```python
from observant.interfaces.dict import IObservableDict

# Methods (in addition to IObservable methods)
observable_dict[key] = value  # Set a value
value = observable_dict[key]  # Get a value
del observable_dict[key]  # Remove a key
observable_dict.clear()  # Clear the dictionary
observable_dict.update(other)  # Update with key-value pairs from another dictionary
```

#### IObservableProxy

The interface for observable proxies:

```python
from observant.interfaces.proxy import IObservableProxy

# Methods
proxy.observable(type, attr)  # Get an observable for a field
proxy.observable_list(item_type, attr)  # Get an observable list for a field
proxy.observable_dict(key_value_types, attr)  # Get an observable dictionary for a field
proxy.computed(type, attr)  # Get an observable for a computed field
proxy.save_to(obj)  # Save changes to an object
proxy.reset()  # Reset changes
```

## API Documentation

For detailed API documentation, see the [API Reference](../api_reference.md).
