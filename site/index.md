<img src="assets/images/observant-py.png" width="300" />

# Observant

A reactive state management library for Python with observable objects, validation, undo/redo, and computed properties.

## What is Observant?

Observant is a Python library that brings reactive programming to your data models. It allows you to:

- Track changes to your data
- Validate data as it changes
- Implement undo/redo functionality
- Create computed properties that update automatically
- Keep track of "dirty" state for unsaved changes

At its core, Observant provides observable objects that notify listeners when their values change, making it easy to build reactive applications.

## Installation

```bash
pip install observant
```

## Key Features

### Observable Objects

```python
from observant import Observable

# Create an observable value
counter = Observable[int](0)

# Listen for changes
counter.on_change(lambda value: print(f"Counter changed to {value}"))

# Update the value
counter.set(1)  # Prints: "Counter changed to 1"
```

### Observable Collections

```python
from observant import ObservableList, ObservableDict

# Observable list
tasks = ObservableList[str](["Buy milk"])
tasks.on_change(lambda change: print(f"Tasks changed: {change}"))
tasks.append("Write docs")

# Observable dictionary
settings = ObservableDict[str, str]({"theme": "dark"})
settings.on_change(lambda change: print(f"Settings changed: {change}"))
settings["language"] = "en"
```

### Observable Proxy

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

user = User(name="Alice", age=30)
proxy = ObservableProxy(user)

# Get observable for a field
name_obs = proxy.observable(str, "name")
name_obs.on_change(lambda value: print(f"Name changed to {value}"))

# Update the field
name_obs.set("Alicia")  # Prints: "Name changed to Alicia"

# Save changes back to the model
proxy.save_to(user)
print(user.name)  # Prints: "Alicia"
```

### Validation

```python
from observant import ObservableProxy

# Add validators
proxy.add_validator("age", lambda age: "Must be positive" if age <= 0 else None)
proxy.add_validator("name", lambda name: "Name too short" if len(name) < 3 else None)

# Check validation state
print(proxy.is_valid())  # True or False
print(proxy.validation_errors())  # Dictionary of field errors
```

### Undo/Redo

```python
from observant import ObservableProxy

# Enable undo
proxy = ObservableProxy(user, undo=True)

# Make changes
proxy.observable(str, "name").set("Bob")
proxy.observable(int, "age").set(25)

# Undo changes
proxy.undo("name")  # Reverts name to "Alicia"
proxy.undo("age")   # Reverts age to 30

# Redo changes
proxy.redo("name")  # Sets name back to "Bob"
```

### Computed Properties

```python
from observant import ObservableProxy

# Register a computed property
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
    dependencies=["first_name", "last_name"]
)

# Access the computed value
print(proxy.computed(str, "full_name").get())
```


## Complete Form Example

```python
# This is a complete form implementation with validation, dirty tracking, and save logic
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class FormData:
    username: str
    email: str
    age: int

# Create a model and proxy
form = FormData(username="", email="", age=0)
proxy = ObservableProxy(form, undo=True)

# Add validation
proxy.add_validator("username", lambda v: "Required" if not v else None)
proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
proxy.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)

# Update fields
proxy.observable(str, "username").set("alice")
proxy.observable(str, "email").set("alice@example.com")
proxy.observable(int, "age").set(25)

# Check if valid
if proxy.is_valid():
    # Save changes
    proxy.save_to(form)
    print("Form saved!")
else:
    # Show errors
    print("Validation errors:", proxy.validation_errors())
```

## Where to Go Next

- [Getting Started](getting_started.md) - Learn the basics
- [Change Tracking](features/change_tracking.md) - Understand how observables work
- [API Reference](api_reference/index.md) - Detailed API documentation
