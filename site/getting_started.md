# Getting Started

This guide will help you get started with Observant, a reactive state management library for Python.

## Installation

Install Observant using pip:

```bash
pip install observant
```

## Basic Concepts

Before diving into code examples, let's understand the core concepts of Observant.

### Observable

An `Observable` is a wrapper around a value that notifies listeners when the value changes. It's the simplest building block in Observant.

```python
from observant import Observable

# Create an observable with an initial value
name = Observable[str]("Alice")

# Register a callback to be notified when the value changes
name.on_change(lambda value: print(f"Name changed to: {value}"))

# Change the value
name.set("Bob")  # Prints: "Name changed to: Bob"

# Get the current value
current_name = name.get()  # Returns: "Bob"
```

### ObservableList and ObservableDict

Observant also provides observable collections that notify listeners when items are added, removed, or updated.

```python
from observant import ObservableList, ObservableDict

# Observable list
tasks = ObservableList[str](["Task 1"])
tasks.on_change(lambda change: print(f"Tasks changed: {change}"))
tasks.append("Task 2")  # Notifies listeners

# Observable dictionary
settings = ObservableDict[str, str]({"theme": "dark"})
settings.on_change(lambda change: print(f"Settings changed: {change}"))
settings["language"] = "en"  # Notifies listeners
```

### ObservableProxy

The `ObservableProxy` is the most powerful component in Observant. It wraps an object (typically a dataclass) and provides observable access to its fields.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int
    email: str

# Create a user and wrap it with a proxy
user = User(name="Alice", age=30, email="alice@example.com")
proxy = ObservableProxy(user)

# Get observables for individual fields
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")

# Register change listeners
name_obs.on_change(lambda value: print(f"Name changed to: {value}"))
age_obs.on_change(lambda value: print(f"Age changed to: {value}"))

# Update fields
name_obs.set("Alicia")  # Prints: "Name changed to: Alicia"
age_obs.set(31)         # Prints: "Age changed to: 31"

# Save changes back to the original object
proxy.save_to(user)
print(user.name)  # Prints: "Alicia"
print(user.age)   # Prints: 31
```

## Minimal Example

Here's a complete example showing how to use Observant with a simple form:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class LoginForm:
    username: str
    password: str
    remember_me: bool

# Create a form and proxy
form = LoginForm(username="", password="", remember_me=False)
proxy = ObservableProxy(form)

# Add validation
proxy.add_validator("username", lambda v: "Username required" if not v else None)
proxy.add_validator("password", lambda v: "Password too short" if len(v) < 8 else None)

# Track changes
proxy.observable(str, "username").on_change(lambda v: print(f"Username: {v}"))
proxy.observable(str, "password").on_change(lambda v: print(f"Password: {'*' * len(v)}"))
proxy.observable(bool, "remember_me").on_change(lambda v: print(f"Remember me: {v}"))

# Update fields
proxy.observable(str, "username").set("alice")
proxy.observable(str, "password").set("securepassword")
proxy.observable(bool, "remember_me").set(True)

# Check validation
if proxy.is_valid().get():
    print("Form is valid!")
    proxy.save_to(form)
else:
    print("Validation errors:", proxy.validation_errors())
```

## Anatomy of a Proxy

The `ObservableProxy` is the central component of Observant. Here's what it provides:

1. **Field Observables**: Access individual fields as observables
   ```python
   name_obs = proxy.observable(str, "name")
   ```

2. **Collection Observables**: Access lists and dictionaries as observable collections
   ```python
   tasks_list = proxy.observable_list(str, "tasks")
   settings_dict = proxy.observable_dict((str, str), "settings")
   ```

3. **Validation**: Add validators to fields and check validation state
   ```python
   proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
   is_valid = proxy.is_valid().get()
   errors = proxy.validation_errors()
   ```

4. **Computed Properties**: Define properties that depend on other fields
   ```python
   proxy.register_computed(
       "full_name",
       lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
       dependencies=["first_name", "last_name"]
   )
   full_name = proxy.computed(str, "full_name").get()
   ```

5. **Undo/Redo**: Track changes and undo/redo them
   ```python
   proxy = ObservableProxy(user, undo=True)
   proxy.observable(str, "name").set("Bob")
   proxy.undo("name")  # Reverts to previous value
   ```

6. **Dirty Tracking**: Track unsaved changes
   ```python
   is_dirty = proxy.is_dirty()
   dirty_fields = proxy.dirty_fields()
   proxy.reset_dirty()
   ```

7. **Saving and Loading**: Save changes back to the model or load from a dictionary
   ```python
   proxy.save_to(user)
   proxy.load_dict({"name": "Charlie", "age": 25})
   ```

## Next Steps

Now that you understand the basics, you can explore more advanced features:

- [Change Tracking](features/change_tracking.md): Learn more about observables and change notifications
- [Validation](features/validation.md): Add validation to your models
- [Computed Properties](features/computed.md): Create properties that depend on other fields
- [Undo and Redo](features/undo.md): Implement undo/redo functionality
- [Dirty Tracking](features/dirty.md): Track unsaved changes
- [Sync vs Non-Sync](features/sync.md): Understand immediate vs. deferred updates
- [Saving and Loading](features/save_load.md): Save changes and load data
