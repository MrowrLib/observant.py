# Validation

Observant provides a powerful validation system that allows you to validate your data as it changes. This page explains how validation works in Observant.

## Overview

Validation in Observant is field-based, meaning you can add validators to individual fields of your model. Validators are functions that check if a field's value is valid and return an error message if it's not.

The validation system provides:

- Field-level validation
- Multiple validators per field
- Observable validation state
- Validation for computed fields
- Exception handling in validators

## Adding Validators

You can add validators to a field using the `add_validator` method of `ObservableProxy`. A validator is a function that takes the field's value as input and returns either:

- `None` if the value is valid
- A string error message if the value is invalid

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    username: str
    email: str
    age: int

# Create a user and proxy
user = User(username="", email="", age=0)
proxy = ObservableProxy(user)

# Add validators
proxy.add_validator("username", lambda v: "Username required" if not v else None)
proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
proxy.add_validator("age", lambda v: "Must be positive" if v <= 0 else None)
```

### Multiple Validators

You can add multiple validators to the same field. All validators will run, and all error messages will be collected.

```python
# Add multiple validators to the same field
proxy.add_validator("username", lambda v: "Username required" if not v else None)
proxy.add_validator("username", lambda v: "Too short" if len(v) < 3 else None)
proxy.add_validator("username", lambda v: "No spaces allowed" if " " in v else None)

# Set an invalid value
proxy.observable(str, "username").set("a")

# Check validation errors
errors = proxy.validation_for("username").get()
print(errors)  # ['Too short']
```

### Complex Validators

Validators can be as simple or complex as needed. Here's an example of a more complex validator:

```python
def validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one digit"
    return None

proxy.add_validator("password", validate_password)
```

## validation_errors() and validation_for()

Observant provides two main methods for checking validation state:

- `validation_errors()`: Returns an observable dictionary of all validation errors
- `validation_for(field)`: Returns an observable list of validation errors for a specific field

### validation_errors()

The `validation_errors()` method returns an observable dictionary where:

- Keys are field names with validation errors
- Values are lists of error messages for each field

```python
# Check all validation errors
errors = proxy.validation_errors()
print(errors)  # {'username': ['Too short'], 'email': ['Invalid email'], 'age': ['Must be positive']}

# The errors dictionary is observable
errors.on_change(lambda change: print(f"Validation errors changed: {change}"))

# Fix the username
proxy.observable(str, "username").set("alice")
# The errors dictionary will update automatically
```

### validation_for()

The `validation_for(field)` method returns an observable list of validation errors for a specific field:

```python
# Check validation errors for a specific field
username_errors = proxy.validation_for("username").get()
print(username_errors)  # ['Too short']

# The errors list is observable
proxy.validation_for("username").on_change(lambda errors: print(f"Username errors: {errors}"))

# Fix the username
proxy.observable(str, "username").set("alice")
# Prints: "Username errors: []"
```

### is_valid()

The `is_valid()` method returns an observable boolean indicating whether the entire model is valid:

```python
# Check if the model is valid
is_valid = proxy.is_valid()
print(is_valid)  # False

# The is_valid observable updates automatically
proxy.is_valid().on_change(lambda valid: print(f"Model is valid: {valid}"))

# Fix all validation errors
proxy.observable(str, "username").set("alice")
proxy.observable(str, "email").set("alice@example.com")
proxy.observable(int, "age").set(30)
# Prints: "Model is valid: True"
```

## Resetting Validation

Sometimes you may want to reset the validation state, for example when a form is submitted or when you want to clear all validation errors.

### reset_validation()

The `reset_validation()` method resets the validation state for all fields or for a specific field:

```python
# Reset validation for all fields
proxy.reset_validation()

# Reset validation for a specific field
proxy.reset_validation("username")
```

By default, `reset_validation()` also re-runs the validators. If you want to just clear the validation state without re-running the validators, you can set `revalidate=False`:

```python
# Reset validation without re-running validators
proxy.reset_validation(revalidate=False)
```

## Computed Field Validation

Observant also supports validation for computed fields. When a computed field's dependencies change, the computed field's validators are automatically re-run.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    first_name: str
    last_name: str

# Create a user and proxy
user = User(first_name="", last_name="")
proxy = ObservableProxy(user)

# Register a computed property for full name
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
    dependencies=["first_name", "last_name"]
)

# Add a validator to the computed field
proxy.add_validator("full_name", lambda v: "Full name too short" if len(v.strip()) < 5 else None)

# Check validation
print(proxy.is_valid())  # False
print(proxy.validation_for("full_name").get())  # ['Full name too short']

# Update the dependencies
proxy.observable(str, "first_name").set("Alice")
proxy.observable(str, "last_name").set("Smith")

# Validation is automatically updated
print(proxy.is_valid())  # True
print(proxy.validation_for("full_name").get())  # []
```

## Exception Handling in Validators

Validators can sometimes raise exceptions, especially if they perform complex operations. Observant catches these exceptions and converts them to validation error messages.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    username: str

# Create a user and proxy
user = User(username="")
proxy = ObservableProxy(user)

# Add a validator that might raise an exception
def buggy_validator(value):
    if not value:
        raise ValueError("Username cannot be empty")
    return None

proxy.add_validator("username", buggy_validator)

# Check validation
print(proxy.is_valid())  # False
print(proxy.validation_for("username").get())  # ['Username cannot be empty']

# Fix the value
proxy.observable(str, "username").set("alice")
print(proxy.is_valid())  # True
```

This feature is particularly useful when:

- You're integrating with external validation libraries that might raise exceptions
- You want to use assert-style validation that raises exceptions
- You're performing complex validation that might fail unexpectedly

### Different Types of Exceptions

Observant handles all types of exceptions in validators, not just `ValueError`:

```python
def type_error_validator(value):
    if not isinstance(value, str):
        raise TypeError("Value must be a string")
    return None

def key_error_validator(value):
    if value not in ["admin", "user", "guest"]:
        raise KeyError(f"Unknown role: {value}")
    return None

proxy.add_validator("role", type_error_validator)
proxy.add_validator("role", key_error_validator)
```

## Next Steps

Now that you understand how validation works in Observant, you might want to explore:

- [Computed Properties](computed.md): Create properties that depend on other fields
- [Undo and Redo](undo.md): Implement undo/redo functionality
- [Dirty Tracking](dirty.md): Track unsaved changes
