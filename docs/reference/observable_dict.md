# ObservableDict

The `ObservableDict` class provides an observable wrapper around a Python dictionary. It notifies listeners when entries are added, updated, or removed.

## Basic Usage

```python
from observant import ObservableDict

# Create an observable dictionary with initial values
settings = ObservableDict({"theme": "dark", "notifications": True})

# Register a callback to be notified when the dictionary changes
settings.on_change(lambda change: print(f"Dict changed: {change.key} = {change.value}"))

# Modify the dictionary
settings["theme"] = "light"  # Prints: Dict changed: theme = light
settings["sound"] = "on"  # Prints: Dict changed: sound = on
del settings["notifications"]  # Prints: Dict changed: notifications = True
settings.clear()  # Prints a clear notification
```

## Type Safety

`ObservableDict` is generic over the types of keys and values it contains:

```python
from observant import ObservableDict

# Type-safe observable dictionary
user_ages: ObservableDict[str, int] = ObservableDict({"Alice": 32, "Bob": 28})
settings: ObservableDict[str, bool] = ObservableDict({"dark_mode": True, "notifications": False})

# The IDE and type checker will warn about incorrect types
user_ages["Charlie"] = "thirty"  # Type error: Expected int, got str
settings[42] = True  # Type error: Expected str key, got int
```

## Change Notifications

When the dictionary changes, the callback receives a `DictChange` object with the following properties:

- `type`: The type of change (SET, REMOVE, CLEAR)
- `key`: The key that was changed (None for CLEAR)
- `value`: The new value for SET operations, or the removed value for REMOVE operations
- `old_value`: The previous value for SET operations (if the key existed)
- `old_items`: For CLEAR operations, the dictionary of items that were cleared

```python
from observant import ObservableDict
from observant.types.collection_change_type import ObservableCollectionChangeType

settings = ObservableDict({"theme": "dark", "notifications": True})

def on_change(change):
    if change.type == ObservableCollectionChangeType.SET:
        if hasattr(change, 'old_value'):
            print(f"Updated {change.key} from {change.old_value} to {change.value}")
        else:
            print(f"Added {change.key} = {change.value}")
    elif change.type == ObservableCollectionChangeType.REMOVE:
        print(f"Removed {change.key} = {change.value}")
    elif change.type == ObservableCollectionChangeType.CLEAR:
        print(f"Cleared {len(change.old_items)} items: {change.old_items}")

settings.on_change(on_change)

settings["theme"] = "light"  # Prints: Updated theme from dark to light
settings["sound"] = "on"  # Prints: Added sound = on
del settings["notifications"]  # Prints: Removed notifications = True
settings.clear()  # Prints: Cleared 2 items: {'theme': 'light', 'sound': 'on'}
```

## API Reference

### Constructor

```python
ObservableDict(initial_items: dict[TKey, TValue] = None, copy: bool = True)
```

- `initial_items`: The initial dictionary of items (default: empty dict)
- `copy`: Whether to copy the initial items (default: True)

### Dictionary Operations

`ObservableDict` supports all standard dictionary operations:

```python
settings = ObservableDict({"theme": "dark", "notifications": True})

# Set a value
settings["sound"] = "on"

# Get a value
theme = settings["theme"]
sound = settings.get("sound", "off")  # With default value

# Remove a key
del settings["notifications"]
removed_value = settings.pop("theme")

# Check if a key exists
if "sound" in settings:
    print("Sound setting exists!")

# Clear the dictionary
settings.clear()

# Get the length
length = len(settings)

# Iterate over keys
for key in settings:
    print(key)

# Iterate over key-value pairs
for key, value in settings.items():
    print(f"{key} = {value}")

# Get all keys and values
keys = settings.keys()
values = settings.values()
```

### Additional Methods

#### `on_change()`

```python
def on_change(self, callback: Callable[[DictChange[TKey, TValue]], None]) -> None
```

Registers a callback to be notified when the dictionary changes.

- `callback`: A function that takes a `DictChange` object as its argument

#### `copy()`

```python
def copy(self) -> dict[TKey, TValue]
```

Returns a copy of the underlying dictionary.

#### `update()`

```python
def update(self, other: dict[TKey, TValue]) -> None
```

Updates the dictionary with key-value pairs from another dictionary.

## Examples

### Form Validation

```python
from observant import ObservableDict
from typing import Dict, List, Optional

class FormValidator:
    def __init__(self, initial_values: Dict[str, str] = None):
        self.values = ObservableDict(initial_values or {})
        self.errors = ObservableDict[str, List[str]]({})
        self.validators: Dict[str, List[callable]] = {}
        
        # Validate when values change
        self.values.on_change(self._on_value_change)
    
    def add_validator(self, field: str, validator: callable):
        """Add a validator function for a field.
        
        The validator should take a value and return an error message or None.
        """
        if field not in self.validators:
            self.validators[field] = []
        self.validators[field].append(validator)
        
        # Validate immediately if the field has a value
        if field in self.values:
            self._validate_field(field, self.values[field])
    
    def _on_value_change(self, change):
        if change.type.name == "SET" and change.key is not None:
            self._validate_field(change.key, change.value)
    
    def _validate_field(self, field: str, value: str):
        if field not in self.validators:
            return
        
        field_errors = []
        for validator in self.validators[field]:
            error = validator(value)
            if error:
                field_errors.append(error)
        
        if field_errors:
            self.errors[field] = field_errors
        elif field in self.errors:
            del self.errors[field]
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

# Usage
form = FormValidator({
    "username": "",
    "email": "",
    "password": ""
})

# Add validators
form.add_validator("username", lambda v: "Username is required" if not v else None)
form.add_validator("email", lambda v: "Email is required" if not v else None)
form.add_validator("email", lambda v: "Invalid email format" if v and "@" not in v else None)
form.add_validator("password", lambda v: "Password must be at least 8 characters" if len(v) < 8 else None)

# Track errors
form.errors.on_change(lambda _: print(f"Form errors: {form.errors.copy()}"))

# Update values
form.values["username"] = "alice"  # No errors
form.values["email"] = "alice"  # Error: Invalid email format
form.values["email"] = "alice@example.com"  # No errors
form.values["password"] = "1234"  # Error: Password must be at least 8 characters
```

### Settings Manager

```python
from observant import ObservableDict
import json
import os

class SettingsManager:
    def __init__(self, filename: str, defaults: dict = None):
        self.filename = filename
        self.defaults = defaults or {}
        self.settings = ObservableDict(self.defaults.copy())
        
        # Load settings from file if it exists
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except (json.JSONDecodeError, IOError):
                # If loading fails, use defaults
                pass
        
        # Save settings when they change
        self.settings.on_change(lambda _: self.save())
    
    def save(self):
        """Save settings to file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.settings.copy(), f, indent=2)
        except IOError:
            print(f"Error saving settings to {self.filename}")
    
    def reset(self):
        """Reset settings to defaults."""
        self.settings.clear()
        self.settings.update(self.defaults)

# Usage
settings = SettingsManager("settings.json", {
    "theme": "light",
    "font_size": 12,
    "notifications": True
})

# Access settings
current_theme = settings.settings["theme"]

# Update settings (automatically saved to file)
settings.settings["theme"] = "dark"
settings.settings["font_size"] = 14

# Reset to defaults
settings.reset()
```

## Implementation Details

The `ObservableDict` class implements the `IObservableDict` interface, which is defined in `observant.interfaces.dict`. This interface ensures that all observable dictionary types in the library have a consistent API.

For more advanced use cases, consider using `ObservableProxy` which can automatically create observable dictionaries for dictionary fields in a data object.

## API Documentation

[API Reference for ObservableDict](../api_reference.md#observabledict)
