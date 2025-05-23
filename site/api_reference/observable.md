# Observable

The `Observable` class is the foundation of Observant. It wraps a single value and notifies listeners when that value changes.

## Overview

`Observable` is a generic class that can wrap any type of value. It provides methods for getting and setting the value, and for registering callbacks that are called when the value changes.

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

## Constructor

```python
Observable[T](initial_value: T)
```

Creates a new `Observable` with the specified initial value.

### Parameters

- `initial_value`: The initial value of the observable.

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

## Example

```python
from observant import Observable

# Create an observable string
name = Observable[str]("Alice")

# Register a callback
name.on_change(lambda value: print(f"Name changed to: {value}"))

# Change the value
name.set("Bob")  # Prints: "Name changed to: Bob"

# Get the current value
current_name = name.get()  # Returns: "Bob"

# Change the value without notifying listeners
name.set("Charlie", notify=False)

# The value is updated, but no callback is triggered
print(name.get())  # Prints: "Charlie"
```

## Multiple Callbacks

You can register multiple callbacks for the same observable:

```python
counter = Observable[int](0)

# Register multiple callbacks
counter.on_change(lambda value: print(f"Callback 1: {value}"))
counter.on_change(lambda value: print(f"Callback 2: {value}"))

# Change the value
counter.set(1)
# Prints:
# Callback 1: 1
# Callback 2: 1
```

## Implementation Details

The `Observable` class implements the `IObservable` interface, which defines the contract for observable objects. This interface is used throughout Observant to ensure consistent behavior across different types of observables.

For more details on the implementation, see the [source code](https://github.com/MrowrLib/observant.py/blob/main/observant/observable.py).

## See Also

- [ObservableList](observable_list.md): An observable list that notifies listeners when items are added, removed, or modified.
- [ObservableDict](observable_dict.md): An observable dictionary that notifies listeners when items are added, updated, or removed.
- [UndoableObservable](undoable_observable.md): An observable that supports undo and redo operations.
- IObservable: The interface that defines the contract for observable objects.
