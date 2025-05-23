# Syncing & Dirty State

`ObservableProxy` provides features for tracking which fields have been modified (dirty state) and synchronizing changes back to the original object. This page explains how to use these features.

## Dirty State Tracking

When you modify a field in an `ObservableProxy`, it keeps track of which fields have been changed. You can check if a field is dirty (has been modified) using the `is_dirty()` method.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

# Create a user
user = User(name="Ada", age=36)

# Create a proxy
proxy = ObservableProxy(user)

# Check if the proxy is dirty
print(proxy.is_dirty())  # Prints: False

# Modify a field
proxy.observable(str, "name").set("Grace")

# Check if the proxy is dirty
print(proxy.is_dirty())  # Prints: True

# Check if a specific field is dirty
print(proxy.is_dirty("name"))  # Prints: True
print(proxy.is_dirty("age"))  # Prints: False
```

### Dirty State for Collections

Dirty state tracking also works for list and dictionary fields:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class User:
    name: str
    friends: List[str]
    preferences: Dict[str, str]

# Create a user
user = User(
    name="Ada",
    friends=["Charles", "Grace"],
    preferences={"theme": "dark"}
)

# Create a proxy
proxy = ObservableProxy(user)

# Modify a list field
friends = proxy.observable_list(str, "friends")
friends.append("Alan")

# Check if the list field is dirty
print(proxy.is_dirty("friends"))  # Prints: True

# Modify a dictionary field
prefs = proxy.observable_dict((str, str), "preferences")
prefs["notifications"] = "on"

# Check if the dictionary field is dirty
print(proxy.is_dirty("preferences"))  # Prints: True
```

### Dirty State Observable

You can also get an observable that tracks the dirty state of the proxy or a specific field:

```python
# Get an observable for the dirty state of the entire proxy
is_dirty = proxy.dirty()
is_dirty.on_change(lambda dirty: print(f"Proxy is {'dirty' if dirty else 'clean'}"))

# Get an observable for the dirty state of a specific field
name_dirty = proxy.dirty_for("name")
name_dirty.on_change(lambda dirty: print(f"Name is {'dirty' if dirty else 'clean'}"))

# Modify a field
proxy.observable(str, "name").set("Grace")  # Prints: Name is dirty, Proxy is dirty
```

## Saving Changes

You can save the changes made to the proxy back to the original object using the `save_to()` method:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

# Create a user
user = User(name="Ada", age=36)

# Create a proxy
proxy = ObservableProxy(user)

# Modify a field
proxy.observable(str, "name").set("Grace")

# Save changes back to the original object
proxy.save_to(user)

print(user)  # Prints: User(name='Grace', age=36)

# The proxy is no longer dirty after saving
print(proxy.is_dirty())  # Prints: False
```

You can also save changes to a different object:

```python
# Create a new user
new_user = User(name="", age=0)

# Save changes to the new user
proxy.save_to(new_user)

print(new_user)  # Prints: User(name='Grace', age=36)
```

## Automatic Syncing

You can enable automatic syncing when creating the proxy. When sync is enabled, changes are immediately synced back to the original object:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

# Create a user
user = User(name="Ada", age=36)

# Create a proxy with sync enabled
proxy = ObservableProxy(user, sync=True)

# Modify a field
proxy.observable(str, "name").set("Grace")

# The change is immediately synced to the original object
print(user)  # Prints: User(name='Grace', age=36)
```

!!! note
    Even with sync enabled, the proxy still tracks dirty state. The dirty state is reset when you call `save_to()` or when you create a new proxy.

## Resetting Changes

You can reset changes made to the proxy using the `reset()` method:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

# Create a user
user = User(name="Ada", age=36)

# Create a proxy
proxy = ObservableProxy(user)

# Modify a field
proxy.observable(str, "name").set("Grace")

# Reset changes
proxy.reset()

# The field is back to its original value
print(proxy.observable(str, "name").get())  # Prints: Ada

# The proxy is no longer dirty
print(proxy.is_dirty())  # Prints: False
```

You can also reset a specific field:

```python
# Modify multiple fields
proxy.observable(str, "name").set("Grace")
proxy.observable(int, "age").set(52)

# Reset only the name field
proxy.reset("name")

# The name field is back to its original value
print(proxy.observable(str, "name").get())  # Prints: Ada

# The age field is still modified
print(proxy.observable(int, "age").get())  # Prints: 52

# The proxy is still dirty because the age field is modified
print(proxy.is_dirty())  # Prints: True
print(proxy.is_dirty("name"))  # Prints: False
print(proxy.is_dirty("age"))  # Prints: True
```

## Dirty State with Validation

Dirty state tracking works with validation. You can check if a field is both dirty and valid:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    username: str
    email: str

# Create a user
user = User(username="ada", email="ada@example.com")

# Create a proxy
proxy = ObservableProxy(user)

# Add validators
proxy.add_validator("username", lambda v: "Username is required" if not v else None)
proxy.add_validator("email", lambda v: "Email is required" if not v else None)
proxy.add_validator("email", lambda v: "Invalid email" if v and "@" not in v else None)

# Modify a field with a valid value
proxy.observable(str, "username").set("grace")

# The field is dirty and valid
print(proxy.is_dirty("username"))  # Prints: True
print(proxy.validation_for("username").get())  # Prints: []

# Modify a field with an invalid value
proxy.observable(str, "email").set("grace")

# The field is dirty and invalid
print(proxy.is_dirty("email"))  # Prints: True
print(proxy.validation_for("email").get())  # Prints: ['Invalid email']

# Check if the entire proxy is valid
print(proxy.is_valid().get())  # Prints: False
```

## Dirty State with Undo/Redo

Dirty state tracking works with undo/redo. When you undo a change, the field is no longer dirty if it's back to its original value:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

# Create a user
user = User(name="Ada", age=36)

# Create a proxy with undo enabled
proxy = ObservableProxy(user, undo=True)

# Modify a field
proxy.observable(str, "name").set("Grace")

# The field is dirty
print(proxy.is_dirty("name"))  # Prints: True

# Undo the change
proxy.undo("name")

# The field is no longer dirty
print(proxy.is_dirty("name"))  # Prints: False

# Redo the change
proxy.redo("name")

# The field is dirty again
print(proxy.is_dirty("name"))  # Prints: True
```

## Advanced Syncing Patterns

### Form Editing

You can use dirty state tracking to implement form editing with save and cancel buttons:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class UserProfile:
    username: str
    email: str
    bio: str

class ProfileEditor:
    def __init__(self, profile: UserProfile):
        self.original_profile = profile
        self.proxy = ObservableProxy(profile)
        
        # Add validators
        self.proxy.add_validator("username", lambda v: "Username is required" if not v else None)
        self.proxy.add_validator("email", lambda v: "Email is required" if not v else None)
        self.proxy.add_validator("email", lambda v: "Invalid email" if v and "@" not in v else None)
        
        # Track dirty state
        self.is_dirty = self.proxy.dirty()
        self.is_valid = self.proxy.is_valid()
        
        # Update save button state when dirty or valid state changes
        self.is_dirty.on_change(self._update_save_button)
        self.is_valid.on_change(self._update_save_button)
    
    def _update_save_button(self, _):
        # Enable save button only if the form is dirty and valid
        save_enabled = self.is_dirty.get() and self.is_valid.get()
        print(f"Save button {'enabled' if save_enabled else 'disabled'}")
    
    def save(self):
        """Save changes to the original profile."""
        if self.is_dirty.get() and self.is_valid.get():
            self.proxy.save_to(self.original_profile)
            print("Changes saved")
            return True
        return False
    
    def cancel(self):
        """Cancel changes and reset the form."""
        self.proxy.reset()
        print("Changes cancelled")
    
    def get_field(self, field_name: str, field_type: type):
        """Get an observable for a field."""
        return self.proxy.observable(field_type, field_name)

# Usage
profile = UserProfile(username="ada", email="ada@example.com", bio="")
editor = ProfileEditor(profile)

# Modify fields
editor.get_field("username", str).set("grace")
editor.get_field("email", str).set("grace@example.com")
editor.get_field("bio", str).set("Computer scientist")

# Save changes
editor.save()

# Check the original profile
print(profile)  # Prints: UserProfile(username='grace', email='grace@example.com', bio='Computer scientist')
```

### Dirty State with Collections

You can use dirty state tracking with collections to implement complex editing scenarios:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List

@dataclass
class TodoItem:
    text: str
    completed: bool

@dataclass
class TodoList:
    items: List[TodoItem]

class TodoListEditor:
    def __init__(self, todo_list: TodoList):
        self.original_list = todo_list
        self.proxy = ObservableProxy(todo_list)
        
        # Get the observable list
        self.items = self.proxy.observable_list(TodoItem, "items")
        
        # Track dirty state
        self.is_dirty = self.proxy.dirty()
        self.is_dirty.on_change(lambda dirty: print(f"Todo list is {'dirty' if dirty else 'clean'}"))
    
    def add_item(self, text: str):
        """Add a new item to the list."""
        self.items.append(TodoItem(text=text, completed=False))
    
    def toggle_item(self, index: int):
        """Toggle the completed state of an item."""
        item = self.items[index]
        item_proxy = ObservableProxy(item)
        completed = item_proxy.observable(bool, "completed")
        completed.set(not completed.get())
        item_proxy.save_to(item)
    
    def remove_item(self, index: int):
        """Remove an item from the list."""
        self.items.pop(index)
    
    def save(self):
        """Save changes to the original list."""
        if self.is_dirty.get():
            self.proxy.save_to(self.original_list)
            print("Changes saved")
            return True
        return False
    
    def cancel(self):
        """Cancel changes and reset the list."""
        self.proxy.reset()
        print("Changes cancelled")

# Usage
todo_list = TodoList(items=[
    TodoItem(text="Buy groceries", completed=False),
    TodoItem(text="Clean house", completed=True)
])
editor = TodoListEditor(todo_list)

# Modify the list
editor.add_item("Write code")
editor.toggle_item(0)  # Toggle "Buy groceries" to completed
editor.remove_item(1)  # Remove "Clean house"

# Save changes
editor.save()

# Check the original list
print(todo_list)  # Prints: TodoList(items=[TodoItem(text='Buy groceries', completed=True), TodoItem(text='Write code', completed=False)])
```

## API Reference

### Dirty State Methods

#### `is_dirty()`

```python
def is_dirty(self, attr: str | None = None) -> bool
```

Checks if the proxy or a specific field is dirty.

- `attr`: The field name to check. If None, checks if any field is dirty.

#### `dirty()`

```python
def dirty(self) -> IObservable[bool]
```

Gets an observable that indicates whether any field is dirty.

#### `dirty_for()`

```python
def dirty_for(self, attr: str) -> IObservable[bool]
```

Gets an observable that indicates whether a specific field is dirty.

- `attr`: The field name to check.

### Syncing Methods

#### `save_to()`

```python
def save_to(self, obj: T) -> None
```

Saves changes to an object.

- `obj`: The object to save changes to.

#### `reset()`

```python
def reset(self, attr: str | None = None) -> None
```

Resets changes made to the proxy.

- `attr`: The field name to reset. If None, resets all fields.

### Constructor Options

```python
ObservableProxy(
    obj: T,
    *,
    sync: bool = False,
)
```

- `sync`: If True, changes are immediately synced back to the original object.
