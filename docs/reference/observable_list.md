# ObservableList {#ref-observable-list}

The `ObservableList` class provides an observable wrapper around a Python list. It notifies listeners when items are added, removed, or the list is cleared.

## Basic Usage

```python
from observant import ObservableList

# Create an observable list with initial values
fruits = ObservableList(["apple", "banana"])

# Register a callback to be notified when the list changes
fruits.on_change(lambda change: print(f"List changed: {change.type.name} at index {change.index}"))

# Modify the list
fruits.append("cherry")  # Prints: List changed: ADD at index 2
fruits.pop(0)  # Prints: List changed: REMOVE at index 0
fruits.clear()  # Prints: List changed: CLEAR at index None
```

## Type Safety

`ObservableList` is generic over the type of items it contains:

```python
from observant import ObservableList

# Type-safe observable list
names: ObservableList[str] = ObservableList(["Ada", "Grace"])
numbers: ObservableList[int] = ObservableList([1, 2, 3])

# The IDE and type checker will warn about incorrect types
names.append(42)  # Type error: Expected str, got int
```

## Change Notifications

When the list changes, the callback receives a `ListChange` object with the following properties:

- `type`: The type of change (ADD, REMOVE, CLEAR)
- `index`: The index where the change occurred (None for CLEAR)
- `item`: The item that was added or removed (None for CLEAR)
- `items`: For CLEAR operations, the list of items that were cleared

```python
from observant import ObservableList
from observant.types.collection_change_type import ObservableCollectionChangeType

fruits = ObservableList(["apple", "banana"])

def on_change(change):
    if change.type == ObservableCollectionChangeType.ADD:
        print(f"Added {change.item} at index {change.index}")
    elif change.type == ObservableCollectionChangeType.REMOVE:
        print(f"Removed {change.item} from index {change.index}")
    elif change.type == ObservableCollectionChangeType.CLEAR:
        print(f"Cleared {len(change.items)} items: {change.items}")

fruits.on_change(on_change)

fruits.append("cherry")  # Prints: Added cherry at index 2
fruits.pop(0)  # Prints: Removed apple from index 0
fruits.clear()  # Prints: Cleared 2 items: ['banana', 'cherry']
```

## API Reference

### Constructor

```python
ObservableList(initial_items: list[T] = None, copy: bool = True)
```

- `initial_items`: The initial list of items (default: empty list)
- `copy`: Whether to copy the initial items (default: True)

### List Operations

`ObservableList` supports all standard list operations:

```python
fruits = ObservableList(["apple", "banana"])

# Append an item
fruits.append("cherry")

# Insert an item at a specific index
fruits.insert(1, "orange")

# Remove an item
fruits.remove("banana")

# Pop an item
item = fruits.pop()  # Removes and returns the last item
item = fruits.pop(0)  # Removes and returns the item at index 0

# Clear the list
fruits.clear()

# Get the length
length = len(fruits)

# Check if an item is in the list
if "apple" in fruits:
    print("Found apple!")

# Access items by index
first = fruits[0]
fruits[1] = "new value"

# Slice the list
subset = fruits[1:3]

# Iterate over items
for fruit in fruits:
    print(fruit)
```

### Additional Methods

#### `on_change()`

```python
def on_change(self, callback: Callable[[ListChange[T]], None]) -> None
```

Registers a callback to be notified when the list changes.

- `callback`: A function that takes a `ListChange` object as its argument

#### `copy()`

```python
def copy(self) -> list[T]
```

Returns a copy of the underlying list.

#### `extend()`

```python
def extend(self, items: Iterable[T]) -> None
```

Extends the list with items from an iterable.

## Examples

### Filtering and Sorting

```python
from observant import ObservableList

# Create a list of users
users = ObservableList([
    {"name": "Alice", "age": 32},
    {"name": "Bob", "age": 28},
    {"name": "Charlie", "age": 45}
])

# Create filtered views
adults = ObservableList()
seniors = ObservableList()

# Update filtered views when the main list changes
def update_filtered_views():
    adults.clear()
    seniors.clear()
    
    for user in users:
        if user["age"] >= 18:
            adults.append(user)
        if user["age"] >= 65:
            seniors.append(user)

# Initial population
update_filtered_views()

# Register for changes
users.on_change(lambda _: update_filtered_views())

# Add a new user
users.append({"name": "Diana", "age": 67})
# adults now contains all 4 users
# seniors now contains Diana
```

### Undo/Redo Support

```python
from observant import ObservableList
from observant.types.collection_change_type import ObservableCollectionChangeType
from typing import List, Any, Callable

class UndoableList:
    def __init__(self, initial_items=None):
        self.list = ObservableList(initial_items)
        self.undo_stack: List[Callable[[], None]] = []
        self.redo_stack: List[Callable[[], None]] = []
        
        # Register for changes to build undo/redo stacks
        self.list.on_change(self._on_change)
    
    def _on_change(self, change):
        # Clear redo stack when a new change is made
        self.redo_stack.clear()
        
        if change.type == ObservableCollectionChangeType.ADD:
            # For adds, the undo action is to remove the item
            def undo():
                if change.index is not None:
                    self.list.pop(change.index)
            self.undo_stack.append(undo)
            
        elif change.type == ObservableCollectionChangeType.REMOVE:
            # For removes, the undo action is to add the item back
            def undo():
                if change.index is not None:
                    self.list.insert(change.index, change.item)
            self.undo_stack.append(undo)
            
        elif change.type == ObservableCollectionChangeType.CLEAR:
            # For clears, the undo action is to restore all items
            items = change.items
            def undo():
                self.list.extend(items)
            self.undo_stack.append(undo)
    
    def undo(self):
        if self.undo_stack:
            undo_action = self.undo_stack.pop()
            # TODO: Store the current state for redo
            undo_action()
    
    def redo(self):
        if self.redo_stack:
            redo_action = self.redo_stack.pop()
            redo_action()

# Usage
todo_list = UndoableList(["Buy groceries", "Clean house"])
todo_list.list.append("Write code")  # Adds to undo stack
todo_list.undo()  # Removes "Write code"
```

## Implementation Details

The `ObservableList` class implements the `IObservableList` interface, which is defined in `observant.interfaces.list`. This interface ensures that all observable list types in the library have a consistent API.

For more advanced use cases, consider using `ObservableProxy` which can automatically create observable lists for list fields in a data object.

## API Documentation

::: observant.observable_list.ObservableList
