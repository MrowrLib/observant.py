# Nested Paths

Observant supports accessing deeply nested properties through dot-notation paths with `observable_for_path()`. This is especially useful when working with complex data structures.

## Basic Nested Paths

Use dot notation to access nested properties:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class Address:
    city: str
    country: str

@dataclass
class User:
    name: str
    address: Address

user = User(
    name="Alice",
    address=Address(city="New York", country="USA")
)

proxy = ObservableProxy(user, sync=True)

# Access nested property
city_obs = proxy.observable_for_path("address.city")
print(city_obs.get())  # "New York"

# Update nested property
city_obs.set("Los Angeles")
print(user.address.city)  # "Los Angeles"
```

## Optional Chaining

Use `?.` syntax (like JavaScript) to safely access properties that might be `None`:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class Address:
    city: str
    country: str

@dataclass
class User:
    name: str
    address: Address | None = None

# User without an address
user = User(name="Alice", address=None)
proxy = ObservableProxy(user, sync=True)

# Without optional chaining, this would error
# With optional chaining, it returns None
city_obs = proxy.observable_for_path("address?.city")
print(city_obs.get())  # None

# Setting when path is broken is a safe no-op
city_obs.set("New York")  # Does nothing, no error
print(city_obs.get())  # Still None
```

## Deep Nesting with Optional Chaining

You can chain multiple optional segments for deeply nested structures:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class Location:
    city: str = ""
    country: str = ""

@dataclass
class Habitat:
    name: str = ""
    location: Location | None = None

@dataclass
class Animal:
    name: str
    species: str
    habitat: Habitat | None = None

animal = Animal(
    name="Leo",
    species="Lion",
    habitat=Habitat(
        name="Savanna",
        location=Location(city="Nairobi", country="Kenya")
    )
)

proxy = ObservableProxy(animal, sync=True)

# Two levels deep with optional chaining
city_obs = proxy.observable_for_path("habitat?.location?.city")
print(city_obs.get())  # "Nairobi"

# Update works when path exists
city_obs.set("Mombasa")
print(animal.habitat.location.city)  # "Mombasa"
```

## Reactive Updates

When using optional chaining, the observable automatically updates when parent objects change:

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class Address:
    city: str

@dataclass
class User:
    name: str
    address: Address | None = None

user = User(name="Alice", address=None)
proxy = ObservableProxy(user, sync=True)

city_obs = proxy.observable_for_path("address?.city")
print(city_obs.get())  # None

# Subscribe to changes
city_obs.on_change(lambda v: print(f"City changed to: {v}"))

# When the parent is set, the observable updates
user.address = Address(city="Boston")
proxy.observable(object, "address").set(user.address)
# Prints: "City changed to: Boston"
```

## Multiple Paths Same Parent

Multiple observables can share the same nested parent efficiently:

```python
proxy = ObservableProxy(user, sync=True)

# Both share the same internal proxy for "address"
city_obs = proxy.observable_for_path("address.city")
country_obs = proxy.observable_for_path("address.country")

# Changes to one don't affect the other
city_obs.set("Chicago")
print(country_obs.get())  # Still "USA"
```

## Use Cases

### UI Data Binding

Perfect for binding UI components to nested model properties:

```python
# In a UI framework
name_field.bind(proxy.observable_for_path("user.profile.display_name"))
avatar_field.bind(proxy.observable_for_path("user.profile?.avatar_url"))
```

### Form Handling

Access nested form data easily:

```python
@dataclass
class ShippingAddress:
    street: str
    city: str
    zip_code: str

@dataclass
class OrderForm:
    customer_name: str
    shipping: ShippingAddress
    billing: ShippingAddress | None = None  # Optional

proxy = ObservableProxy(form, sync=True)

# Required fields
shipping_city = proxy.observable_for_path("shipping.city")

# Optional fields (billing might be None if "same as shipping")
billing_city = proxy.observable_for_path("billing?.city")
```

## Summary

| Syntax | Behavior |
|--------|----------|
| `"a.b.c"` | Required path - errors if any segment is None |
| `"a?.b?.c"` | Optional path - returns None if any `?.` segment is None |
| `"a.b?.c"` | Mixed - `a.b` required, `c` optional |

The `observable_for_path()` method provides a clean, JavaScript-like API for working with nested data structures while maintaining full reactivity and type safety.
