# ObservableList

The `ObservableList` class is an observable collection that wraps a list and notifies listeners when items are added, removed, or modified.

## Overview

`ObservableList` is a generic class that can wrap a list of any type. It provides methods for manipulating the list and for registering callbacks that are called when the list changes.

```python
from observant import ObservableList, ObservableCollectionChangeType

# Create an observable list with initial items
tasks = ObservableList[str](["Task 1", "Task 2"])

# Register a callback to be notified when the list changes
def on_tasks_change(change):
    if change.type == ObservableCollectionChangeType.ADD:
        print(f"Added task: {change.item}")
    elif change.type == ObservableCollectionChangeType.REMOVE:
        print(f"Removed task: {change.item}")
    elif change.type == ObservableCollectionChangeType.CLEAR:
        print(f"Cleared tasks: {change.items}")

tasks.on_change(on_tasks_change)

# Add an item
tasks.append("Task 3")  # Prints: "Added task: Task 3"

# Remove an item
tasks.remove("Task 1")  # Prints: "Removed task: Task 1"

# Clear the list
tasks.clear()  # Prints: "Cleared tasks: ['Task 2', 'Task 3']"
```

## Constructor

```python
ObservableList[T](initial_items: list[T] = None)
```

Creates a new `ObservableList` with the specified initial items.

### Parameters

- `initial_items`: The initial items of the list. Default is `None` (empty list).

### Type Parameters

- `T`: The type of items in the list.

## Methods

### append

```python
append(item: T) -> None
```

Adds an item to the end of the list.

#### Parameters

- `item`: The item to add.

### extend

```python
extend(items: list[T]) -> None
```

Adds multiple items to the end of the list.

#### Parameters

- `items`: The items to add.

### insert

```python
insert(index: int, item: T) -> None
```

Inserts an item at the specified index.

#### Parameters

- `index`: The index at which to insert the item.
- `item`: The item to insert.

### remove

```python
remove(item: T) -> None
```

Removes the first occurrence of the specified item from the list.

#### Parameters

- `item`: The item to remove.

### pop

```python
pop(index: int = -1) -> T
```

Removes and returns the item at the specified index.

#### Parameters

- `index`: The index of the item to remove. Default is `-1` (the last item).

#### Returns

The removed item.

### clear

```python
clear() -> None
```

Removes all items from the list.

### sort

```python
sort(key=None, reverse=False) -> None
```

Sorts the list in place.

#### Parameters

- `key`: A function that takes an item and returns a key for sorting. Default is `None`.
- `reverse`: Whether to sort in reverse order. Default is `False`.

### reverse

```python
reverse() -> None
```

Reverses the list in place.

### on_change

```python
on_change(callback: Callable[[ObservableListChange[T]], None]) -> None
```

Registers a callback to be called when the list changes.

#### Parameters

- `callback`: A function that takes an `ObservableListChange` object as its only argument.

### get

```python
get() -> list[T]
```

Returns a copy of the list.

## Indexing and Slicing

`ObservableList` supports indexing and slicing, just like a regular list:

```python
# Create an observable list
numbers = ObservableList[int]([1, 2, 3, 4, 5])

# Get an item by index
print(numbers[0])  # Prints: 1

# Set an item by index
numbers[0] = 10
print(numbers[0])  # Prints: 10

# Delete an item by index
del numbers[0]
print(numbers.get())  # Prints: [2, 3, 4, 5]

# Get a slice
print(numbers[1:3])  # Prints: [3, 4]

# Set a slice
numbers[1:3] = [30, 40]
print(numbers.get())  # Prints: [2, 30, 40, 5]

# Delete a slice
del numbers[1:3]
print(numbers.get())  # Prints: [2, 5]
```

## ObservableListChange

When a list changes, the callback receives an `ObservableListChange` object with the following properties:

- `type`: The type of change (ADD, REMOVE, CLEAR)
- `index`: The index where the change occurred (for ADD and REMOVE)
- `item`: The item that was added or removed (for single-item changes)
- `items`: The items that were added or removed (for multi-item changes)

```python
from observant import ObservableList, ObservableCollectionChangeType

# Create an observable list
tasks = ObservableList[str](["Task 1"])

# Register a callback
def on_tasks_change(change):
    print(f"Change type: {change.type}")
    if hasattr(change, "index"):
        print(f"Index: {change.index}")
    if hasattr(change, "item"):
        print(f"Item: {change.item}")
    if hasattr(change, "items"):
        print(f"Items: {change.items}")

tasks.on_change(on_tasks_change)

# Add an item
tasks.append("Task 2")
# Prints:
# Change type: ObservableCollectionChangeType.ADD
# Index: 1
# Item: Task 2

# Remove an item
tasks.remove("Task 1")
# Prints:
# Change type: ObservableCollectionChangeType.REMOVE
# Index: 0
# Item: Task 1

# Clear the list
tasks.clear()
# Prints:
# Change type: ObservableCollectionChangeType.CLEAR
# Items: ['Task 2']
```

## Implementation Details

The `ObservableList` class implements the `IObservableList` interface, which extends the `IObservable` interface. This ensures that `ObservableList` has all the functionality of `Observable` plus list-specific operations.

For more details on the implementation, see the [source code](https://github.com/MrowrLib/observant.py/blob/main/observant/observable_list.py).

## See Also

- [Observable](observable.md): The base observable class for scalar values.
- [ObservableDict](observable_dict.md): An observable dictionary that notifies listeners when items are added, updated, or removed.
- ObservableCollectionChangeType: An enum that represents the type of change that occurred in a collection.
- ObservableListChange: A class that represents a change to an observable list.
- IObservableList: The interface that defines the contract for observable lists.
