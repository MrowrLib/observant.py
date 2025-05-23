# Getting Started with Observant.py

This guide will walk you through the basics of using Observant.py to manage observable state in your Python applications.

## Installation

Install Observant.py using pip:

```bash
pip install observant
```

## Basic Concepts

Observant.py provides several key components:

- **Observable**: A wrapper around a value that notifies listeners when the value changes
- **ObservableList**: A list that notifies listeners when items are added, removed, or the list is cleared
- **ObservableDict**: A dictionary that notifies listeners when entries are added, updated, or removed
- **ObservableProxy**: A proxy for a data object that exposes its fields as observables

## Using Observable

The `Observable` class is the simplest way to track changes to a value:

```python
from observant import Observable

# Create an observable with an initial value
name = Observable("Ada")

# Register a callback to be notified when the value changes
name.on_change(lambda value: print(f"Name changed to: {value}"))

# Change the value
name.set("Grace")  # Prints: Name changed to: Grace

# Get the current value
current_name = name.get()  # Returns: "Grace"
```

## Using ObservableList

`ObservableList` tracks changes to a list:

```python
from observant import ObservableList

# Create an observable list
fruits = ObservableList(["apple", "banana"])

# Register a callback
fruits.on_change(lambda change: print(f"List changed: {change.type.name} at index {change.index}"))

# Modify the list
fruits.append("cherry")  # Prints: List changed: ADD at index 2
fruits.pop(0)  # Prints: List changed: REMOVE at index 0
```

## Using ObservableDict

`ObservableDict` tracks changes to a dictionary:

```python
from observant import ObservableDict

# Create an observable dictionary
settings = ObservableDict({"theme": "dark", "notifications": True})

# Register a callback
settings.on_change(lambda change: print(f"Dict changed: {change.key} = {change.value}"))

# Modify the dictionary
settings["theme"] = "light"  # Prints: Dict changed: theme = light
settings["sound"] = "on"  # Prints: Dict changed: sound = on
```

## Using ObservableProxy

`ObservableProxy` is a powerful way to make an existing object observable:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    preferences: dict[str, str]
    friends: list[str]

# Create a user
user = User(
    name="Ada",
    age=36,
    preferences={"theme": "dark"},
    friends=["Charles", "Grace"]
)

# Create a proxy for the user
proxy = ObservableProxy(user)

# Access scalar fields as observables
name_obs = proxy.observable(str, "name")
name_obs.on_change(lambda name: print(f"Name changed to: {name}"))

# Access list fields as observable lists
friends_obs = proxy.observable_list(str, "friends")
friends_obs.on_change(lambda change: print(f"Friends changed: {change.type.name}"))

# Access dict fields as observable dictionaries
prefs_obs = proxy.observable_dict((str, str), "preferences")
prefs_obs.on_change(lambda change: print(f"Preferences changed: {change.key}"))

# Make changes
name_obs.set("Grace")  # Prints: Name changed to: Grace
friends_obs.append("Alan")  # Prints: Friends changed: ADD
prefs_obs["notifications"] = "on"  # Prints: Preferences changed: notifications

# Save changes back to the original object
proxy.save_to(user)
```

## Next Steps

Now that you understand the basics, you can explore more advanced features:

- [Validation](reference/proxy/validation.md): Add validators to ensure data integrity
- [Undo/Redo](reference/proxy/undo.md): Track and revert changes
- [Computed Fields](reference/proxy/computed.md): Create properties that automatically update
- [Syncing & Dirty State](reference/proxy/sync.md): Synchronize state between models

Check out the [Examples](examples/basic.md) section for more practical use cases.
