# Computed Fields

`ObservableProxy` allows you to define computed fields that automatically update based on changes to other fields. This page explains how to use computed fields.

## Basic Usage

Computed fields are properties that are derived from other fields. They are recalculated automatically when their dependencies change.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    first_name: str
    last_name: str

# Create a user
user = User(first_name="Ada", last_name="Lovelace")

# Create a proxy
proxy = ObservableProxy(user)

# Register a computed property for the full name
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
    ["first_name", "last_name"]
)

# Access the computed property
full_name = proxy.computed(str, "full_name")
print(full_name.get())  # Prints: Ada Lovelace

# Update a dependency
proxy.observable(str, "first_name").set("Grace")
print(full_name.get())  # Prints: Grace Lovelace
```

## Registering Computed Fields

To create a computed field, you need to register it with the proxy:

```python
proxy.register_computed(
    "field_name",     # Name of the computed field
    compute_function, # Function that computes the value
    dependencies      # List of field names that the computed field depends on
)
```

The compute function should return the computed value. It can access the values of other fields using the proxy's `observable()`, `observable_list()`, `observable_dict()`, or `computed()` methods.

## Accessing Computed Fields

You can access a computed field using the `computed()` method:

```python
computed_field = proxy.computed(field_type, "field_name")
```

The returned object is an `Observable` that you can use like any other observable:

```python
# Get the current value
value = computed_field.get()

# Listen for changes
computed_field.on_change(lambda value: print(f"Computed field changed to {value}"))
```

## Computed Field Dependencies

When you register a computed field, you specify its dependencies. The computed field will be recalculated automatically when any of its dependencies change.

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class Rectangle:
    width: float
    height: float

# Create a rectangle
rect = Rectangle(width=10.0, height=5.0)

# Create a proxy
proxy = ObservableProxy(rect)

# Register computed properties
proxy.register_computed(
    "area",
    lambda: proxy.observable(float, "width").get() * proxy.observable(float, "height").get(),
    ["width", "height"]
)

proxy.register_computed(
    "perimeter",
    lambda: 2 * (proxy.observable(float, "width").get() + proxy.observable(float, "height").get()),
    ["width", "height"]
)

# Access computed properties
area = proxy.computed(float, "area")
perimeter = proxy.computed(float, "perimeter")

print(f"Area: {area.get()}")  # Prints: Area: 50.0
print(f"Perimeter: {perimeter.get()}")  # Prints: Perimeter: 30.0

# Update a dependency
proxy.observable(float, "width").set(20.0)

print(f"Area: {area.get()}")  # Prints: Area: 100.0
print(f"Perimeter: {perimeter.get()}")  # Prints: Perimeter: 50.0
```

## Computed Fields with Collections

Computed fields can also depend on list and dictionary fields:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List

@dataclass
class ShoppingCart:
    items: List[float]

# Create a shopping cart
cart = ShoppingCart(items=[10.0, 20.0, 5.0])

# Create a proxy
proxy = ObservableProxy(cart)

# Register computed properties
proxy.register_computed(
    "total",
    lambda: sum(proxy.observable_list(float, "items")),
    ["items"]
)

proxy.register_computed(
    "item_count",
    lambda: len(proxy.observable_list(float, "items")),
    ["items"]
)

proxy.register_computed(
    "average_price",
    lambda: proxy.computed(float, "total").get() / proxy.computed(int, "item_count").get() if proxy.computed(int, "item_count").get() > 0 else 0.0,
    ["total", "item_count"]
)

# Access computed properties
total = proxy.computed(float, "total")
item_count = proxy.computed(int, "item_count")
average_price = proxy.computed(float, "average_price")

print(f"Total: ${total.get()}")  # Prints: Total: $35.0
print(f"Item count: {item_count.get()}")  # Prints: Item count: 3
print(f"Average price: ${average_price.get()}")  # Prints: Average price: $11.67

# Update the items
items = proxy.observable_list(float, "items")
items.append(15.0)

print(f"Total: ${total.get()}")  # Prints: Total: $50.0
print(f"Item count: {item_count.get()}")  # Prints: Item count: 4
print(f"Average price: ${average_price.get()}")  # Prints: Average price: $12.5
```

## Computed Fields Depending on Other Computed Fields

Computed fields can depend on other computed fields. In the example above, `average_price` depends on `total` and `item_count`, which are themselves computed fields.

When you update a field, all computed fields that depend on it, directly or indirectly, will be recalculated in the correct order.

## Computed Fields with Validation

You can add validators to computed fields just like regular fields:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    first_name: str
    last_name: str

# Create a user
user = User(first_name="", last_name="")

# Create a proxy
proxy = ObservableProxy(user)

# Register a computed property for the full name
proxy.register_computed(
    "full_name",
    lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}".strip(),
    ["first_name", "last_name"]
)

# Add a validator to the computed property
proxy.add_validator("full_name", lambda v: "Full name is required" if not v else None)

# Check validation errors
errors = proxy.validation_for("full_name").get()
print(errors)  # Prints: ['Full name is required']

# Fix the validation error
proxy.observable(str, "first_name").set("Ada")
proxy.observable(str, "last_name").set("Lovelace")

# Check validation errors again
errors = proxy.validation_for("full_name").get()
print(errors)  # Prints: []
```

## Computed Fields with Undo/Redo

Computed fields are automatically updated during undo and redo operations:

```python
from observant import ObservableProxy
from dataclasses import dataclass

@dataclass
class User:
    first_name: str
    last_name: str

# Create a user
user = User(first_name="Ada", last_name="Lovelace")

# Create a proxy with undo enabled
proxy = ObservableProxy(user, undo=True)

# Register a computed property for the full name
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

## Advanced Computed Field Patterns

### Filtering and Sorting

Computed fields can be used to filter and sort collections:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class TodoItem:
    text: str
    completed: bool

@dataclass
class TodoList:
    items: List[TodoItem]

# Create a todo list
todo_list = TodoList(items=[
    TodoItem(text="Buy groceries", completed=False),
    TodoItem(text="Clean house", completed=True),
    TodoItem(text="Write code", completed=False)
])

# Create a proxy
proxy = ObservableProxy(todo_list)

# Register computed properties
proxy.register_computed(
    "active_items",
    lambda: [item for item in proxy.observable_list(TodoItem, "items") if not item.completed],
    ["items"]
)

proxy.register_computed(
    "completed_items",
    lambda: [item for item in proxy.observable_list(TodoItem, "items") if item.completed],
    ["items"]
)

proxy.register_computed(
    "active_count",
    lambda: len(proxy.computed(list, "active_items").get()),
    ["active_items"]
)

proxy.register_computed(
    "completed_count",
    lambda: len(proxy.computed(list, "completed_items").get()),
    ["completed_items"]
)

# Access computed properties
active_items = proxy.computed(list, "active_items")
completed_items = proxy.computed(list, "completed_items")
active_count = proxy.computed(int, "active_count")
completed_count = proxy.computed(int, "completed_count")

print(f"Active items: {[item.text for item in active_items.get()]}")
# Prints: Active items: ['Buy groceries', 'Write code']

print(f"Completed items: {[item.text for item in completed_items.get()]}")
# Prints: Completed items: ['Clean house']

print(f"Active count: {active_count.get()}")  # Prints: Active count: 2
print(f"Completed count: {completed_count.get()}")  # Prints: Completed count: 1

# Update an item
items = proxy.observable_list(TodoItem, "items")
items[0].completed = True

# Computed properties are automatically updated
print(f"Active items: {[item.text for item in active_items.get()]}")
# Prints: Active items: ['Write code']

print(f"Completed items: {[item.text for item in completed_items.get()]}")
# Prints: Completed items: ['Buy groceries', 'Clean house']

print(f"Active count: {active_count.get()}")  # Prints: Active count: 1
print(f"Completed count: {completed_count.get()}")  # Prints: Completed count: 2
```

### Aggregation and Statistics

Computed fields can be used to calculate aggregations and statistics:

```python
from observant import ObservableProxy
from dataclasses import dataclass
from typing import List
import statistics

@dataclass
class Student:
    name: str
    grades: List[int]

@dataclass
class Classroom:
    students: List[Student]

# Create a classroom
classroom = Classroom(students=[
    Student(name="Alice", grades=[85, 90, 95]),
    Student(name="Bob", grades=[75, 80, 85]),
    Student(name="Charlie", grades=[95, 90, 100])
])

# Create a proxy
proxy = ObservableProxy(classroom)

# Register computed properties
proxy.register_computed(
    "all_grades",
    lambda: [grade for student in proxy.observable_list(Student, "students") for grade in student.grades],
    ["students"]
)

proxy.register_computed(
    "average_grade",
    lambda: statistics.mean(proxy.computed(list, "all_grades").get()) if proxy.computed(list, "all_grades").get() else 0,
    ["all_grades"]
)

proxy.register_computed(
    "median_grade",
    lambda: statistics.median(proxy.computed(list, "all_grades").get()) if proxy.computed(list, "all_grades").get() else 0,
    ["all_grades"]
)

proxy.register_computed(
    "top_student",
    lambda: max(proxy.observable_list(Student, "students"), key=lambda s: statistics.mean(s.grades)).name if proxy.observable_list(Student, "students") else "",
    ["students"]
)

# Access computed properties
all_grades = proxy.computed(list, "all_grades")
average_grade = proxy.computed(float, "average_grade")
median_grade = proxy.computed(float, "median_grade")
top_student = proxy.computed(str, "top_student")

print(f"All grades: {all_grades.get()}")
# Prints: All grades: [85, 90, 95, 75, 80, 85, 95, 90, 100]

print(f"Average grade: {average_grade.get()}")  # Prints: Average grade: 88.33
print(f"Median grade: {median_grade.get()}")  # Prints: Median grade: 90.0
print(f"Top student: {top_student.get()}")  # Prints: Top student: Charlie

# Update a student's grades
students = proxy.observable_list(Student, "students")
students[1].grades = [95, 100, 100]

# Computed properties are automatically updated
print(f"Average grade: {average_grade.get()}")  # Prints: Average grade: 94.44
print(f"Median grade: {median_grade.get()}")  # Prints: Median grade: 95.0
print(f"Top student: {top_student.get()}")  # Prints: Top student: Bob
```

## API Reference

### `register_computed()`

```python
def register_computed(
    self,
    attr: str,
    compute_fn: Callable[[], T],
    dependencies: list[str],
) -> None
```

Registers a computed field.

- `attr`: The name of the computed field
- `compute_fn`: A function that computes the value of the field
- `dependencies`: A list of field names that the computed field depends on

### `computed()`

```python
def computed(self, type_: Type[T], attr: str) -> IObservable[T]
```

Gets an observable for a computed field.

- `type_`: The type of the computed field
- `attr`: The name of the computed field

### `has_computed()`

```python
def has_computed(self, attr: str) -> bool
```

Checks if a computed field exists.

- `attr`: The name of the computed field
