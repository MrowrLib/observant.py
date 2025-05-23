# UndoableObservable

The `UndoableObservable` class extends `Observable` with undo and redo functionality. It allows you to track changes to a value and revert them if needed.

## Overview

`UndoableObservable` is a generic class that can wrap any type of value. It provides all the functionality of `Observable`, plus methods for undoing and redoing changes.

```python
from observant import UndoableObservable

# Create an undoable observable with an initial value
counter = UndoableObservable[int](0)

# Register a callback to be notified when the value changes
counter.on_change(lambda value: print(f"Counter changed to: {value}"))

# Make changes
counter.set(1)  # Prints: "Counter changed to: 1"
counter.set(2)  # Prints: "Counter changed to: 2"
counter.set(3)  # Prints: "Counter changed to: 3"

# Undo changes
counter.undo()  # Prints: "Counter changed to: 2"
counter.undo()  # Prints: "Counter changed to: 1"

# Redo changes
counter.redo()  # Prints: "Counter changed to: 2"
```

## Constructor

```python
UndoableObservable[T](initial_value: T, undo_max: int = None, undo_debounce_ms: int = None)
```

Creates a new `UndoableObservable` with the specified initial value.

### Parameters

- `initial_value`: The initial value of the observable.
- `undo_max`: Maximum number of undo steps to store. Default is `None` (unlimited).
- `undo_debounce_ms`: Time in milliseconds to wait before recording a new undo step. Default is `None` (no debounce).

### Type Parameters

- `T`: The type of the value wrapped by the observable.

## Methods

### get

```python
get() -> T
```

Returns the current value of the observable.

### set

```python
set(value: T, notify: bool = True) -> None
```

Sets the value of the observable and notifies listeners if `notify` is `True`.

#### Parameters

- `value`: The new value to set.
- `notify`: Whether to notify listeners of the change. Default is `True`.

### on_change

```python
on_change(callback: Callable[[T], None]) -> None
```

Registers a callback to be called when the value changes.

#### Parameters

- `callback`: A function that takes the new value as its only argument.

### undo

```python
undo() -> None
```

Undoes the last change to the value.

### redo

```python
redo() -> None
```

Redoes the last undone change to the value.

### can_undo

```python
can_undo() -> bool
```

Returns whether undo is available.

### can_redo

```python
can_redo() -> bool
```

Returns whether redo is available.

## Example

```python
from observant import UndoableObservable

# Create an undoable observable string
name = UndoableObservable[str]("Alice")

# Register a callback
name.on_change(lambda value: print(f"Name changed to: {value}"))

# Make changes
name.set("Bob")    # Prints: "Name changed to: Bob"
name.set("Charlie")  # Prints: "Name changed to: Charlie"
name.set("Dave")   # Prints: "Name changed to: Dave"

# Check undo/redo availability
print(name.can_undo())  # True
print(name.can_redo())  # False

# Undo changes
name.undo()  # Prints: "Name changed to: Charlie"
name.undo()  # Prints: "Name changed to: Bob"

# Check undo/redo availability again
print(name.can_undo())  # True
print(name.can_redo())  # True

# Redo changes
name.redo()  # Prints: "Name changed to: Charlie"

# Make a new change
name.set("Eve")  # Prints: "Name changed to: Eve"

# The redo history is cleared
print(name.can_redo())  # False
```

## Undo Configuration

The `UndoableObservable` class provides two configuration options for undo behavior:

### undo_max

The `undo_max` parameter limits the number of undo steps that are stored. This prevents the undo stack from growing too large and consuming too much memory.

```python
# Limit to 10 undo steps
counter = UndoableObservable[int](0, undo_max=10)
```

When the undo stack reaches the maximum size, the oldest undo step is discarded when a new one is added.

### undo_debounce_ms

The `undo_debounce_ms` parameter adds debounce behavior to the undo system. If multiple changes are made within the debounce time, only the last change is recorded as an undo step.

```python
# Debounce undo steps by 500ms
name = UndoableObservable[str]("", undo_debounce_ms=500)

# These rapid changes will be combined into a single undo step
name.set("A")
name.set("Al")
name.set("Ali")
name.set("Alic")
name.set("Alice")

# Only one undo step is created
name.undo()  # Reverts directly to the original value
```

This is useful for fields that change rapidly, such as text fields during typing.

## Implementation Details

The `UndoableObservable` class extends the `Observable` class and implements the `IObservable` interface. It maintains an undo stack and a redo stack to track changes to the value.

For more details on the implementation, see the [source code](https://github.com/MrowrLib/observant.py/blob/main/observant/undoable_observable.py).

## See Also

- [Observable](observable.md): The base observable class for scalar values.
- [ObservableProxy](observable_proxy.md): An observable proxy that provides undo/redo functionality for object fields.
- UndoConfig: A class that represents the configuration for undo/redo functionality.
