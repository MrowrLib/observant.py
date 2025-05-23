# Undo/Redo

`ObservableProxy` provides built-in support for undo and redo operations, allowing users to track and revert changes to any field. This page explains how to use the undo/redo features.

## Enabling Undo/Redo

Undo/redo functionality is disabled by default. You can enable it globally when creating the proxy:

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

# Create a proxy with undo enabled
proxy = ObservableProxy(user, undo=True)
```

You can also configure the maximum number of undo steps and debounce time:

```python
# Create a proxy with undo enabled and custom settings
proxy = ObservableProxy(
    user,
    undo=True,
    undo_max=50,  # Store up to 50 undo steps (default is 100)
    undo_debounce_ms=500  # Group changes within 500ms (default is None)
)
```

## Basic Undo/Redo

Once undo is enabled, you can undo and redo changes to any field:

```python
# Get an observable for a field
name = proxy.observable(str, "name")

# Make some changes
name.set("Grace")
name.set("Alan")

# Undo the last change
proxy.undo("name")  # name is now "Grace"

# Redo the undone change
proxy.redo("name")  # name is now "Alan"
```

## Checking Undo/Redo Availability

You can check if undo or redo operations are available for a field:

```python
# Check if undo is available
if proxy.can_undo("name"):
    proxy.undo("name")

# Check if redo is available
if proxy.can_redo("name"):
    proxy.redo("name")
```

## Undo/Redo for Collections

Undo/redo works for list and dictionary fields as well:

### Lists

```python
# Get an observable list
friends = proxy.observable_list(str, "friends")

# Make some changes
friends.append("Alan")
friends.pop(0)  # Remove "Charles"

# Undo the last change
proxy.undo("friends")  # "Charles" is back

# Redo the undone change
proxy.redo("friends")  # "Charles" is removed again
```

### Dictionaries

```python
# Get an observable dictionary
prefs = proxy.observable_dict((str, str), "preferences")

# Make some changes
prefs["theme"] = "light"
prefs["notifications"] = "on"

# Undo the last change
proxy.undo("preferences")  # "notifications" is removed

# Redo the undone change
proxy.redo("preferences")  # "notifications" is back
```

## Configuring Undo/Redo for Specific Fields

You can configure undo/redo settings for specific fields:

```python
# Enable undo for a specific field
proxy.set_undo_config("name", enabled=True)

# Disable undo for a specific field
proxy.set_undo_config("age", enabled=False)

# Set custom undo settings for a field
proxy.set_undo_config(
    "preferences",
    enabled=True,
    undo_max=20,
    undo_debounce_ms=1000
)
```

You can also set undo configuration when getting an observable:

```python
# Get an observable with custom undo settings
name = proxy.observable(
    str,
    "name",
    undo_max=10,
    undo_debounce_ms=200
)
```

## Debouncing Changes

When debounce is enabled, changes made within the debounce window are grouped into a single undo step:

```python
# Create a proxy with debouncing
proxy = ObservableProxy(user, undo=True, undo_debounce_ms=500)

# Get an observable
name = proxy.observable(str, "name")

# Make rapid changes
name.set("Grace")
name.set("Alan")
name.set("John")  # All within 500ms

# Undo will revert all changes in one step
proxy.undo("name")  # name is back to "Ada"
```

This is particularly useful for fields that might change rapidly, such as text fields during typing.

## Undo/Redo with Validation

Undo/redo operations automatically trigger validation:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    username: str

# Create a proxy with undo enabled
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

# Check validation state
is_valid = proxy.is_valid().get()  # True
```

## Undo/Redo with Computed Fields

Computed fields are automatically updated during undo/redo operations:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    first_name: str
    last_name: str

# Create a proxy with undo enabled
user = User(first_name="Ada", last_name="Lovelace")
proxy = ObservableProxy(user, undo=True)

# Register a computed property
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
    ["first_name", "last_name"]
)

# Get observables
first_name = proxy.observable(str, "first_name")
full_name = proxy.computed(str, "full_name")

# Make a change
first_name.set("Grace")  # full_name becomes "Grace Lovelace"

# Undo the change
proxy.undo("first_name")  # full_name is automatically updated to "Ada Lovelace"
```

## Undo/Redo with Sync

When using undo/redo with sync enabled, changes are immediately synced back to the original object:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    name: str

# Create a user
user = User(name="Ada")

# Create a proxy with undo and sync enabled
proxy = ObservableProxy(user, undo=True, sync=True)

# Get an observable
name = proxy.observable(str, "name")

# Make a change
name.set("Grace")  # user.name is now "Grace"

# Undo the change
proxy.undo("name")  # user.name is now "Ada" again

# Redo the change
proxy.redo("name")  # user.name is now "Grace" again
```

!!! warning
    Using sync=True with undo=True may cause unexpected model mutations during undo/redo. Consider using sync=False and explicitly calling save_to() when needed.

## Advanced Undo/Redo Patterns

### Implementing a History Stack

You can implement a global undo/redo stack by tracking which fields have been modified:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple

@dataclass
class Document:
    title: str
    content: str
    tags: List[str]

class DocumentEditor:
    def __init__(self, document: Document):
        self.document = document
        self.proxy = ObservableProxy(document, undo=True)
        
        # Track which fields have been modified
        self.modified_fields: List[Tuple[str, int]] = []  # (field_name, timestamp)
        
        # Set up change tracking for all fields
        self._track_field("title")
        self._track_field("content")
        self._track_field("tags")
    
    def _track_field(self, field_name: str):
        # Get the appropriate observable based on field type
        if field_name == "tags":
            obs = self.proxy.observable_list(str, field_name)
        else:
            obs = self.proxy.observable(str, field_name)
        
        # Track changes
        obs.on_change(lambda _: self._on_field_changed(field_name))
    
    def _on_field_changed(self, field_name: str):
        import time
        # Add the field to the modified list with current timestamp
        self.modified_fields.append((field_name, int(time.time() * 1000)))
    
    def undo(self):
        """Undo the most recent change."""
        if not self.modified_fields:
            return False
        
        # Get the most recently modified field
        field_name, _ = self.modified_fields.pop()
        
        # Undo the change to that field
        if self.proxy.can_undo(field_name):
            self.proxy.undo(field_name)
            return True
        
        return False
    
    def save(self):
        """Save changes back to the document."""
        self.proxy.save_to(self.document)
        # Clear the modified fields list after saving
        self.modified_fields.clear()

# Usage
doc = Document(title="Draft", content="Hello world", tags=["draft"])
editor = DocumentEditor(doc)

# Make some changes
editor.proxy.observable(str, "title").set("Final")
editor.proxy.observable(str, "content").set("Hello, world!")
editor.proxy.observable_list(str, "tags").append("final")

# Undo the most recent change (to tags)
editor.undo()  # Removes "final" from tags

# Undo the next most recent change (to content)
editor.undo()  # Content is back to "Hello world"

# Save changes
editor.save()
```

### Implementing Undo/Redo Buttons

You can implement undo/redo buttons in a UI application:

```python
from observant import ObservableProxy
from dataclasses import dataclass
import tkinter as tk
from typing import Set

@dataclass
class TextDocument:
    content: str

class TextEditor:
    def __init__(self, root, document: TextDocument):
        self.document = document
        self.proxy = ObservableProxy(document, undo=True, undo_debounce_ms=500)
        
        # Create UI
        self.root = root
        self.root.title("Text Editor")
        
        # Create toolbar
        toolbar = tk.Frame(root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Create undo/redo buttons
        self.undo_button = tk.Button(toolbar, text="Undo", command=self.undo)
        self.undo_button.pack(side=tk.LEFT)
        self.redo_button = tk.Button(toolbar, text="Redo", command=self.redo)
        self.redo_button.pack(side=tk.LEFT)
        
        # Create text area
        self.text_area = tk.Text(root)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.insert(tk.END, document.content)
        
        # Bind text changes
        self.text_area.bind("<<Modified>>", self.on_text_changed)
        
        # Track if we're currently updating from the model
        self.updating_from_model = False
        
        # Update button states
        self.update_button_states()
        
        # Set up content observable
        self.content_obs = self.proxy.observable(str, "content")
        self.content_obs.on_change(self.update_text_area)
    
    def on_text_changed(self, event):
        if not self.updating_from_model:
            content = self.text_area.get("1.0", tk.END).rstrip()
            self.content_obs.set(content)
            self.update_button_states()
        self.text_area.edit_modified(False)
    
    def update_text_area(self, content):
        self.updating_from_model = True
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", content)
        self.updating_from_model = False
        self.update_button_states()
    
    def undo(self):
        if self.proxy.can_undo("content"):
            self.proxy.undo("content")
            self.update_button_states()
    
    def redo(self):
        if self.proxy.can_redo("content"):
            self.proxy.redo("content")
            self.update_button_states()
    
    def update_button_states(self):
        self.undo_button["state"] = tk.NORMAL if self.proxy.can_undo("content") else tk.DISABLED
        self.redo_button["state"] = tk.NORMAL if self.proxy.can_redo("content") else tk.DISABLED
    
    def save(self):
        self.proxy.save_to(self.document)

# Usage
if __name__ == "__main__":
    root = tk.Tk()
    doc = TextDocument(content="Hello, world!")
    editor = TextEditor(root, doc)
    root.mainloop()
```

## API Reference

### Constructor Options

```python
ObservableProxy(
    obj: T,
    *,
    undo: bool = False,
    undo_max: int | None = None,
    undo_debounce_ms: int | None = None,
)
```

- `undo`: If True, enables undo/redo functionality for all fields
- `undo_max`: Maximum number of undo steps to store (None means unlimited)
- `undo_debounce_ms`: Time window in milliseconds to group changes (None means no debouncing)

### Undo/Redo Methods

#### `undo()`

```python
def undo(self, attr: str) -> None
```

Undoes the most recent change to a field.

- `attr`: The field name to undo changes for

#### `redo()`

```python
def redo(self, attr: str) -> None
```

Redoes the most recently undone change to a field.

- `attr`: The field name to redo changes for

#### `can_undo()`

```python
def can_undo(self, attr: str) -> bool
```

Checks if there are changes that can be undone for a field.

- `attr`: The field name to check

#### `can_redo()`

```python
def can_redo(self, attr: str) -> bool
```

Checks if there are changes that can be redone for a field.

- `attr`: The field name to check

#### `set_undo_config()`

```python
def set_undo_config(
    self,
    attr: str,
    *,
    enabled: bool | None = None,
    undo_max: int | None = None,
    undo_debounce_ms: int | None = None,
) -> None
```

Sets the undo configuration for a specific field.

- `attr`: The field name to configure
- `enabled`: Whether undo/redo functionality is enabled for this field
- `undo_max`: Maximum number of undo steps to store
- `undo_debounce_ms`: Time window in milliseconds to group changes
