# Advanced Usage Examples

This page provides examples of more advanced patterns and use cases for Observant.py.

## Model-View-ViewModel (MVVM) Pattern

Using `ObservableProxy` to implement the MVVM pattern:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List, Optional

# Model
@dataclass
class TodoItem:
    id: int
    text: str
    completed: bool

@dataclass
class TodoListModel:
    items: List[TodoItem]
    next_id: int = 1

# ViewModel
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
        
        # Filter state
        self.filter_proxy = ObservableProxy({"filter": "all"})
        self.filter = self.filter_proxy.observable(str, "filter")
        
        # Register filtered items computed property
        self.proxy.register_computed(
            "filtered_items",
            lambda: [
                item for item in self.items
                if self.filter.get() == "all"
                or (self.filter.get() == "active" and not item.completed)
                or (self.filter.get() == "completed" and item.completed)
            ],
            ["items"]
        )
        
        # Listen for filter changes to update filtered items
        self.filter.on_change(lambda _: self.proxy.computed(list, "filtered_items").get())
    
    def add_item(self, text: str):
        """Add a new todo item."""
        next_id = self.proxy.observable(int, "next_id").get()
        self.items.append(TodoItem(id=next_id, text=text, completed=False))
        self.proxy.observable(int, "next_id").set(next_id + 1)
    
    def remove_item(self, item_id: int):
        """Remove a todo item by ID."""
        index = next((i for i, item in enumerate(self.items) if item.id == item_id), -1)
        if index >= 0:
            self.items.pop(index)
    
    def toggle_item(self, item_id: int):
        """Toggle the completed state of a todo item."""
        item = next((item for item in self.items if item.id == item_id), None)
        if item:
            item_proxy = ObservableProxy(item)
            completed_obs = item_proxy.observable(bool, "completed")
            completed_obs.set(not completed_obs.get())
            item_proxy.save_to(item)
    
    def clear_completed(self):
        """Remove all completed items."""
        active_items = [item for item in self.items if not item.completed]
        self.items.clear()
        self.items.extend(active_items)
    
    def toggle_all(self):
        """Toggle the completed state of all items."""
        target_state = not self.proxy.computed(bool, "all_completed").get()
        for item in self.items:
            item_proxy = ObservableProxy(item)
            item_proxy.observable(bool, "completed").set(target_state)
            item_proxy.save_to(item)
    
    def set_filter(self, filter_value: str):
        """Set the current filter."""
        if filter_value in ["all", "active", "completed"]:
            self.filter.set(filter_value)
    
    def save(self):
        """Save changes back to the model."""
        self.proxy.save_to(self.model)

# View (pseudocode)
class TodoListView:
    def __init__(self, view_model: TodoListViewModel):
        self.view_model = view_model
        
        # Listen for changes to the filtered items
        self.view_model.proxy.computed(list, "filtered_items").on_change(self.render_items)
        
        # Listen for changes to the counts
        self.view_model.proxy.computed(int, "active_count").on_change(self.render_counts)
        self.view_model.proxy.computed(int, "completed_count").on_change(self.render_counts)
        
        # Listen for changes to the filter
        self.view_model.filter.on_change(self.update_filter_buttons)
    
    def render_items(self, items):
        print(f"Rendering {len(items)} items:")
        for item in items:
            print(f"  {'[x]' if item.completed else '[ ]'} {item.text}")
    
    def render_counts(self, _):
        active_count = self.view_model.proxy.computed(int, "active_count").get()
        completed_count = self.view_model.proxy.computed(int, "completed_count").get()
        print(f"Counts: {active_count} active, {completed_count} completed")
    
    def update_filter_buttons(self, filter_value):
        print(f"Filter changed to: {filter_value}")
    
    def handle_add_item(self, text):
        self.view_model.add_item(text)
    
    def handle_toggle_item(self, item_id):
        self.view_model.toggle_item(item_id)
    
    def handle_remove_item(self, item_id):
        self.view_model.remove_item(item_id)
    
    def handle_clear_completed(self):
        self.view_model.clear_completed()
    
    def handle_toggle_all(self):
        self.view_model.toggle_all()
    
    def handle_filter_change(self, filter_value):
        self.view_model.set_filter(filter_value)

# Usage
model = TodoListModel(items=[])
view_model = TodoListViewModel(model)
view = TodoListView(view_model)

# Add some items
view.handle_add_item("Learn Python")
view.handle_add_item("Learn Observant.py")
view.handle_add_item("Build an app")

# Toggle an item
view.handle_toggle_item(1)  # Mark "Learn Python" as completed

# Change the filter
view.handle_filter_change("active")
view.handle_filter_change("all")

# Save changes back to the model
view_model.save()
```

## Nested Observable Proxies

Using nested `ObservableProxy` instances to work with complex object hierarchies:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Address:
    street: str
    city: str
    state: str
    zip_code: str

@dataclass
class Contact:
    name: str
    email: str
    phone: str
    address: Address

@dataclass
class User:
    username: str
    contacts: List[Contact]
    preferences: Dict[str, str]

# Create a user with nested objects
user = User(
    username="alice",
    contacts=[
        Contact(
            name="Bob",
            email="bob@example.com",
            phone="555-1234",
            address=Address(
                street="123 Main St",
                city="Anytown",
                state="CA",
                zip_code="12345"
            )
        )
    ],
    preferences={"theme": "dark", "notifications": "on"}
)

# Create a proxy for the user
user_proxy = ObservableProxy(user)

# Access the contacts list
contacts = user_proxy.observable_list(Contact, "contacts")

# Get the first contact
contact = contacts[0]

# Create a proxy for the contact
contact_proxy = ObservableProxy(contact)

# Access the address
address_obs = contact_proxy.observable(Address, "address")

# Get the current address
address = address_obs.get()

# Create a proxy for the address
address_proxy = ObservableProxy(address)

# Update the address
address_proxy.observable(str, "street").set("456 Oak Ave")
address_proxy.observable(str, "city").set("Othertown")

# Save the address changes back to the address object
address_proxy.save_to(address)

# Save the contact changes back to the contact object
contact_proxy.save_to(contact)

# Save the user changes back to the user object
user_proxy.save_to(user)

print(user.contacts[0].address.street)  # Prints: 456 Oak Ave
print(user.contacts[0].address.city)  # Prints: Othertown
```

## Dependency Injection with Observables

Using observables with dependency injection to create loosely coupled components:

```python
from observant import Observable, ObservableList
from typing import List, Protocol, Optional

# Define protocols for services
class IUserService(Protocol):
    def get_current_user(self) -> str: ...
    def set_current_user(self, username: str) -> None: ...

class IMessageService(Protocol):
    def get_messages(self, username: str) -> List[str]: ...
    def send_message(self, username: str, message: str) -> None: ...

# Implement services
class UserService:
    def __init__(self):
        self.current_user = Observable("")
    
    def get_current_user(self) -> str:
        return self.current_user.get()
    
    def set_current_user(self, username: str) -> None:
        self.current_user.set(username)

class MessageService:
    def __init__(self):
        self.messages = {}
    
    def get_messages(self, username: str) -> List[str]:
        return self.messages.get(username, [])
    
    def send_message(self, username: str, message: str) -> None:
        if username not in self.messages:
            self.messages[username] = []
        self.messages[username].append(message)

# Create a service container
class ServiceContainer:
    def __init__(self):
        self.user_service = UserService()
        self.message_service = MessageService()

# Create components that use the services
class UserComponent:
    def __init__(self, user_service: IUserService):
        self.user_service = user_service
        self.current_user = self.user_service.current_user
        
        # Listen for changes to the current user
        self.current_user.on_change(self.on_user_changed)
    
    def on_user_changed(self, username):
        if username:
            print(f"User changed to: {username}")
        else:
            print("User logged out")
    
    def login(self, username: str):
        self.user_service.set_current_user(username)
    
    def logout(self):
        self.user_service.set_current_user("")

class MessageComponent:
    def __init__(self, user_service: IUserService, message_service: IMessageService):
        self.user_service = user_service
        self.message_service = message_service
        self.messages = ObservableList([])
        
        # Listen for changes to the current user
        self.user_service.current_user.on_change(self.load_messages)
    
    def load_messages(self, username):
        if username:
            # Load messages for the current user
            messages = self.message_service.get_messages(username)
            self.messages.clear()
            self.messages.extend(messages)
        else:
            # Clear messages when no user is logged in
            self.messages.clear()
    
    def send_message(self, message: str):
        username = self.user_service.get_current_user()
        if username:
            self.message_service.send_message(username, message)
            self.load_messages(username)

# Usage
container = ServiceContainer()
user_component = UserComponent(container.user_service)
message_component = MessageComponent(container.user_service, container.message_service)

# Listen for changes to the messages
message_component.messages.on_change(
    lambda change: print(f"Messages changed: {message_component.messages}")
)

# Login as Alice
user_component.login("alice")  # Prints: User changed to: alice

# Send some messages
message_component.send_message("Hello, world!")
message_component.send_message("How are you?")
# Prints: Messages changed: ['Hello, world!', 'How are you?']

# Login as Bob
user_component.login("bob")  # Prints: User changed to: bob
# Prints: Messages changed: []

# Send a message as Bob
message_component.send_message("Hi there!")
# Prints: Messages changed: ['Hi there!']

# Login back as Alice
user_component.login("alice")
# Prints: Messages changed: ['Hello, world!', 'How are you?']

# Logout
user_component.logout()  # Prints: User logged out
# Prints: Messages changed: []
```

## State Management with Undo/Redo

Using `ObservableProxy` with undo/redo to implement a document editor:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List, Dict, Optional
import time

@dataclass
class TextBlock:
    id: int
    content: str
    style: Dict[str, str]

@dataclass
class Document:
    title: str
    blocks: List[TextBlock]
    metadata: Dict[str, str]

class DocumentEditor:
    def __init__(self, document: Document):
        self.document = document
        self.proxy = ObservableProxy(document, undo=True, undo_debounce_ms=500)
        
        # Get observables
        self.title = self.proxy.observable(str, "title")
        self.blocks = self.proxy.observable_list(TextBlock, "blocks")
        self.metadata = self.proxy.observable_dict((str, str), "metadata")
        
        # Track history
        self.history = []
        self.title.on_change(lambda _: self._add_history_entry("title"))
        self.blocks.on_change(lambda _: self._add_history_entry("blocks"))
        self.metadata.on_change(lambda _: self._add_history_entry("metadata"))
    
    def _add_history_entry(self, field_name):
        self.history.append({
            "field": field_name,
            "timestamp": time.time(),
            "can_undo": self.proxy.can_undo(field_name),
            "can_redo": self.proxy.can_redo(field_name)
        })
    
    def set_title(self, title: str):
        """Set the document title."""
        self.title.set(title)
    
    def add_block(self, content: str, style: Dict[str, str] = None):
        """Add a new text block."""
        block_id = len(self.blocks) + 1
        self.blocks.append(TextBlock(
            id=block_id,
            content=content,
            style=style or {}
        ))
    
    def update_block(self, block_id: int, content: Optional[str] = None, style: Optional[Dict[str, str]] = None):
        """Update a text block."""
        block = next((b for b in self.blocks if b.id == block_id), None)
        if block:
            block_proxy = ObservableProxy(block, undo=True)
            
            if content is not None:
                block_proxy.observable(str, "content").set(content)
            
            if style is not None:
                block_style = block_proxy.observable_dict((str, str), "style")
                for key, value in style.items():
                    block_style[key] = value
            
            block_proxy.save_to(block)
    
    def remove_block(self, block_id: int):
        """Remove a text block."""
        index = next((i for i, b in enumerate(self.blocks) if b.id == block_id), -1)
        if index >= 0:
            self.blocks.pop(index)
    
    def set_metadata(self, key: str, value: str):
        """Set a metadata value."""
        self.metadata[key] = value
    
    def undo(self, field_name: str):
        """Undo changes to a field."""
        if self.proxy.can_undo(field_name):
            self.proxy.undo(field_name)
            return True
        return False
    
    def redo(self, field_name: str):
        """Redo changes to a field."""
        if self.proxy.can_redo(field_name):
            self.proxy.redo(field_name)
            return True
        return False
    
    def save(self):
        """Save changes back to the document."""
        self.proxy.save_to(self.document)
        return self.document

# Usage
doc = Document(
    title="Untitled Document",
    blocks=[],
    metadata={"author": "Anonymous", "created": "2023-01-01"}
)

editor = DocumentEditor(doc)

# Set the title
editor.set_title("My Document")

# Add some blocks
editor.add_block("Introduction", {"font-weight": "bold"})
editor.add_block("This is a sample document created with Observant.py.")
editor.add_block("Conclusion", {"font-weight": "bold"})

# Update a block
editor.update_block(2, content="This is a sample document created with Observant.py. It demonstrates the use of ObservableProxy with undo/redo functionality.")

# Set metadata
editor.set_metadata("author", "Alice")
editor.set_metadata("modified", "2023-01-02")

# Undo the last metadata change
editor.undo("metadata")

# Redo the metadata change
editor.redo("metadata")

# Save the document
saved_doc = editor.save()

print(f"Title: {saved_doc.title}")
print(f"Blocks: {len(saved_doc.blocks)}")
for block in saved_doc.blocks:
    print(f"  {block.id}: {block.content} {block.style}")
print(f"Metadata: {saved_doc.metadata}")
print(f"History: {len(editor.history)} entries")
```

## Reactive Data Processing Pipeline

Using observables to create a reactive data processing pipeline:

```python
from observant import Observable, ObservableList
from typing import List, Dict, Any, Callable
import time
import random

# Define a data source
class DataSource:
    def __init__(self, interval_ms: int = 1000):
        self.data = ObservableList([])
        self.interval_ms = interval_ms
        self.running = False
    
    def start(self):
        """Start generating data."""
        self.running = True
        self._generate_data()
    
    def stop(self):
        """Stop generating data."""
        self.running = False
    
    def _generate_data(self):
        """Generate a random data point."""
        if not self.running:
            return
        
        # Generate a random data point
        data_point = {
            "timestamp": time.time(),
            "value": random.random() * 100
        }
        
        # Add it to the list
        self.data.append(data_point)
        
        # Schedule the next data point
        time.sleep(self.interval_ms / 1000)
        self._generate_data()

# Define a data processor
class DataProcessor:
    def __init__(self, data_source: DataSource, window_size: int = 10):
        self.data_source = data_source
        self.window_size = window_size
        self.processed_data = Observable([])
        
        # Listen for changes to the data source
        self.data_source.data.on_change(self._process_data)
    
    def _process_data(self, _):
        """Process the data when it changes."""
        data = self.data_source.data[-self.window_size:] if len(self.data_source.data) > 0 else []
        
        if not data:
            self.processed_data.set([])
            return
        
        # Calculate statistics
        values = [d["value"] for d in data]
        result = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "timestamp": time.time()
        }
        
        # Update the processed data
        current = self.processed_data.get()
        self.processed_data.set(current + [result])

# Define a data visualizer
class DataVisualizer:
    def __init__(self, data_processor: DataProcessor):
        self.data_processor = data_processor
        
        # Listen for changes to the processed data
        self.data_processor.processed_data.on_change(self._update_visualization)
    
    def _update_visualization(self, data):
        """Update the visualization when the data changes."""
        if not data:
            print("No data to visualize")
            return
        
        # Get the latest data point
        latest = data[-1]
        
        # Print a simple visualization
        print(f"Data point {latest['count']}:")
        print(f"  Min: {latest['min']:.2f}")
        print(f"  Max: {latest['max']:.2f}")
        print(f"  Avg: {latest['avg']:.2f}")
        print(f"  {'=' * int(latest['avg'] / 5)}")

# Define an alert manager
class AlertManager:
    def __init__(self, data_processor: DataProcessor, threshold: float = 80):
        self.data_processor = data_processor
        self.threshold = threshold
        self.alerts = ObservableList([])
        
        # Listen for changes to the processed data
        self.data_processor.processed_data.on_change(self._check_alerts)
    
    def _check_alerts(self, data):
        """Check for alerts when the data changes."""
        if not data:
            return
        
        # Get the latest data point
        latest = data[-1]
        
        # Check if the average exceeds the threshold
        if latest["avg"] > self.threshold:
            alert = {
                "timestamp": time.time(),
                "message": f"Average value {latest['avg']:.2f} exceeds threshold {self.threshold}",
                "level": "warning"
            }
            self.alerts.append(alert)
            print(f"ALERT: {alert['message']}")

# Usage
data_source = DataSource(interval_ms=500)
data_processor = DataProcessor(data_source, window_size=5)
data_visualizer = DataVisualizer(data_processor)
alert_manager = AlertManager(data_processor, threshold=80)

# Start generating data
data_source.start()

# Let it run for a few seconds
time.sleep(5)

# Stop generating data
data_source.stop()

print(f"Generated {len(data_source.data)} data points")
print(f"Processed {len(data_processor.processed_data.get())} data points")
print(f"Generated {len(alert_manager.alerts)} alerts")
```

## Next Steps

These examples demonstrate some of the more advanced patterns and use cases for Observant.py. For more information, see the [API Reference](../api_reference.md).
