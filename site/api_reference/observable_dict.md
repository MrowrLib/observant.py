# ObservableDict

The `ObservableDict` class is an observable collection that wraps a dictionary and notifies listeners when items are added, updated, or removed.

## Overview

`ObservableDict` is a generic class that can wrap a dictionary with keys and values of any type. It provides methods for manipulating the dictionary and for registering callbacks that are called when the dictionary changes.

```python
from observant import ObservableDict, ObservableCollectionChangeType

# Create an observable dictionary with initial items
settings = ObservableDict[str, str]({"theme": "dark", "language": "en"})

# Register a callback to be notified when the dictionary changes
def on_settings_change(change):
    if change.type == ObservableCollectionChangeType.ADD:
        print(f"Added setting: {change.key} = {change.value}")
    elif change.type == ObservableCollectionChangeType.UPDATE:
        print(f"Updated setting: {change.key} = {change.value}")
    elif change.type == ObservableCollectionChangeType.REMOVE:
        print(f"Removed setting: {change.key}")
    elif change.type == ObservableCollectionChangeType.CLEAR:
        print(f"Cleared settings: {change.items}")

settings.on_change(on_settings_change)

# Add a new key
settings["font"] = "Arial"  # Prints: "Added setting: font = Arial"

# Update an existing key
settings["theme"] = "light"  # Prints: "Updated setting: theme = light"

# Remove a key
del settings["language"]  # Prints: "Removed setting: language"

# Clear the dictionary
settings.clear()  # Prints: "Cleared settings: {'theme': 'light', 'font': 'Arial'}"
```

## Constructor

```python
ObservableDict[K, V](initial_items: dict[K, V] = None)
```

Creates a new `ObservableDict` with the specified initial items.

### Parameters

- `initial_items`: The initial items of the dictionary. Default is `None` (empty dictionary).

### Type Parameters

- `K`: The type of keys in the dictionary.
- `V`: The type of values in the dictionary.

## Methods

### __getitem__

```python
__getitem__(key: K) -> V
```

Gets the value for the specified key.

#### Parameters

- `key`: The key to get the value for.

#### Returns

The value for the specified key.

#### Raises

- `KeyError`: If the key is not found in the dictionary.

### __setitem__

```python
__setitem__(key: K, value: V) -> None
```

Sets the value for the specified key.

#### Parameters

- `key`: The key to set the value for.
- `value`: The value to set.

### __delitem__

```python
__delitem__(key: K) -> None
```

Removes the specified key and its value from the dictionary.

#### Parameters

- `key`: The key to remove.

#### Raises

- `KeyError`: If the key is not found in the dictionary.

### get

```python
get(key: K, default: V = None) -> V
```

Gets the value for the specified key, or a default value if the key is not found.

#### Parameters

- `key`: The key to get the value for.
- `default`: The default value to return if the key is not found. Default is `None`.

#### Returns

The value for the specified key, or the default value if the key is not found.

### setdefault

```python
setdefault(key: K, default: V = None) -> V
```

Gets the value for the specified key, or sets it to a default value if the key is not found.

#### Parameters

- `key`: The key to get or set the value for.
- `default`: The default value to set if the key is not found. Default is `None`.

#### Returns

The value for the specified key, or the default value if the key was not found.

### pop

```python
pop(key: K, default: V = None) -> V
```

Removes the specified key and returns its value, or a default value if the key is not found.

#### Parameters

- `key`: The key to remove.
- `default`: The default value to return if the key is not found. Default is `None`.

#### Returns

The value for the specified key, or the default value if the key was not found.

#### Raises

- `KeyError`: If the key is not found in the dictionary and no default value is provided.

### popitem

```python
popitem() -> tuple[K, V]
```

Removes and returns an arbitrary key-value pair from the dictionary.

#### Returns

A tuple containing the key and value of the removed item.

#### Raises

- `KeyError`: If the dictionary is empty.

### clear

```python
clear() -> None
```

Removes all items from the dictionary.

### update

```python
update(other: dict[K, V]) -> None
```

Updates the dictionary with key-value pairs from another dictionary.

#### Parameters

- `other`: The dictionary to update from.

### on_change

```python
on_change(callback: Callable[[ObservableDictChange[K, V]], None]) -> None
```

Registers a callback to be called when the dictionary changes.

#### Parameters

- `callback`: A function that takes an `ObservableDictChange` object as its only argument.

### to_dict

```python
to_dict() -> dict[K, V]
```

Returns a copy of the dictionary.

## ObservableDictChange

When a dictionary changes, the callback receives an `ObservableDictChange` object with the following properties:

- `type`: The type of change (ADD, UPDATE, REMOVE, CLEAR)
- `key`: The key that was added, updated, or removed (for single-item changes)
- `value`: The value that was added or updated (for single-item changes)
- `items`: The items that were added, updated, or removed (for multi-item changes)

```python
from observant import ObservableDict, ObservableCollectionChangeType

# Create an observable dictionary
settings = ObservableDict[str, str]({"theme": "dark"})

# Register a callback
def on_settings_change(change):
    print(f"Change type: {change.type}")
    if hasattr(change, "key"):
        print(f"Key: {change.key}")
    if hasattr(change, "value"):
        print(f"Value: {change.value}")
    if hasattr(change, "items"):
        print(f"Items: {change.items}")

settings.on_change(on_settings_change)

# Add a new key
settings["language"] = "en"
# Prints:
# Change type: ObservableCollectionChangeType.ADD
# Key: language
# Value: en

# Update an existing key
settings["theme"] = "light"
# Prints:
# Change type: ObservableCollectionChangeType.UPDATE
# Key: theme
# Value: light

# Remove a key
del settings["theme"]
# Prints:
# Change type: ObservableCollectionChangeType.REMOVE
# Key: theme

# Clear the dictionary
settings.clear()
# Prints:
# Change type: ObservableCollectionChangeType.CLEAR
# Items: {'language': 'en'}
```

## Implementation Details

The `ObservableDict` class implements the `IObservableDict` interface, which extends the `IObservable` interface. This ensures that `ObservableDict` has all the functionality of `Observable` plus dictionary-specific operations.

For more details on the implementation, see the [source code](https://github.com/MrowrLib/observant.py/blob/main/observant/observable_dict.py).

## See Also

- [Observable](observable.md): The base observable class for scalar values.
- [ObservableList](observable_list.md): An observable list that notifies listeners when items are added, removed, or modified.
- ObservableCollectionChangeType: An enum that represents the type of change that occurred in a collection.
- ObservableDictChange: A class that represents a change to an observable dictionary.
- IObservableDict: The interface that defines the contract for observable dictionaries.
