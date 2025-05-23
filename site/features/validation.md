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

## When to Validate

Observant's validation system is flexible and can be used in different ways depending on your needs. Here are three common approaches to validation timing:

### Immediate Validation

With immediate validation, validators run as soon as a field's value changes. This provides instant feedback to users but can be intrusive for fields that are still being edited.

```python
# Immediate validation is the default behavior
username_obs = proxy.observable(str, "username")
username_obs.set("a")  # Validation runs immediately

# Check validation errors
print(proxy.validation_for("username").get())  # ['Too short']
```

This approach is good for:
- Simple forms where immediate feedback is helpful
- Fields with critical validation requirements
- When you want to prevent invalid input as early as possible

### Deferred Validation

With deferred validation, you manually trigger validation when needed, such as when a form is submitted. This gives users more freedom to enter data without being interrupted by validation errors.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class LoginForm:
    username: str
    password: str

# Create a form and proxy
form = LoginForm(username="", password="")
proxy = ObservableProxy(form)

# Add validators but don't run them yet
proxy.add_validator("username", lambda v: "Username required" if not v else None)
proxy.add_validator("password", lambda v: "Password required" if not v else None)

# Disable automatic validation
username_obs = proxy.observable(str, "username")
username_obs.set("", notify=False)  # No validation runs
password_obs = proxy.observable(str, "password")
password_obs.set("", notify=False)  # No validation runs

# Later, when the form is submitted, manually trigger validation
def on_submit():
    # Force validation of all fields
    proxy.reset_validation()
    
    if proxy.is_valid().get():
        # Form is valid, proceed with submission
        print("Form submitted successfully")
    else:
        # Show validation errors
        print("Please fix the following errors:")
        for field, errors in proxy.validation_errors().get().items():
            print(f"{field}: {', '.join(errors)}")

# Test the submit function
on_submit()
# Prints:
# Please fix the following errors:
# username: Username required
# password: Password required
```

This approach is good for:
- Complex forms where immediate validation would be disruptive
- When you want to validate multiple fields at once
- When validation should only happen at specific points (e.g., form submission)

### Hybrid Validation

You can also use a hybrid approach, where some fields are validated immediately and others are validated only when needed:

```python
# Username is validated immediately
proxy.add_validator("username", lambda v: "Username required" if not v else None)

# Password is not validated until form submission
proxy.add_validator("password", lambda v: "Password required" if not v else None)
password_obs = proxy.observable(str, "password")
password_obs.set("", notify=False)  # No validation runs

# When the form is submitted, validate all fields
def on_submit():
    # Force validation of all fields
    proxy.reset_validation()
    
    if proxy.is_valid().get():
        # Form is valid, proceed with submission
        print("Form submitted successfully")
    else:
        # Show validation errors
        print("Please fix the following errors:")
        for field, errors in proxy.validation_errors().get().items():
            print(f"{field}: {', '.join(errors)}")
```

This approach is good for:
- Forms with a mix of critical and non-critical fields
- When you want immediate validation for some fields but not others
- When you want to balance user experience with validation requirements

## Clearing Validation Errors

Sometimes you may want to clear validation errors, for example after a successful form submission or when you want to reset the form.

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

This is particularly useful when:
- You've successfully saved the form and want to clear all validation errors
- You're resetting the form to its initial state
- You want to temporarily disable validation

### Practical Example: Form Submission

Here's a complete example of a form submission flow with validation:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class RegistrationForm:
    username: str
    email: str
    password: str

# Create a form and proxy
form = RegistrationForm(username="", email="", password="")
proxy = ObservableProxy(form)

# Add validators
proxy.add_validator("username", lambda v: "Username required" if not v else None)
proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
proxy.add_validator("password", lambda v: "Password too short" if len(v) < 8 else None)

# Function to handle form submission
def submit_form():
    # Force validation of all fields
    proxy.reset_validation()
    
    if proxy.is_valid().get():
        # Form is valid, proceed with submission
        print("Form submitted successfully")
        
        # Save the form data (e.g., to a database)
        save_to_database(proxy)
        
        # Clear all validation errors and mark form as clean
        proxy.reset_validation(revalidate=False)
        proxy.reset_dirty()
        
        return True
    else:
        # Show validation errors
        print("Please fix the following errors:")
        for field, errors in proxy.validation_errors().get().items():
            print(f"{field}: {', '.join(errors)}")
        
        return False

# Simulate user input
proxy.observable(str, "username").set("alice")
proxy.observable(str, "email").set("alice@example.com")
proxy.observable(str, "password").set("password123")

# Submit the form
submit_form()  # Prints: "Form submitted successfully"
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

[← Back to Overview](../index.md)
