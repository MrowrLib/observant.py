# ObservableProxy

The `ObservableProxy` class is the most powerful component of Observant.py. It wraps an existing object and exposes its fields as observables, allowing you to track changes, validate data, implement undo/redo, create computed properties, and synchronize state.

## Basic Usage

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

## Key Features

`ObservableProxy` provides several powerful features:

1. **Type-safe field access**: Get strongly-typed observables for each field
2. **Validation**: Add validators to ensure data integrity
3. **Undo/Redo**: Track and revert changes
4. **Computed Properties**: Create properties that automatically update
5. **Dirty State Tracking**: Know which fields have been modified
6. **Synchronization**: Optionally sync changes back to the original object

## Constructor

```python
ObservableProxy(
    obj: T,
    *,
    sync: bool = False,
    undo: bool = False,
    undo_max: int | None = None,
    undo_debounce_ms: int | None = None,
)
```

- `obj`: The object to proxy
- `sync`: If True, changes are immediately synced back to the original object
- `undo`: If True, enables undo/redo functionality for all fields
- `undo_max`: Maximum number of undo steps to store (None means unlimited)
- `undo_debounce_ms`: Time window in milliseconds to group changes (None means no debouncing)

## Core Methods

### Accessing Fields

```python
# Get an observable for a scalar field
name_obs = proxy.observable(str, "name")

# Get an observable list for a list field
friends_obs = proxy.observable_list(str, "friends")

# Get an observable dict for a dict field
prefs_obs = proxy.observable_dict((str, str), "preferences")
```

### Saving Changes

```python
# Save all changes back to the original object
proxy.save_to(user)

# Or create a new object with the changes
new_user = User(name="", age=0, preferences={}, friends=[])
proxy.save_to(new_user)
```

### Updating Multiple Fields

```python
# Update multiple scalar fields at once
proxy.update(name="Grace", age=52)

# Load values from a dictionary
proxy.load_dict({"name": "Grace", "age": 52})
```

### Accessing the Original Object

```python
# Get the original object being proxied
original = proxy.get()
```

## Examples

### Form Binding

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class UserProfile:
    username: str
    email: str
    bio: str
    tags: List[str]
    settings: Dict[str, bool]

# Create a model
profile = UserProfile(
    username="",
    email="",
    bio="",
    tags=[],
    settings={"public": True, "notifications": True}
)

# Create a proxy
proxy = ObservableProxy(profile)

# Add validation
proxy.add_validator("username", lambda v: "Username is required" if not v else None)
proxy.add_validator("username", lambda v: "Username too short" if len(v) < 3 else None)
proxy.add_validator("email", lambda v: "Email is required" if not v else None)
proxy.add_validator("email", lambda v: "Invalid email" if v and "@" not in v else None)

# Bind to UI elements (pseudocode)
def bind_input(field_name, input_element):
    # Get the observable
    obs = proxy.observable(str, field_name)
    
    # Update the observable when the input changes
    input_element.on_change(lambda value: obs.set(value))
    
    # Update the input when the observable changes
    obs.on_change(lambda value: input_element.set_value(value))
    
    # Show validation errors
    proxy.validation_for(field_name).on_change(
        lambda errors: input_element.show_errors(errors)
    )

# Bind to form elements
bind_input("username", username_input)
bind_input("email", email_input)
bind_input("bio", bio_textarea)

# Disable submit button if form is invalid
proxy.is_valid().on_change(
    lambda valid: submit_button.set_enabled(valid)
)

# Handle form submission
def on_submit():
    if proxy.is_valid().get():
        # Save changes back to the model
        proxy.save_to(profile)
        # Submit the form
        api.submit_profile(profile)
```

### Model-View-ViewModel (MVVM) Pattern

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List

@dataclass
class TodoItem:
    text: str
    completed: bool

@dataclass
class TodoListModel:
    items: List[TodoItem]

class TodoListViewModel:
    def __init__(self, model: TodoListModel):
        self.model = model
        self.proxy = ObservableProxy(model)
        
        # Get observable list of items
        self.items = self.proxy.observable_list(TodoItem, "items")
        
        # Register computed properties
        self.proxy.register_computed(
            "completed_count",
            lambda: sum(1 for item in self.items if item.completed),
            ["items"]
        )
        
        self.proxy.register_computed(
            "active_count",
            lambda: len(self.items) - self.proxy.computed(int, "completed_count").get(),
            ["items", "completed_count"]
        )
        
        self.proxy.register_computed(
            "all_completed",
            lambda: len(self.items) > 0 and self.proxy.computed(int, "completed_count").get() == len(self.items),
            ["items", "completed_count"]
        )
    
    def add_item(self, text: str):
        self.items.append(TodoItem(text=text, completed=False))
    
    def remove_item(self, index: int):
        self.items.pop(index)
    
    def toggle_item(self, index: int):
        item = self.items[index]
        item_proxy = ObservableProxy(item)
        completed_obs = item_proxy.observable(bool, "completed")
        completed_obs.set(not completed_obs.get())
        item_proxy.save_to(item)
    
    def clear_completed(self):
        # Create a new list with only active items
        active_items = [item for item in self.items if not item.completed]
        self.items.clear()
        self.items.extend(active_items)
    
    def toggle_all(self):
        target_state = not self.proxy.computed(bool, "all_completed").get()
        for item in self.items:
            item_proxy = ObservableProxy(item)
            item_proxy.observable(bool, "completed").set(target_state)
            item_proxy.save_to(item)
    
    def save(self):
        self.proxy.save_to(self.model)
```

## Next Steps

Explore the specific features of `ObservableProxy` in more detail:

- [Validation](validation.md): Add validators to ensure data integrity
- [Undo/Redo](undo.md): Track and revert changes
- [Computed Fields](computed.md): Create properties that automatically update
- [Syncing & Dirty State](sync.md): Synchronize state between models

## API Documentation

[API Reference for ObservableProxy](../../api_reference/observable_proxy.md)
