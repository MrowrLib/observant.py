# Sync vs Non-Sync

Observant provides two modes of operation for `ObservableProxy`: sync mode and non-sync mode. This page explains the differences between these modes and when to use each.

## Overview

When you create an `ObservableProxy`, you can specify whether changes to the proxy should be immediately synchronized with the underlying model:

- `sync=True`: Changes to the proxy are immediately applied to the underlying model
- `sync=False`: Changes to the proxy are only applied to the underlying model when you call `save_to()`

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user
user = User(name="Alice", age=30)

# Create a proxy with sync=True
proxy_sync = ObservableProxy(user, sync=True)

# Create a proxy with sync=False
proxy_non_sync = ObservableProxy(user, sync=False)
```

## sync=True vs sync=False

### sync=True

When `sync=True`, any changes you make to the proxy are immediately applied to the underlying model:

```python
# Create a user and proxy with sync=True
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=True)

# Change a field
proxy.observable(str, "name").set("Bob")

# The change is immediately applied to the user object
print(user.name)  # "Bob"
```

This mode is useful when:

- You want to keep the model and proxy in sync at all times
- You're working with a model that needs to reflect changes immediately
- You don't need to validate or review changes before applying them

### sync=False

When `sync=False`, changes to the proxy are not automatically applied to the underlying model. You need to explicitly call `save_to()` to apply the changes:

```python
# Create a user and proxy with sync=False
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=False)

# Change a field
proxy.observable(str, "name").set("Bob")

# The change is not applied to the user object yet
print(user.name)  # "Alice"

# Apply the changes
proxy.save_to(user)

# Now the change is applied
print(user.name)  # "Bob"
```

This mode is useful when:

- You want to validate changes before applying them
- You need to support undo/redo functionality
- You want to track dirty state
- You need to review or confirm changes before saving

## When to Use Each

### Use sync=True When

- You need immediate synchronization between the proxy and the model
- You're working with a model that needs to reflect changes in real-time
- You don't need undo/redo functionality
- You don't need to track dirty state

### Use sync=False When

- You need to validate changes before applying them
- You want to support undo/redo functionality
- You want to track dirty state
- You need to review or confirm changes before saving
- You want to optimize performance by batching updates

## save_to() and load_dict()

When using `sync=False`, you need to explicitly apply changes to the model using `save_to()`:

```python
# Create a user and proxy with sync=False
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=False)

# Make changes
proxy.observable(str, "name").set("Bob")
proxy.observable(int, "age").set(31)

# Validate changes
if proxy.is_valid():
    # Apply changes
    proxy.save_to(user)
else:
    # Show validation errors
    print("Validation errors:", proxy.validation_errors())
```

You can also load data into the proxy from a dictionary using `load_dict()`:

```python
# Load data from a dictionary
proxy.load_dict({
    "name": "Charlie",
    "age": 32
})

# The changes are not applied to the user object yet
print(user.name)  # "Bob" (or "Alice" if save_to() wasn't called)

# Apply the changes
proxy.save_to(user)

# Now the changes are applied
print(user.name)  # "Charlie"
```

## update() vs load_dict()

Observant provides two methods for updating multiple fields at once: `update()` and `load_dict()`. The main difference is that `update()` only updates the fields that are provided, while `load_dict()` updates all fields in the dictionary.

### update()

The `update()` method updates only the fields that are provided in the dictionary:

```python
# Create a user and proxy
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=False)

# Update specific fields
proxy.update({
    "name": "Bob"
})

# Only the specified fields are updated
print(proxy.observable(str, "name").get())  # "Bob"
print(proxy.observable(int, "age").get())  # 30 (unchanged)
```

### load_dict()

The `load_dict()` method updates all fields in the dictionary, and can optionally reset fields that are not in the dictionary:

```python
# Create a user and proxy
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=False)

# Load a dictionary
proxy.load_dict({
    "name": "Bob"
}, reset_missing=False)

# Only the specified fields are updated
print(proxy.observable(str, "name").get())  # "Bob"
print(proxy.observable(int, "age").get())  # 30 (unchanged)

# Load a dictionary with reset_missing=True
proxy.load_dict({
    "name": "Charlie"
}, reset_missing=True)

# Fields not in the dictionary are reset to their default values
print(proxy.observable(str, "name").get())  # "Charlie"
print(proxy.observable(int, "age").get())  # 0 (reset to default)
```

## Performance Considerations

The choice between `sync=True` and `sync=False` can affect performance:

- `sync=True` may be slower if you're making many changes, since each change triggers an update to the model
- `sync=False` may be faster for bulk updates, since you can batch changes and apply them all at once

```python
# sync=True: Each change triggers an update
proxy_sync = ObservableProxy(user, sync=True)
for i in range(1000):
    proxy_sync.observable(int, "age").set(i)  # 1000 updates to the model

# sync=False: Changes are batched
proxy_non_sync = ObservableProxy(user, sync=False)
for i in range(1000):
    proxy_non_sync.observable(int, "age").set(i)  # No updates to the model yet
proxy_non_sync.save_to(user)  # 1 update to the model
```

## Sync and Undo

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

## Next Steps

Now that you understand the difference between sync and non-sync modes in Observant, you might want to explore:

- [Saving and Loading](save_load.md): Learn more about saving changes and loading data
- [Dirty Tracking](dirty.md): Track unsaved changes
- [Undo and Redo](undo.md): Implement undo/redo functionality

[← Back to Overview](../index.md)
