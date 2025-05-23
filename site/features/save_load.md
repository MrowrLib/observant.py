# Saving and Loading

Observant provides methods for saving changes back to the model and loading data from external sources. This page explains how saving and loading work in Observant.

## Overview

When working with `ObservableProxy`, you often need to:

- Save changes back to the original model
- Load data from external sources (e.g., API responses, user input)
- Update multiple fields at once

Observant provides several methods for these operations:

- `save_to()`: Save changes back to a model
- `load_dict()`: Load data from a dictionary
- `update()`: Update specific fields

## save_to()

The `save_to()` method saves the current state of the proxy back to a model:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user and proxy
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=False)

# Make changes
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
name_obs.set("Bob")
age_obs.set(31)

# Save changes back to the model
proxy.save_to(user)

# The model is updated
print(user.name)  # "Bob"
print(user.age)   # 31
```

### Saving to a Different Model

You can save changes to a different model instance, as long as it has the same structure:

```python
# Create two user instances
user1 = User(name="Alice", age=30)
user2 = User(name="Charlie", age=32)

# Create a proxy for user1
proxy = ObservableProxy(user1, sync=False)

# Make changes
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
name_obs.set("Bob")
age_obs.set(31)

# Save changes to user2
proxy.save_to(user2)

# user2 is updated
print(user2.name)  # "Bob"
print(user2.age)   # 31

# user1 is unchanged
print(user1.name)  # "Alice"
print(user1.age)   # 30
```

This can be useful when you want to:

- Create a copy of a model with modifications
- Apply changes to multiple models
- Implement a "reset to original" feature

### Saving and Dirty State

When you call `save_to()`, the dirty state is automatically reset. This means that after saving, all fields are marked as clean:

```python
# Make changes
name_obs = proxy.observable(str, "name")
name_obs.set("Bob")

# The field is dirty
print(proxy.is_dirty())  # True

# Save changes
proxy.save_to(user)

# The field is now clean
print(proxy.is_dirty())  # False
```

If you want to manually reset the dirty state without saving, you can call `reset_dirty()`:

```python
# Make changes
name_obs = proxy.observable(str, "name")
name_obs.set("Bob")

# The field is dirty
print(proxy.is_dirty())  # True

# Reset dirty state without saving
proxy.reset_dirty()

# Now the field is not dirty
print(proxy.is_dirty())  # False
```

## load_dict()

The `load_dict()` method loads data from a dictionary into the proxy:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user and proxy
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=False)

# Load data from a dictionary
proxy.load_dict({
    "name": "Bob",
    "age": 31
})

# The proxy is updated
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
print(name_obs.get())  # "Bob"
print(age_obs.get())  # 31

# The model is not updated yet
print(user.name)  # "Alice"
print(user.age)   # 30

# Save changes to the model
proxy.save_to(user)

# Now the model is updated
print(user.name)  # "Bob"
print(user.age)   # 31
```

### Nested Data

Note that `load_dict()` does not automatically handle nested objects. If your model contains nested objects, you'll need to manually create proxies for them:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class Address:
    street: str
    city: str

@dataclass
class User:
    name: str
    address: Address

# Create a user with an address
user = User(name="Alice", address=Address(street="123 Main St", city="Anytown"))
proxy = ObservableProxy(user, sync=False)

# This will NOT work for nested objects:
proxy.load_dict({
    "name": "Bob",
    "address": {"street": "456 Oak St", "city": "Othertown"}  # Not automatically proxied
})

# Instead, you need to handle nested objects manually:
proxy.observable(str, "name").set("Bob")
address_proxy = ObservableProxy(user.address, sync=False)
address_proxy.load_dict({
    "street": "456 Oak St",
    "city": "Othertown"
})
proxy.save_to(user)
address_proxy.save_to(user.address)
```

### reset_missing

The `load_dict()` method has an optional `reset_missing` parameter. When set to `True`, fields that are not in the dictionary are reset to their default values:

```python
# Load data with reset_missing=True
proxy.load_dict({
    "name": "Charlie"
}, reset_missing=True)

# Fields not in the dictionary are reset
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
print(name_obs.get())  # "Charlie"
print(age_obs.get())  # 0 (default value for int)
```

When `reset_missing=False` (the default), fields not in the dictionary are left unchanged:

```python
# Load data with reset_missing=False
proxy.load_dict({
    "name": "Dave"
}, reset_missing=False)

# Fields not in the dictionary are unchanged
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
print(name_obs.get())  # "Dave"
print(age_obs.get())  # 31 (unchanged)
```

### Validation and load_dict()

When you call `load_dict()`, validation is automatically triggered for the fields that are updated:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user and proxy
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=False)

# Add validators
proxy.add_validator("name", lambda v: "Name required" if not v else None)
proxy.add_validator("age", lambda v: "Age must be positive" if v <= 0 else None)

# Load valid data
proxy.load_dict({
    "name": "Bob",
    "age": 31
})

# Validation passes
print(proxy.is_valid().get())  # True

# Load invalid data
proxy.load_dict({
    "name": "",
    "age": -1
})

# Validation fails
print(proxy.is_valid().get())  # False
print(proxy.validation_errors().get())  # {"name": ["Name required"], "age": ["Age must be positive"]}
```

## update()

The `update()` method updates specific fields in the proxy:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int
    email: str

# Create a user and proxy
user = User(name="Alice", age=30, email="alice@example.com")
proxy = ObservableProxy(user, sync=False)

# Update specific fields
proxy.update({
    "name": "Bob",
    "age": 31
})

# Only the specified fields are updated
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
email_obs = proxy.observable(str, "email")
print(name_obs.get())  # "Bob"
print(age_obs.get())  # 31
print(email_obs.get())  # "alice@example.com" (unchanged)
```

### update() vs load_dict()

The main differences between `update()` and `load_dict()` are:

1. `update()` only updates the fields that are provided in the dictionary
2. `load_dict()` can optionally reset fields that are not in the dictionary
3. `update()` does not have a `reset_missing` parameter

```python
# update() only updates the specified fields
proxy.update({
    "name": "Charlie"
})
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
print(name_obs.get())  # "Charlie"
print(age_obs.get())  # 31 (unchanged)

# load_dict() with reset_missing=True resets unspecified fields
proxy.load_dict({
    "name": "Dave"
}, reset_missing=True)
print(name_obs.get())  # "Dave"
print(age_obs.get())  # 0 (reset to default)
```

## Saving to Different Models

One powerful feature of Observant is the ability to save changes to different models. This can be useful for:

- Creating copies of a model with modifications
- Applying changes to multiple models
- Implementing a "reset to original" feature

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create original user
original_user = User(name="Alice", age=30)

# Create a proxy
proxy = ObservableProxy(original_user, sync=False)

# Make changes
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
name_obs.set("Bob")
age_obs.set(31)

# Create a modified copy
modified_user = User(name="", age=0)
proxy.save_to(modified_user)

# original_user is unchanged
print(original_user.name)  # "Alice"
print(original_user.age)   # 30

# modified_user has the changes
print(modified_user.name)  # "Bob"
print(modified_user.age)   # 31
```

### Saving to Models with Different Fields

When saving to a model with a different structure, only the fields that exist in both the proxy and the target model are updated:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int
    email: str

@dataclass
class SimpleUser:
    name: str
    age: int

# Create a user and proxy
user = User(name="Alice", age=30, email="alice@example.com")
proxy = ObservableProxy(user, sync=False)

# Make changes
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")
email_obs = proxy.observable(str, "email")
name_obs.set("Bob")
age_obs.set(31)
email_obs.set("bob@example.com")

# Create a simple user
simple_user = SimpleUser(name="", age=0)

# Save changes to the simple user
proxy.save_to(simple_user)

# Only the fields that exist in SimpleUser are updated
print(simple_user.name)  # "Bob"
print(simple_user.age)   # 31
# simple_user doesn't have an email field
```

## Reusing a Single Proxy

A powerful feature of Observant is the ability to reuse a single proxy instance across multiple data loads. This preserves observers, computed properties, and other state:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user and proxy
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, sync=False)

# Register an observer
name_obs = proxy.observable(str, "name")
name_obs.on_change(lambda value: print(f"Name changed to: {value}"))

# Make a change
name_obs.set("Bob")  # Prints: "Name changed to: Bob"

# Later, load new data into the SAME proxy
new_data = User(name="Charlie", age=25)
proxy.load_from(new_data)  # Loads data from new_data into the existing proxy

# The observer is still active
name_obs.set("Dave")  # Prints: "Name changed to: Dave"

# Save changes to the original user
proxy.save_to(user)
print(user.name)  # "Dave"
```

This approach is particularly useful when:

1. You have UI elements bound to observables and want to update the data without rebinding
2. You have complex observer setups that you want to preserve
3. You're implementing undo/redo and want to maintain the history

## Next Steps

Now that you understand how saving and loading work in Observant, you might want to explore:

- [API Reference](../api_reference/index.md): Detailed API documentation
- [Sync vs Non-Sync](sync.md): Understand immediate vs. deferred updates
- [Dirty Tracking](dirty.md): Track unsaved changes

[← Back to Overview](../index.md)
