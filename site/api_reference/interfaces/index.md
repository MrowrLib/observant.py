# Interfaces

This section documents the interfaces that define the contract for observable objects in the Observant library. These interfaces ensure consistent behavior across different types of observables.

## IObservable

An interface that defines the contract for observable objects. It includes methods for getting and setting values, and registering change listeners.

```python
from observant.interfaces import IObservable

# This is typically used for type annotations
def process_observable(observable: IObservable[int]):
    value = observable.get()
    observable.set(value + 1)
```

## IObservableList

An interface that extends `IObservable` for lists. It includes methods for list operations like append, extend, insert, etc.

```python
from observant.interfaces import IObservableList

# This is typically used for type annotations
def process_observable_list(observable_list: IObservableList[str]):
    observable_list.append("New Item")
    items = observable_list.get()
```

## IObservableDict

An interface that extends `IObservable` for dictionaries. It includes methods for dictionary operations like setting and getting items, updating, etc.

```python
from observant.interfaces import IObservableDict

# This is typically used for type annotations
def process_observable_dict(observable_dict: IObservableDict[str, int]):
    observable_dict["key"] = 42
    value = observable_dict["key"]
```

## IObservableProxy

An interface that defines the contract for observable proxies. It includes methods for accessing fields, validation, undo/redo, etc.

```python
from observant.interfaces import IObservableProxy

# This is typically used for type annotations
def process_observable_proxy(proxy: IObservableProxy):
    name_obs = proxy.observable(str, "name")
    name_obs.set("New Name")
```

## Implementation Details

These interfaces are used throughout the Observant library to ensure consistent behavior across different types of observables. They are implemented by the following classes:

- `Observable` implements `IObservable`
- `ObservableList` implements `IObservableList`
- `ObservableDict` implements `IObservableDict`
- `ObservableProxy` implements `IObservableProxy`

The interfaces are defined using Python's typing system, which allows for type checking and better IDE support.

## Auto-Generated Documentation

For more detailed information about each interface, refer to the auto-generated documentation:

- IObservable
- IObservableList
- IObservableDict
- IObservableProxy
