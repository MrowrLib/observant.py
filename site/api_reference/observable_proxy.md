# ObservableProxy

The `ObservableProxy` class is the most powerful component in Observant. It wraps an object (typically a dataclass) and provides observable access to its fields, along with validation, undo/redo, computed properties, and dirty tracking.

## Overview

`ObservableProxy` allows you to:

- Access fields as observables
- Validate field values
- Track changes to fields
- Implement undo/redo functionality
- Create computed properties
- Track dirty state
- Save changes back to the model

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

## Constructor

```python
ObservableProxy(model: Any, sync: bool = False, undo: bool = False)
```

Creates a new `ObservableProxy` for the specified model.

### Parameters

- `model`: The model to wrap.
- `sync`: Whether to synchronize changes to the model immediately. Default is `False`.
- `undo`: Whether to enable undo/redo functionality for all fields. Default is `False`.

## Field Access

### observable

```python
observable(type_: Type[T], field: str) -> Observable[T]
```

Gets an observable for the specified field.

#### Parameters

- `type_`: The type of the field.
- `field`: The name of the field.

#### Returns

An `Observable` for the specified field.

### observable_list

```python
observable_list(type_: Type[T], field: str) -> ObservableList[T]
```

Gets an observable list for the specified field.

#### Parameters

- `type_`: The type of items in the list.
- `field`: The name of the field.

#### Returns

An `ObservableList` for the specified field.

### observable_dict

```python
observable_dict(type_: tuple[Type[K], Type[V]], field: str) -> ObservableDict[K, V]
```

Gets an observable dictionary for the specified field.

#### Parameters

- `type_`: A tuple containing the types of keys and values in the dictionary.
- `field`: The name of the field.

#### Returns

An `ObservableDict` for the specified field.

## Validation

### add_validator

```python
add_validator(field: str, validator: Callable[[Any], str | None]) -> None
```

Adds a validator for the specified field.

#### Parameters

- `field`: The name of the field to validate.
- `validator`: A function that takes the field value and returns an error message if the value is invalid, or `None` if the value is valid.

### validation_for

```python
validation_for(field: str) -> Observable[list[str]]
```

Gets an observable list of validation errors for the specified field.

#### Parameters

- `field`: The name of the field.

#### Returns

An `Observable` containing a list of validation error messages for the field.

### validation_errors

```python
validation_errors() -> ObservableDict[str, list[str]]
```

Gets an observable dictionary of validation errors for all fields.

#### Returns

An `ObservableDict` where keys are field names and values are lists of validation error messages.

### is_valid

```python
is_valid() -> Observable[bool]
```

Gets an observable boolean indicating whether all fields are valid.

#### Returns

An `Observable` containing a boolean value.

### reset_validation

```python
reset_validation(field: str = None, revalidate: bool = True) -> None
```

Resets the validation state for the specified field or for all fields.

#### Parameters

- `field`: The name of the field to reset validation for. If `None`, resets validation for all fields. Default is `None`.
- `revalidate`: Whether to re-run validators after resetting. Default is `True`.

## Computed Properties

### register_computed

```python
register_computed(field: str, compute: Callable[[], T], dependencies: list[str]) -> None
```

Registers a computed property.

#### Parameters

- `field`: The name of the computed property.
- `compute`: A function that computes the value of the property.
- `dependencies`: A list of field names that the computed property depends on.

### computed

```python
computed(type_: Type[T], field: str) -> Observable[T]
```

Gets an observable for the specified computed property.

#### Parameters

- `type_`: The type of the computed property.
- `field`: The name of the computed property.

#### Returns

An `Observable` for the specified computed property.

## Undo/Redo

### set_undo_config

```python
set_undo_config(field: str, enabled: bool = True, undo_max: int = None, undo_debounce_ms: int = None) -> None
```

Sets the undo configuration for the specified field.

#### Parameters

- `field`: The name of the field.
- `enabled`: Whether undo is enabled for the field. Default is `True`.
- `undo_max`: Maximum number of undo steps to store. Default is `None` (unlimited).
- `undo_debounce_ms`: Time in milliseconds to wait before recording a new undo step. Default is `None` (no debounce).

### undo

```python
undo(field: str) -> None
```

Undoes the last change to the specified field.

#### Parameters

- `field`: The name of the field.

### redo

```python
redo(field: str) -> None
```

Redoes the last undone change to the specified field.

#### Parameters

- `field`: The name of the field.

### can_undo

```python
can_undo(field: str) -> Observable[bool]
```

Gets an observable boolean indicating whether undo is available for the specified field.

#### Parameters

- `field`: The name of the field.

#### Returns

An `Observable` containing a boolean value.

### can_redo

```python
can_redo(field: str) -> Observable[bool]
```

Gets an observable boolean indicating whether redo is available for the specified field.

#### Parameters

- `field`: The name of the field.

#### Returns

An `Observable` containing a boolean value.

## Dirty Tracking

### is_dirty

```python
is_dirty() -> Observable[bool]
```

Gets an observable boolean indicating whether any field is dirty.

#### Returns

An `Observable` containing a boolean value.

### dirty_fields

```python
dirty_fields() -> Observable[list[str]]
```

Gets an observable list of dirty field names.

#### Returns

An `Observable` containing a list of field names.

### is_field_dirty

```python
is_field_dirty(field: str) -> Observable[bool]
```

Gets an observable boolean indicating whether the specified field is dirty.

#### Parameters

- `field`: The name of the field.

#### Returns

An `Observable` containing a boolean value.

### reset_dirty

```python
reset_dirty(field: str = None) -> None
```

Resets the dirty state for the specified field or for all fields.

#### Parameters

- `field`: The name of the field to reset dirty state for. If `None`, resets dirty state for all fields. Default is `None`.

## Saving and Loading

### save_to

```python
save_to(model: Any) -> None
```

Saves the current state of the proxy to the specified model.

#### Parameters

- `model`: The model to save to.

### load_dict

```python
load_dict(data: dict[str, Any], reset_missing: bool = False) -> None
```

Loads data from a dictionary into the proxy.

#### Parameters

- `data`: The dictionary to load data from.
- `reset_missing`: Whether to reset fields that are not in the dictionary to their default values. Default is `False`.

### update

```python
update(data: dict[str, Any]) -> None
```

Updates specific fields in the proxy.

#### Parameters

- `data`: A dictionary where keys are field names and values are the new values to set.

## Examples

### Basic Usage

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

# Get observables for individual fields
name_obs = proxy.observable(str, "name")
age_obs = proxy.observable(int, "age")

# Update fields
name_obs.set("Bob")
age_obs.set(31)

# Save changes back to the model
proxy.save_to(user)
print(user.name)  # "Bob"
print(user.age)   # 31
```

### Validation

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user and proxy
user = User(name="", age=0)
proxy = ObservableProxy(user)

# Add validators
proxy.add_validator("name", lambda v: "Name required" if not v else None)
proxy.add_validator("age", lambda v: "Age must be positive" if v <= 0 else None)

# Check validation
print(proxy.is_valid())  # False
print(proxy.validation_errors())  # {"name": ["Name required"], "age": ["Age must be positive"]}

# Fix validation errors
proxy.observable(str, "name").set("Alice")
proxy.observable(int, "age").set(30)

# Check validation again
print(proxy.is_valid())  # True
print(proxy.validation_errors())  # {}
```

### Computed Properties

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

# Register a computed property
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
    dependencies=["first_name", "last_name"]
)

# Get the computed value
print(proxy.computed(str, "full_name").get())  # "Alice Smith"

# Update a dependency
proxy.observable(str, "first_name").set("Bob")

# The computed value is automatically updated
print(proxy.computed(str, "full_name").get())  # "Bob Smith"
```

### Undo/Redo

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class User:
    name: str
    age: int

# Create a user and proxy with undo enabled
user = User(name="Alice", age=30)
proxy = ObservableProxy(user, undo=True)

# Make changes
proxy.observable(str, "name").set("Bob")
proxy.observable(int, "age").set(31)

# Undo changes
proxy.undo("name")  # Reverts name to "Alice"
proxy.undo("age")   # Reverts age to 30

# Redo changes
proxy.redo("name")  # Sets name back to "Bob"
proxy.redo("age")   # Sets age back to 31
```

### Dirty Tracking

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
print(proxy.is_dirty().get())  # False
print(proxy.dirty_fields().get())  # []

# Modify a field
proxy.observable(str, "name").set("Bob")

# Now the field is dirty
print(proxy.is_dirty().get())  # True
print(proxy.dirty_fields().get())  # ["name"]

# Reset dirty state
proxy.reset_dirty()

# Now no fields are dirty again
print(proxy.is_dirty().get())  # False
print(proxy.dirty_fields().get())  # []
```

## Implementation Details

The `ObservableProxy` class implements the `IObservableProxy` interface, which defines the contract for observable proxies. This interface is used throughout Observant to ensure consistent behavior across different types of proxies.

For more details on the implementation, see the [source code](https://github.com/MrowrLib/observant.py/blob/main/observant/observable_proxy.py).

## See Also

- [Observable](observable.md): The base observable class for scalar values.
- [ObservableList](observable_list.md): An observable list that notifies listeners when items are added, removed, or modified.
- [ObservableDict](observable_dict.md): An observable dictionary that notifies listeners when items are added, updated, or removed.
- [UndoableObservable](undoable_observable.md): An observable that supports undo and redo operations.
- IObservableProxy: The interface that defines the contract for observable proxies.
