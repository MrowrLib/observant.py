from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, Iterator, TypeVar, cast, override

from observant.observable import CollectionChangeType, ComparableOrPrimitive

TKey = TypeVar("TKey", bound=ComparableOrPrimitive)
TValue = TypeVar("TValue", bound=ComparableOrPrimitive)


@dataclass
class DictChange(Generic[TKey, TValue]):
    """Information about a change to an ObservableDict."""

    type: CollectionChangeType
    key: TKey | None = None  # Key where the change occurred, if applicable
    value: TValue | None = (
        None  # Value that was added, removed, or updated, if applicable
    )
    items: dict[TKey, TValue] | None = (
        None  # Multiple items that were added, removed, or updated, if applicable
    )


class IObservableDict(Generic[TKey, TValue], ABC):
    """Interface for observable dictionaries with specific event types."""

    @abstractmethod
    def __len__(self) -> int:
        """Return the number of items in the dictionary."""
        ...

    @abstractmethod
    def __getitem__(self, key: TKey) -> TValue:
        """Get an item from the dictionary."""
        ...

    @abstractmethod
    def __setitem__(self, key: TKey, value: TValue) -> None:
        """Set an item in the dictionary."""
        ...

    @abstractmethod
    def __delitem__(self, key: TKey) -> None:
        """Delete an item from the dictionary."""
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[TKey]:
        """Return an iterator over the keys in the dictionary."""
        ...

    @abstractmethod
    def __contains__(self, key: TKey) -> bool:
        """Check if a key is in the dictionary."""
        ...

    @abstractmethod
    def get(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """Return the value for a key if it exists, otherwise return a default value."""
        ...

    @abstractmethod
    def setdefault(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """Return the value for a key if it exists, otherwise set and return the default value."""
        ...

    @abstractmethod
    def pop(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """Remove and return the value for a key if it exists, otherwise return a default value."""
        ...

    @abstractmethod
    def popitem(self) -> tuple[TKey, TValue]:
        """Remove and return a (key, value) pair from the dictionary."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all items from the dictionary."""
        ...

    @abstractmethod
    def update(self, other: dict[TKey, TValue]) -> None:
        """Update the dictionary with the key/value pairs from another dictionary."""
        ...

    @abstractmethod
    def keys(self) -> list[TKey]:
        """Return a list of all keys in the dictionary."""
        ...

    @abstractmethod
    def values(self) -> list[TValue]:
        """Return a list of all values in the dictionary."""
        ...

    @abstractmethod
    def items(self) -> list[tuple[TKey, TValue]]:
        """Return a list of all (key, value) pairs in the dictionary."""
        ...

    @abstractmethod
    def copy(self) -> dict[TKey, TValue]:
        """Return a shallow copy of the dictionary."""
        ...

    @abstractmethod
    def on_change(self, callback: Callable[[DictChange[TKey, TValue]], None]) -> None:
        """Register for all change events with detailed information."""
        ...

    @abstractmethod
    def on_add(self, callback: Callable[[TKey, TValue], None]) -> None:
        """Register for add events with key and value."""
        ...

    @abstractmethod
    def on_remove(self, callback: Callable[[TKey, TValue], None]) -> None:
        """Register for remove events with key and value."""
        ...

    @abstractmethod
    def on_update(self, callback: Callable[[TKey, TValue], None]) -> None:
        """Register for update events with key and new value."""
        ...

    @abstractmethod
    def on_clear(self, callback: Callable[[dict[TKey, TValue]], None]) -> None:
        """Register for clear events with the cleared items."""
        ...


class ObservableDictBase(Generic[TKey, TValue], IObservableDict[TKey, TValue]):
    """Base implementation that can work with an external dict or create its own."""

    def __init__(
        self, items: dict[TKey, TValue] | None = None, *, copy: bool = False
    ) -> None:
        """
        Initialize with optional external dict reference.

        Args:
            items: Optional external dict to observe. If None, creates a new dict.
        """
        if copy:
            self._items: dict[TKey, TValue] = dict(items) if items is not None else {}
        else:
            self._items = items if items is not None else {}
        self._change_callbacks: list[Callable[[DictChange[TKey, TValue]], None]] = []
        self._add_callbacks: list[Callable[[TKey, TValue], None]] = []
        self._remove_callbacks: list[Callable[[TKey, TValue], None]] = []
        self._update_callbacks: list[Callable[[TKey, TValue], None]] = []
        self._clear_callbacks: list[Callable[[dict[TKey, TValue]], None]] = []

    @override
    def __len__(self) -> int:
        """Return the number of items in the dictionary."""
        return len(self._items)

    @override
    def __getitem__(self, key: TKey) -> TValue:
        """Get an item from the dictionary."""
        return self._items[key]

    @override
    def __setitem__(self, key: TKey, value: TValue) -> None:
        """Set an item in the dictionary."""
        if key in self._items:
            self._items[key] = value
            self._notify_update(key, value)
        else:
            self._items[key] = value
            self._notify_add(key, value)

    @override
    def __delitem__(self, key: TKey) -> None:
        """Delete an item from the dictionary."""
        value = self._items[key]
        del self._items[key]
        self._notify_remove(key, value)

    @override
    def __iter__(self) -> Iterator[TKey]:
        """Return an iterator over the keys in the dictionary."""
        return iter(self._items)

    @override
    def __contains__(self, key: TKey) -> bool:
        """Check if a key is in the dictionary."""
        return key in self._items

    @override
    def get(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """
        Return the value for a key if it exists, otherwise return a default value.

        Args:
            key: The key to look up
            default: The default value to return if the key is not found

        Returns:
            The value for the key, or the default value
        """
        return self._items.get(key, default)

    @override
    def setdefault(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """
        Return the value for a key if it exists, otherwise set and return the default value.

        Args:
            key: The key to look up
            default: The default value to set and return if the key is not found

        Returns:
            The value for the key, or the default value
        """
        if key not in self._items:
            self._items[key] = cast(
                TValue, default
            )  # Cast to V since we know it's a value
            self._notify_add(key, cast(TValue, default))
            return default
        return self._items[key]

    @override
    def pop(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """
        Remove and return the value for a key if it exists, otherwise return a default value.

        Args:
            key: The key to look up
            default: The default value to return if the key is not found

        Returns:
            The value for the key, or the default value

        Raises:
            KeyError: If the key is not found and no default value is provided
        """
        if key in self._items:
            value = self._items.pop(key)
            self._notify_remove(key, value)
            return value
        if default is not None:
            return default
        raise KeyError(key)

    @override
    def popitem(self) -> tuple[TKey, TValue]:
        """
        Remove and return a (key, value) pair from the dictionary.

        Returns:
            A (key, value) pair

        Raises:
            KeyError: If the dictionary is empty
        """
        key, value = self._items.popitem()
        self._notify_remove(key, value)
        return key, value

    @override
    def clear(self) -> None:
        """Remove all items from the dictionary."""
        if not self._items:
            return
        items = self._items.copy()
        self._items.clear()
        self._notify_clear(items)

    @override
    def update(self, other: dict[TKey, TValue]) -> None:
        """
        Update the dictionary with the key/value pairs from another dictionary.

        Args:
            other: Another dictionary to update from
        """
        if not other:
            return
        added_items: dict[TKey, TValue] = {}
        updated_items: dict[TKey, TValue] = {}
        for key, value in other.items():
            if key in self._items:
                updated_items[key] = value
            else:
                added_items[key] = value
        self._items.update(other)

        # Notify for added items
        if added_items:
            for key, value in added_items.items():
                self._notify_add(key, value)

        # Notify for updated items
        if updated_items:
            for key, value in updated_items.items():
                self._notify_update(key, value)

    @override
    def keys(self) -> list[TKey]:
        """
        Return a list of all keys in the dictionary.

        Returns:
            A list of keys
        """
        return list(self._items.keys())

    @override
    def values(self) -> list[TValue]:
        """
        Return a list of all values in the dictionary.

        Returns:
            A list of values
        """
        return list(self._items.values())

    @override
    def items(self) -> list[tuple[TKey, TValue]]:
        """
        Return a list of all (key, value) pairs in the dictionary.

        Returns:
            A list of (key, value) pairs
        """
        return list(self._items.items())

    @override
    def copy(self) -> dict[TKey, TValue]:
        """
        Return a shallow copy of the dictionary.

        Returns:
            A copy of the dictionary
        """
        return self._items.copy()

    @override
    def on_change(self, callback: Callable[[DictChange[TKey, TValue]], None]) -> None:
        """
        Add a callback to be called when the dictionary changes.

        Args:
            callback: A function that takes a DictChange object
        """
        self._change_callbacks.append(callback)

    @override
    def on_add(self, callback: Callable[[TKey, TValue], None]) -> None:
        """
        Register for add events with key and value.

        Args:
            callback: A function that takes a key and value
        """
        self._add_callbacks.append(callback)

    @override
    def on_remove(self, callback: Callable[[TKey, TValue], None]) -> None:
        """
        Register for remove events with key and value.

        Args:
            callback: A function that takes a key and value
        """
        self._remove_callbacks.append(callback)

    @override
    def on_update(self, callback: Callable[[TKey, TValue], None]) -> None:
        """
        Register for update events with key and new value.

        Args:
            callback: A function that takes a key and new value
        """
        self._update_callbacks.append(callback)

    @override
    def on_clear(self, callback: Callable[[dict[TKey, TValue]], None]) -> None:
        """
        Register for clear events with the cleared items.

        Args:
            callback: A function that takes a dict of cleared items
        """
        self._clear_callbacks.append(callback)

    def _notify_add(self, key: TKey, value: TValue) -> None:
        """
        Notify all callbacks of an item being added.

        Args:
            key: The key that was added
            value: The value that was added
        """
        # Call specific callbacks
        for callback in self._add_callbacks:
            callback(key, value)

        # Create a dictionary with the single item for the items field
        items_dict = {key: value}

        # Call general change callbacks
        change = DictChange(
            type=CollectionChangeType.ADD, key=key, value=value, items=items_dict
        )
        for callback in self._change_callbacks:
            callback(change)

    def _notify_remove(self, key: TKey, value: TValue) -> None:
        """
        Notify all callbacks of an item being removed.

        Args:
            key: The key that was removed
            value: The value that was removed
        """
        # Call specific callbacks
        for callback in self._remove_callbacks:
            callback(key, value)

        # Create a dictionary with the single item for the items field
        items_dict = {key: value}

        # Call general change callbacks
        change = DictChange(
            type=CollectionChangeType.REMOVE, key=key, value=value, items=items_dict
        )
        for callback in self._change_callbacks:
            callback(change)

    def _notify_update(self, key: TKey, value: TValue) -> None:
        """
        Notify all callbacks of an item being updated.

        Args:
            key: The key that was updated
            value: The new value
        """
        # Call specific callbacks
        for callback in self._update_callbacks:
            callback(key, value)

        # Create a dictionary with the single item for the items field
        items_dict = {key: value}

        # Call general change callbacks
        change = DictChange(
            type=CollectionChangeType.UPDATE, key=key, value=value, items=items_dict
        )
        for callback in self._change_callbacks:
            callback(change)

    def _notify_clear(self, items: dict[TKey, TValue]) -> None:
        """
        Notify all callbacks of the dictionary being cleared.

        Args:
            items: The items that were cleared
        """
        # Call specific callbacks
        for callback in self._clear_callbacks:
            callback(items)

        # Call general change callbacks
        change = DictChange(type=CollectionChangeType.CLEAR, items=items)
        for callback in self._change_callbacks:
            callback(change)


class ObservableDict(ObservableDictBase[TKey, TValue]):
    """A dictionary that notifies observers when items are added, removed, or updated."""

    def __init__(
        self, initial_items: dict[TKey, TValue] | None = None, *, copy: bool = False
    ) -> None:
        """
        Initialize an ObservableDict.

        Args:
            initial_items: Initial items to add to the dictionary
        """
        super().__init__(initial_items, copy=copy)
