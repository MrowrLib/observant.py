# API Reference

This section provides detailed documentation for the Observant API. It covers all the classes, methods, and types available in the library.

## Core Classes

- [Observable](observable.md): The base observable class for scalar values
- [ObservableList](observable_list.md): An observable list that notifies listeners when items are added, removed, or modified
- [ObservableDict](observable_dict.md): An observable dictionary that notifies listeners when items are added, updated, or removed
- [ObservableProxy](observable_proxy.md): An observable proxy that wraps an object and provides observable access to its fields

## Types

The [Types](types/index.md) section documents the various types used throughout the library:

- ObservableCollectionChangeType: An enum that represents the type of change that occurred in a collection
- ObservableListChange: A class that represents a change to an observable list
- ObservableDictChange: A class that represents a change to an observable dictionary
- ProxyFieldKey: A class that represents a field key in an ObservableProxy
- UndoConfig: A class that represents the configuration for undo/redo functionality

## Interfaces

The [Interfaces](interfaces/index.md) section documents the interfaces that define the contract for observable objects:

- IObservable: The base interface for observable objects
- IObservableList: The interface for observable lists
- IObservableDict: The interface for observable dictionaries
- IObservableProxy: The interface for observable proxies
