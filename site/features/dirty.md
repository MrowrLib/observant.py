# Dirty Tracking

Observant provides a dirty tracking system that allows you to track which fields have been modified since the last save or reset. This page explains how dirty tracking works in Observant.

## Overview

Dirty tracking is useful for:

- Knowing which fields have been modified
- Enabling/disabling save buttons based on whether there are unsaved changes
- Prompting users to save changes before navigating away
- Optimizing save operations by only saving modified fields

Key features of dirty tracking in Observant:

- Field-level dirty tracking
- Observable dirty state
- Integration with undo/redo
- Exclusion of computed fields

## What is Dirty?

In Observant, a field is considered "dirty" if its value has been changed since the last save or reset. The dirty state is tracked at the field level, so you can see exactly which fields have been modified.

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

# Initially, no fields are dirty
print(proxy.is_dirty())         # False
print(proxy.dirty_fields())     # set()

# Modify a field
proxy.observable(str, "name").set("Bob")

# Now the field is dirty
print(proxy.is_dirty())         # True
print(proxy.dirty_fields())     # {"name"}

# Modify another field
proxy.observable(int, "age").set(31)

# Now both fields are dirty
print(proxy.is_dirty())         # True
print(proxy.dirty_fields())     # {"name", "age"}
```

## Tracking Dirty Fields

Observant provides two methods for tracking dirty fields:

- `is_dirty()`: Returns an observable indicating whether any field is dirty
- `dirty_fields()`: Returns a set of dirty field names

### is_dirty()

The `is_dirty()` method returns an observable boolean indicating whether any field is dirty. It can be used directly as a bool (via `__bool__`) or observed for changes:

```python
# Use directly as a bool
if proxy.is_dirty():
    print("Has unsaved changes")

# Or get the value explicitly
print(proxy.is_dirty().get())  # True or False

# Listen for changes to the dirty state
proxy.is_dirty().on_change(lambda dirty: print(f"Dirty: {dirty}"))
```

### dirty_fields()

The `dirty_fields()` method returns a set of dirty field names:

```python
# Get the set of dirty fields
dirty = proxy.dirty_fields()
print(dirty)  # {"name", "age"}

# Check if a specific field is dirty
if "name" in proxy.dirty_fields():
    print("Name has been modified")
```

## reset_dirty()

The `reset_dirty()` method resets the dirty state for all fields:

```python
# Reset dirty state for all fields
proxy.reset_dirty()
```

After resetting the dirty state, the current values become the new baseline for dirty tracking. Any subsequent changes will mark the fields as dirty again.

```python
# Initially, no fields are dirty
if not proxy.is_dirty():
    print("Clean")

# Modify a field
proxy.observable(str, "name").set("Bob")

# Now the field is dirty
if proxy.is_dirty():
    print("Has changes")

# Reset dirty state
proxy.reset_dirty()

# Now no fields are dirty again
if not proxy.is_dirty():
    print("Clean again")
```

## Interaction with Undo

The dirty tracking system integrates with the undo system. When you undo or redo a change, the dirty state is updated accordingly:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user and proxy
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, undo=True)

# Initially, no fields are dirty
print(proxy.is_dirty())         # False
print(proxy.dirty_fields())     # set()

# Modify a field
proxy.observable(str, "name").set("Bob")

# Now the field is dirty
print(proxy.is_dirty())         # True
print(proxy.dirty_fields())     # {"name"}

# Undo the change
proxy.undo("name")

# Still dirty (undo doesn't clear dirty state)
print(proxy.is_dirty())         # True
```

!!! note
    Undoing a change does not automatically clear the dirty state. The field remains marked as dirty because it was modified during the session. Use `reset_dirty()` to explicitly mark fields as clean.

## Computed Fields and Dirty State

Computed fields are not included in dirty tracking, since their values are derived from other fields. When a dependency of a computed field changes, the computed field itself is not marked as dirty.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    first_name: str
    last_name: str

# Create a user and proxy
user = User(first_name="Alice", last_name="Smith")
proxy = ObservableProxy(user)

# Register a computed property for full name
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
    dependencies=["first_name", "last_name"]
)

# Initially, no fields are dirty
print(proxy.is_dirty())         # False
print(proxy.dirty_fields())     # set()

# Modify a dependency
proxy.observable(str, "first_name").set("Bob")

# Only the dependency is marked as dirty, not the computed field
print(proxy.is_dirty())         # True
print(proxy.dirty_fields())     # {"first_name"}
```

## Practical Use Cases

### Enabling/Disabling Save Buttons

You can use the dirty state to enable or disable save buttons in a UI:

```python
# In a UI framework - use directly as bool
save_button.disabled = not proxy.is_dirty()

# Listen for changes to the dirty state
proxy.is_dirty().on_change(lambda dirty: setattr(save_button, 'disabled', not dirty))
```

### Prompting to Save Changes

You can use the dirty state to prompt users to save changes before navigating away:

```python
def on_navigate_away():
    if proxy.is_dirty():
        # Show a confirmation dialog
        if confirm("You have unsaved changes. Save before leaving?"):
            save_changes()
    # Navigate away
    navigate_to_next_page()
```

### Optimizing Save Operations

You can use the dirty fields to optimize save operations by only saving modified fields:

```python
def save_changes():
    dirty = proxy.dirty_fields()
    if not dirty:
        return  # Nothing to save

    # Create a dictionary with only the dirty fields
    data = {}
    for field in dirty:
        if field == "name":
            data[field] = proxy.observable(str, field).get()
        elif field == "age":
            data[field] = proxy.observable(int, field).get()

    # Save only the dirty fields
    api.update_user(user_id, data)

    # Reset dirty state
    proxy.reset_dirty()
```

## Next Steps

Now that you understand how dirty tracking works in Observant, you might want to explore:

- [Sync vs Non-Sync](sync.md): Understand immediate vs. deferred updates
- [Saving and Loading](save_load.md): Save changes and load data
- [API Reference](../api_reference/index.md): Detailed API documentation

[← Back to Overview](../index.md)
