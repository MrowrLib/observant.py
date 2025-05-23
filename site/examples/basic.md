# Basic Usage Examples

This page provides examples of common patterns and use cases for Observant.py.

## Simple Counter

A basic example of using `Observable` to track a counter value:

```python
from observant import Observable

# Create a counter
counter = Observable(0)

# Register a callback to be notified when the counter changes
counter.on_change(lambda value: print(f"Counter changed to {value}"))

# Increment the counter
counter.set(counter.get() + 1)  # Prints: Counter changed to 1
counter.set(counter.get() + 1)  # Prints: Counter changed to 2
```

## Form Validation

Using `ObservableProxy` to implement form validation:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class LoginForm:
    username: str
    password: str
    remember_me: bool

# Create a form
form = LoginForm(username="", password="", remember_me=False)

# Create a proxy
proxy = ObservableProxy(form)

# Add validators
proxy.add_validator("username", lambda v: "Username is required" if not v else None)
proxy.add_validator("password", lambda v: "Password is required" if not v else None)
proxy.add_validator("password", lambda v: "Password must be at least 8 characters" if v and len(v) < 8 else None)

# Get observables for form fields
username = proxy.observable(str, "username")
password = proxy.observable(str, "password")
remember_me = proxy.observable(bool, "remember_me")

# Listen for validation errors
proxy.validation_for("username").on_change(
    lambda errors: print(f"Username errors: {errors}")
)
proxy.validation_for("password").on_change(
    lambda errors: print(f"Password errors: {errors}")
)

# Listen for overall form validity
proxy.is_valid().on_change(
    lambda valid: print(f"Form is {'valid' if valid else 'invalid'}")
)

# Update form fields
username.set("alice")  # Username errors: []
password.set("123")  # Password errors: ['Password must be at least 8 characters']
password.set("password123")  # Password errors: []
remember_me.set(True)  # Form is valid

# Check if the form is valid
if proxy.is_valid().get():
    # Save the form
    proxy.save_to(form)
    print(f"Form saved: {form}")
```

## Shopping Cart

Using `ObservableList` and `ObservableProxy` to implement a shopping cart:

```python
from observant import ObservableList, ObservableProxy
from dataclasses import dataclass
from typing import List

@dataclass
class CartItem:
    product_id: str
    name: str
    price: float
    quantity: int

@dataclass
class ShoppingCart:
    items: List[CartItem]
    coupon_code: str

# Create a shopping cart
cart = ShoppingCart(items=[], coupon_code="")

# Create a proxy
proxy = ObservableProxy(cart)

# Get the observable list of items
items = proxy.observable_list(CartItem, "items")

# Register computed properties
proxy.register_computed(
    "subtotal",
    lambda: sum(item.price * item.quantity for item in items),
    ["items"]
)

proxy.register_computed(
    "discount",
    lambda: proxy.computed(float, "subtotal").get() * 0.1 if proxy.observable(str, "coupon_code").get() == "SAVE10" else 0,
    ["subtotal", "coupon_code"]
)

proxy.register_computed(
    "total",
    lambda: proxy.computed(float, "subtotal").get() - proxy.computed(float, "discount").get(),
    ["subtotal", "discount"]
)

# Listen for changes
items.on_change(lambda _: print(f"Cart items changed"))
proxy.computed(float, "subtotal").on_change(lambda value: print(f"Subtotal: ${value:.2f}"))
proxy.computed(float, "discount").on_change(lambda value: print(f"Discount: ${value:.2f}"))
proxy.computed(float, "total").on_change(lambda value: print(f"Total: ${value:.2f}"))

# Add items to the cart
items.append(CartItem(product_id="p1", name="T-shirt", price=19.99, quantity=1))
# Cart items changed
# Subtotal: $19.99
# Discount: $0.00
# Total: $19.99

items.append(CartItem(product_id="p2", name="Jeans", price=49.99, quantity=1))
# Cart items changed
# Subtotal: $69.98
# Discount: $0.00
# Total: $69.98

# Update an item's quantity
item = items[0]
item_proxy = ObservableProxy(item)
item_proxy.observable(int, "quantity").set(2)
item_proxy.save_to(item)
# Cart items changed
# Subtotal: $89.97
# Discount: $0.00
# Total: $89.97

# Apply a coupon code
proxy.observable(str, "coupon_code").set("SAVE10")
# Discount: $8.99
# Total: $80.98
```

## Todo List

Using `ObservableList` and `ObservableProxy` to implement a todo list with filtering:

```python
from observant import ObservableList, ObservableProxy
from dataclasses import dataclass
from typing import List

@dataclass
class TodoItem:
    text: str
    completed: bool

@dataclass
class TodoList:
    items: List[TodoItem]
    filter: str  # "all", "active", or "completed"

# Create a todo list
todo_list = TodoList(items=[], filter="all")

# Create a proxy
proxy = ObservableProxy(todo_list)

# Get the observable list of items
items = proxy.observable_list(TodoItem, "items")

# Register computed properties
proxy.register_computed(
    "filtered_items",
    lambda: [
        item for item in items
        if proxy.observable(str, "filter").get() == "all"
        or (proxy.observable(str, "filter").get() == "active" and not item.completed)
        or (proxy.observable(str, "filter").get() == "completed" and item.completed)
    ],
    ["items", "filter"]
)

proxy.register_computed(
    "active_count",
    lambda: sum(1 for item in items if not item.completed),
    ["items"]
)

proxy.register_computed(
    "completed_count",
    lambda: sum(1 for item in items if item.completed),
    ["items"]
)

# Listen for changes
proxy.computed(list, "filtered_items").on_change(
    lambda items: print(f"Filtered items: {[item.text for item in items]}")
)
proxy.computed(int, "active_count").on_change(
    lambda count: print(f"Active count: {count}")
)
proxy.computed(int, "completed_count").on_change(
    lambda count: print(f"Completed count: {count}")
)

# Add items to the list
items.append(TodoItem(text="Buy groceries", completed=False))
# Filtered items: ['Buy groceries']
# Active count: 1
# Completed count: 0

items.append(TodoItem(text="Clean house", completed=False))
# Filtered items: ['Buy groceries', 'Clean house']
# Active count: 2
# Completed count: 0

items.append(TodoItem(text="Pay bills", completed=True))
# Filtered items: ['Buy groceries', 'Clean house', 'Pay bills']
# Active count: 2
# Completed count: 1

# Toggle an item's completed state
item = items[0]
item_proxy = ObservableProxy(item)
item_proxy.observable(bool, "completed").set(True)
item_proxy.save_to(item)
# Filtered items: ['Buy groceries', 'Clean house', 'Pay bills']
# Active count: 1
# Completed count: 2

# Change the filter
proxy.observable(str, "filter").set("active")
# Filtered items: ['Clean house']

proxy.observable(str, "filter").set("completed")
# Filtered items: ['Buy groceries', 'Pay bills']

proxy.observable(str, "filter").set("all")
# Filtered items: ['Buy groceries', 'Clean house', 'Pay bills']
```

## Settings Manager

Using `ObservableDict` to implement a settings manager:

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
            print(f"Settings saved to {self.filename}")
        except IOError:
            print(f"Error saving settings to {self.filename}")
    
    def reset(self):
        """Reset settings to defaults."""
        self.settings.clear()
        self.settings.update(self.defaults)
        print("Settings reset to defaults")

# Usage
settings = SettingsManager("settings.json", {
    "theme": "light",
    "font_size": 12,
    "notifications": True
})

# Access settings
current_theme = settings.settings["theme"]
print(f"Current theme: {current_theme}")

# Update settings (automatically saved to file)
settings.settings["theme"] = "dark"
settings.settings["font_size"] = 14

# Reset to defaults
settings.reset()
```

## Undo/Redo Text Editor

Using `UndoableObservable` to implement a text editor with undo/redo:

```python
from observant import UndoableObservable

class TextEditor:
    def __init__(self, initial_text: str = ""):
        self.text = UndoableObservable(initial_text, undo_debounce_ms=500)
        self.text.on_change(self._on_text_changed)
        
        # Track if we can undo/redo
        self._can_undo = False
        self._can_redo = False
        self._update_undo_redo_state()
    
    def _on_text_changed(self, text):
        print(f"Text changed: {text}")
        self._update_undo_redo_state()
    
    def _update_undo_redo_state(self):
        can_undo = self.text.can_undo()
        can_redo = self.text.can_redo()
        
        if can_undo != self._can_undo:
            self._can_undo = can_undo
            print(f"Can undo: {can_undo}")
        
        if can_redo != self._can_redo:
            self._can_redo = can_redo
            print(f"Can redo: {can_redo}")
    
    def set_text(self, text: str):
        self.text.set(text)
    
    def undo(self):
        if self.text.can_undo():
            self.text.undo()
            return True
        return False
    
    def redo(self):
        if self.text.can_redo():
            self.text.redo()
            return True
        return False
    
    def get_text(self):
        return self.text.get()

# Usage
editor = TextEditor("Hello, world!")
print(f"Initial text: {editor.get_text()}")

editor.set_text("Hello, Python!")
# Text changed: Hello, Python!
# Can undo: True

editor.set_text("Hello, Observant!")
# Text changed: Hello, Observant!

editor.undo()
# Text changed: Hello, Python!
# Can redo: True

editor.redo()
# Text changed: Hello, Observant!
# Can redo: False

print(f"Final text: {editor.get_text()}")
```

## Next Steps

For more advanced examples, see the [Advanced Patterns](advanced.md) page.
