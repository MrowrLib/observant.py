# Validation

`ObservableProxy` provides a powerful validation system that allows you to ensure data integrity by adding validators to fields. This page explains how to use validation features.

## Basic Validation

You can add validators to any field in an `ObservableProxy`. A validator is a function that takes a value and returns an error message (as a string) if the value is invalid, or `None` if the value is valid.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    username: str
    email: str
    age: int

# Create a user
user = User(username="", email="", age=0)

# Create a proxy
proxy = ObservableProxy(user)

# Add validators
proxy.add_validator("username", lambda v: "Username is required" if not v else None)
proxy.add_validator("username", lambda v: "Username too short" if len(v) < 3 else None)
proxy.add_validator("email", lambda v: "Email is required" if not v else None)
proxy.add_validator("email", lambda v: "Invalid email" if v and "@" not in v else None)
proxy.add_validator("age", lambda v: "Age must be positive" if v <= 0 else None)

# Check if the proxy is valid
if not proxy.is_valid().get():
    print("User is invalid")
```

## Multiple Validators

You can add multiple validators to a single field. All validators will be run, and all error messages will be collected.

```python
# Add multiple validators to a field
proxy.add_validator("password", lambda v: "Password is required" if not v else None)
proxy.add_validator("password", lambda v: "Password too short" if len(v) < 8 else None)
proxy.add_validator("password", lambda v: "Password needs a number" if not any(c.isdigit() for c in v) else None)
proxy.add_validator("password", lambda v: "Password needs a special character" if not any(c in "!@#$%^&*" for c in v) else None)

# Set an invalid password
proxy.observable(str, "password").set("abc")

# Get all validation errors for the password field
errors = proxy.validation_for("password").get()
print(errors)  # ['Password too short', 'Password needs a number', 'Password needs a special character']
```

## Validation Events

You can listen for changes to the validation state of the entire proxy or individual fields.

```python
# Listen for changes to the overall validation state
proxy.is_valid().on_change(lambda valid: print(f"Form is {'valid' if valid else 'invalid'}"))

# Listen for changes to validation errors for a specific field
proxy.validation_for("username").on_change(
    lambda errors: print(f"Username errors: {errors}")
)

# Listen for all validation errors
proxy.validation_errors().on_change(
    lambda errors_dict: print(f"All errors: {errors_dict}")
)
```

## Validating Collections

You can also validate list and dictionary fields.

### Validating Lists

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List

@dataclass
class TodoList:
    items: List[str]

todo_list = TodoList(items=[])
proxy = ObservableProxy(todo_list)

# Validate the entire list
proxy.add_validator("items", lambda items: "List cannot be empty" if len(items) == 0 else None)

# Validate individual items in the list
proxy.add_validator("items", lambda items: "All items must be non-empty" if any(not item for item in items) else None)

# Get the observable list
items = proxy.observable_list(str, "items")

# Add some items
items.append("Buy groceries")
items.append("")  # This will trigger the "All items must be non-empty" validator

# Check validation errors
errors = proxy.validation_for("items").get()
print(errors)  # ['All items must be non-empty']
```

### Validating Dictionaries

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import Dict

@dataclass
class Settings:
    preferences: Dict[str, str]

settings = Settings(preferences={})
proxy = ObservableProxy(settings)

# Validate the entire dictionary
proxy.add_validator("preferences", lambda prefs: "Theme must be set" if "theme" not in prefs else None)

# Validate specific values in the dictionary
proxy.add_validator("preferences", lambda prefs: "Invalid theme" if prefs.get("theme") not in ["light", "dark"] else None)

# Get the observable dictionary
prefs = proxy.observable_dict((str, str), "preferences")

# Set some preferences
prefs["notifications"] = "on"  # This will trigger the "Theme must be set" validator
prefs["theme"] = "blue"  # This will trigger the "Invalid theme" validator

# Check validation errors
errors = proxy.validation_for("preferences").get()
print(errors)  # ['Invalid theme']
```

## Validation with Computed Fields

Computed fields can also be validated.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    first_name: str
    last_name: str

user = User(first_name="", last_name="")
proxy = ObservableProxy(user)

# Register a computed property for the full name
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}".strip(),
    ["first_name", "last_name"]
)

# Add a validator to the computed property
proxy.add_validator("full_name", lambda v: "Full name is required" if not v else None)

# Set values that will make the computed property invalid
proxy.observable(str, "first_name").set("")
proxy.observable(str, "last_name").set("")

# Check validation errors
errors = proxy.validation_for("full_name").get()
print(errors)  # ['Full name is required']
```

## Resetting Validation

You can reset validation errors for a specific field or all fields.

```python
# Reset validation for a specific field
proxy.reset_validation("username")

# Reset validation for all fields
proxy.reset_validation()

# Reset and revalidate
proxy.reset_validation("username", revalidate=True)
proxy.reset_validation(revalidate=True)
```

## Validation During Undo/Redo

Validation is automatically triggered during undo and redo operations.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    username: str

user = User(username="alice")
proxy = ObservableProxy(user, undo=True)

# Add a validator
proxy.add_validator("username", lambda v: "Username is required" if not v else None)

# Get the observable
username = proxy.observable(str, "username")

# Make a change that will be valid
username.set("bob")  # Valid

# Make a change that will be invalid
username.set("")  # Invalid

# Undo to the valid state
proxy.undo("username")  # Validation will be triggered, and the proxy will be valid again

# Redo to the invalid state
proxy.redo("username")  # Validation will be triggered, and the proxy will be invalid again
```

## Validation with Load and Save

Validation is triggered when loading values from a dictionary or saving to an object.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    username: str
    email: str

user = User(username="alice", email="alice@example.com")
proxy = ObservableProxy(user)

# Add validators
proxy.add_validator("username", lambda v: "Username is required" if not v else None)
proxy.add_validator("email", lambda v: "Email is required" if not v else None)

# Load invalid values
proxy.load_dict({
    "username": "",
    "email": ""
})

# Check if the proxy is valid
if not proxy.is_valid().get():
    print("User is invalid after loading")

# Fix the values
proxy.update(username="alice", email="alice@example.com")

# Save to a new object
new_user = User(username="", email="")
proxy.save_to(new_user)

print(new_user)  # User(username='alice', email='alice@example.com')
```

## Advanced Validation Patterns

### Cross-Field Validation

You can implement cross-field validation using computed properties.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    password: str
    confirm_password: str

user = User(password="", confirm_password="")
proxy = ObservableProxy(user)

# Register a computed property that checks if passwords match
proxy.register_computed(
    "passwords_match",
    lambda: proxy.observable(str, "password").get() == proxy.observable(str, "confirm_password").get(),
    ["password", "confirm_password"]
)

# Add a validator to the computed property
proxy.add_validator("passwords_match", lambda match: "Passwords do not match" if not match else None)

# Set different passwords
proxy.observable(str, "password").set("secret123")
proxy.observable(str, "confirm_password").set("secret456")

# Check validation errors
errors = proxy.validation_for("passwords_match").get()
print(errors)  # ['Passwords do not match']
```

### Custom Validator Classes

For more complex validation logic, you can create custom validator classes.

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import Optional

class EmailValidator:
    def __call__(self, value: str) -> Optional[str]:
        if not value:
            return "Email is required"
        if "@" not in value:
            return "Invalid email format"
        if not value.endswith((".com", ".org", ".net")):
            return "Email must end with .com, .org, or .net"
        return None

@dataclass
class User:
    email: str

user = User(email="")
proxy = ObservableProxy(user)

# Add the custom validator
proxy.add_validator("email", EmailValidator())

# Set an invalid email
proxy.observable(str, "email").set("alice@example")

# Check validation errors
errors = proxy.validation_for("email").get()
print(errors)  # ['Email must end with .com, .org, or .net']
```

## API Reference

### `add_validator()`

```python
def add_validator(
    self,
    attr: str,
    validator: Callable[[Any], str | None],
) -> None
```

Adds a validator function for a field.

- `attr`: The field name to validate
- `validator`: A function that takes the field value and returns an error message if invalid, or None if valid

### `is_valid()`

```python
def is_valid(self) -> IObservable[bool]
```

Gets an observable that indicates whether all fields are valid.

### `validation_errors()`

```python
def validation_errors(self) -> IObservableDict[str, list[str]]
```

Gets an observable dictionary of validation errors.

### `validation_for()`

```python
def validation_for(self, attr: str) -> IObservable[list[str]]
```

Gets an observable list of validation errors for a specific field.

### `reset_validation()`

```python
def reset_validation(self, attr: str | None = None, *, revalidate: bool = False) -> None
```

Resets validation errors for a specific field or all fields.

- `attr`: The field name to reset validation for. If None, reset all fields.
- `revalidate`: Whether to re-run validators after clearing errors.
