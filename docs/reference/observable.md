# Observable {#ref-observable}

The `Observable` class is the foundation of Observant.py. It wraps a value and notifies listeners when the value changes.

## Basic Usage

```python
from observant import Observable

# Create an observable with an initial value
counter = Observable(0)

# Register a callback to be notified when the value changes
counter.on_change(lambda value: print(f"Counter changed to {value}"))

# Change the value
counter.set(1)  # Prints: Counter changed to 1

# Get the current value
current_value = counter.get()  # Returns: 1
```

## Type Safety

`Observable` is generic over the type of value it contains:

```python
from observant import Observable
from typing import List

# Type-safe observable
name: Observable[str] = Observable("Ada")
numbers: Observable[List[int]] = Observable([1, 2, 3])

# The IDE and type checker will warn about incorrect types
name.set(42)  # Type error: Expected str, got int
```

## API Reference

### Constructor

```python
Observable(initial_value: T, on_change_enabled: bool = True)
```

- `initial_value`: The initial value to store
- `on_change_enabled`: Whether to enable change notifications immediately

### Methods

#### `get()`

```python
def get(self) -> T
```

Returns the current value.

#### `set()`

```python
def set(self, value: T, notify: bool = True) -> None
```

Sets a new value.

- `value`: The new value to set
- `notify`: Whether to notify listeners of the change

#### `on_change()`

```python
def on_change(self, callback: Callable[[T], None]) -> None
```

Registers a callback to be notified when the value changes.

- `callback`: A function that takes the new value as its argument

#### `enable()`

```python
def enable(self) -> None
```

Enables change notifications.

#### `disable()`

```python
def disable(self) -> None
```

Disables change notifications.

## Examples

### Tracking UI State

```python
from observant import Observable

# Track UI state
is_loading = Observable(False)
error_message = Observable("")
user_data = Observable(None)

# Update UI when state changes
is_loading.on_change(lambda loading: update_loading_spinner(loading))
error_message.on_change(lambda error: show_error(error) if error else hide_error())
user_data.on_change(lambda data: render_user(data) if data else show_login())

# During an API call
is_loading.set(True)
try:
    data = api.fetch_user()
    user_data.set(data)
    error_message.set("")
except Exception as e:
    error_message.set(str(e))
    user_data.set(None)
finally:
    is_loading.set(False)
```

### Debouncing Changes

```python
from observant import Observable
import time
from threading import Timer

def debounce(wait):
    """Decorator that will postpone a function's execution until after wait seconds
    have elapsed since the last time it was invoked."""
    def decorator(fn):
        timer = None
        def debounced(*args, **kwargs):
            nonlocal timer
            if timer is not None:
                timer.cancel()
            timer = Timer(wait, lambda: fn(*args, **kwargs))
            timer.start()
        return debounced
    return decorator

# Create an observable for a search query
search_query = Observable("")

# Create a debounced search function
@debounce(0.5)  # Wait 500ms before searching
def perform_search(query):
    print(f"Searching for: {query}")
    # Actual search logic here...

# Connect the observable to the debounced function
search_query.on_change(perform_search)

# Simulate user typing
search_query.set("a")
search_query.set("ap")
search_query.set("app")
search_query.set("appl")
search_query.set("apple")

# Only the final "apple" will trigger the search after 500ms
```

### Combining Observables

```python
from observant import Observable

# Create observables for first and last name
first_name = Observable("Ada")
last_name = Observable("Lovelace")

# Create a derived observable for the full name
full_name = Observable(f"{first_name.get()} {last_name.get()}")

# Update full_name when either component changes
def update_full_name(*args):
    full_name.set(f"{first_name.get()} {last_name.get()}")

first_name.on_change(update_full_name)
last_name.on_change(update_full_name)

# Test it
first_name.set("Grace")  # full_name becomes "Grace Lovelace"
last_name.set("Hopper")  # full_name becomes "Grace Hopper"
```

## Implementation Details

The `Observable` class implements the `IObservable` interface, which is defined in `observant.interfaces.observable`. This interface ensures that all observable types in the library have a consistent API.

For more advanced use cases, consider using `ObservableProxy` which can automatically create observables for all fields in a data object.

## API Documentation

::: observant.observable.Observable
