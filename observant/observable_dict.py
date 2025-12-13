from typing import Callable, Generic, Iterator, TypeVar, cast, override

from observant.interfaces.dict import IObservableDict, ObservableDictChange
from observant.types.collection_change_type import ObservableCollectionChangeType

TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


class ObservableDict(Generic[TKey, TValue], IObservableDict[TKey, TValue]):
    """
    An observable implementation of Python's dictionary that notifies listeners of changes.

    ObservableDict wraps a Python dictionary and provides the same interface, but with
    additional notification capabilities. It can either create its own internal
    dictionary or work with an existing one.

    When the dictionary is modified (items added, removed, updated, etc.), registered
    callbacks are notified with details about the change. This allows other components
    to react to changes in the dictionary.

    Attributes:
        _items: The internal dictionary being observed.
        _change_callbacks: Callbacks for all types of changes.
        _add_callbacks: Callbacks specifically for add operations.
        _remove_callbacks: Callbacks specifically for remove operations.
        _update_callbacks: Callbacks specifically for update operations.
        _clear_callbacks: Callbacks specifically for clear operations.

    Examples:
        ```python
        # Create an empty observable dictionary
        settings = ObservableDict[str, int]()

        # Create with initial items
        user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})

        # Register a callback for all changes
        user_data.on_change(lambda change: print(f"Change: {change.type}"))

        # Register a callback for adds
        user_data.on_add(lambda key, value: print(f"Added {key}: {value}"))

        # Modify the dictionary
        user_data["phone"] = "555-1234"  # Triggers callbacks
        ```
    """

    def __init__(self, items: dict[TKey, TValue] | None = None, *, copy: bool = False) -> None:
        """
        Initialize with optional external dict reference.

        Args:
            items: Optional external dict to observe. If None, creates a new dict.
            copy: If True, creates a copy of the provided dict instead of using it directly.
                This is useful when you want to avoid modifying the original dict.

        Examples:
            ```python
            # Create an empty observable dictionary
            empty_dict = ObservableDict[str, int]()

            # Create with initial items
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})

            # Create with a copy of initial items
            original = {"red": "#FF0000", "green": "#00FF00"}
            colors = ObservableDict[str, str](original, copy=True)
            colors["blue"] = "#0000FF"  # original dict is not modified
            ```
        """
        if copy:
            self._items: dict[TKey, TValue] = dict(items) if items is not None else {}
        else:
            self._items = items if items is not None else {}
        self._change_callbacks: list[Callable[[ObservableDictChange[TKey, TValue]], None]] = []
        self._add_callbacks: list[Callable[[TKey, TValue], None]] = []
        self._remove_callbacks: list[Callable[[TKey, TValue], None]] = []
        self._update_callbacks: list[Callable[[TKey, TValue], None]] = []
        self._clear_callbacks: list[Callable[[dict[TKey, TValue]], None]] = []

    @override
    def __len__(self) -> int:
        """
        Return the number of items in the dictionary.

        Returns:
            The number of items in the dictionary.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            length = len(user_data)  # Returns: 2
            ```
        """
        return len(self._items)

    @override
    def __getitem__(self, key: TKey) -> TValue:
        """
        Get an item from the dictionary.

        Args:
            key: The key to look up.

        Returns:
            The value for the key.

        Raises:
            KeyError: If the key is not found.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            name = user_data["name"]  # Returns: "Alice"
            ```
        """
        return self._items[key]

    @override
    def __setitem__(self, key: TKey, value: TValue) -> None:
        """
        Set an item in the dictionary.

        This method notifies callbacks about the added or updated item.
        If the key already exists, an update notification is sent.
        If the key is new, an add notification is sent.

        Args:
            key: The key to set.
            value: The value to set.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice"})
            user_data["email"] = "alice@example.com"  # Triggers add callbacks
            user_data["name"] = "Alicia"  # Triggers update callbacks
            ```
        """
        if key in self._items:
            self._items[key] = value
            self._notify_update(key, value)
        else:
            self._items[key] = value
            self._notify_add(key, value)

    @override
    def __delitem__(self, key: TKey) -> None:
        """
        Delete an item from the dictionary.

        This method notifies callbacks about the removed item.

        Args:
            key: The key to delete.

        Raises:
            KeyError: If the key is not found.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            del user_data["email"]  # Triggers remove callbacks
            ```
        """
        value = self._items[key]
        del self._items[key]
        self._notify_remove(key, value)

    @override
    def __iter__(self) -> Iterator[TKey]:
        """
        Return an iterator over the keys in the dictionary.

        Returns:
            An iterator over the keys in the dictionary.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            for key in user_data:
                print(key)  # Prints: "name", "email"
            ```
        """
        return iter(self._items)

    @override
    def __contains__(self, key: TKey) -> bool:
        """
        Check if a key is in the dictionary.

        Args:
            key: The key to check for.

        Returns:
            True if the key is in the dictionary, False otherwise.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            if "name" in user_data:
                print("Name is present")
            ```
        """
        return key in self._items

    @override
    def get(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """
        Return the value for a key if it exists, otherwise return a default value.

        This method does not modify the dictionary or trigger any callbacks.

        Args:
            key: The key to look up.
            default: The default value to return if the key is not found.

        Returns:
            The value for the key, or the default value.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice"})
            email = user_data.get("email", "No email")  # Returns: "No email"
            name = user_data.get("name", "Unknown")  # Returns: "Alice"
            ```
        """
        return self._items.get(key, default)

    @override
    def setdefault(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """
        Return the value for a key if it exists, otherwise set and return the default value.

        If the key does not exist, this method adds it with the default value and
        triggers add callbacks.

        Args:
            key: The key to look up.
            default: The default value to set and return if the key is not found.

        Returns:
            The value for the key, or the default value.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice"})
            email = user_data.setdefault("email", "alice@example.com")  # Returns: "alice@example.com" and adds it
            name = user_data.setdefault("name", "Unknown")  # Returns: "Alice" without changing it
            ```
        """
        if key not in self._items:
            self._items[key] = cast(TValue, default)  # Cast to V since we know it's a value
            self._notify_add(key, cast(TValue, default))
            return default
        return self._items[key]

    @override
    def pop(self, key: TKey, default: TValue | None = None) -> TValue | None:
        """
        Remove and return the value for a key if it exists, otherwise return a default value.

        If the key exists, this method removes it and triggers remove callbacks.
        If the key does not exist and a default is provided, no callbacks are triggered.

        Args:
            key: The key to look up.
            default: The default value to return if the key is not found.

        Returns:
            The value for the key, or the default value.

        Raises:
            KeyError: If the key is not found and no default value is provided.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            email = user_data.pop("email")  # Returns: "alice@example.com" and removes it
            phone = user_data.pop("phone", "No phone")  # Returns: "No phone" without modifying the dict
            ```
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

        This method removes an arbitrary (key, value) pair and triggers remove callbacks.
        In Python 3.7+, the pairs are returned in LIFO order (last inserted, first returned).

        Returns:
            A (key, value) pair.

        Raises:
            KeyError: If the dictionary is empty.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            key, value = user_data.popitem()  # Might return: ("email", "alice@example.com")
            ```
        """
        key, value = self._items.popitem()
        self._notify_remove(key, value)
        return key, value

    @override
    def clear(self) -> None:
        """
        Remove all items from the dictionary.

        This method notifies callbacks about the cleared items.
        If the dictionary is already empty, no notifications are sent.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            user_data.clear()  # Dictionary becomes {}
            ```
        """
        if not self._items:
            return
        items = self._items.copy()
        self._items.clear()
        self._notify_clear(items)

    @override
    def update(self, other: dict[TKey, TValue]) -> None:
        """
        Update the dictionary with the key/value pairs from another dictionary.

        This method notifies callbacks about added and updated items.
        For each key in the other dictionary:
        - If the key already exists, an update notification is sent.
        - If the key is new, an add notification is sent.
        If the other dictionary is empty, no notifications are sent.

        Args:
            other: Another dictionary to update from.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice"})
            user_data.update({"email": "alice@example.com", "name": "Alicia"})
            # Dictionary becomes {"name": "Alicia", "email": "alice@example.com"}
            ```
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

        This method does not modify the dictionary or trigger any callbacks.

        Returns:
            A list of keys.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            keys = user_data.keys()  # Returns: ["name", "email"]
            ```
        """
        return list(self._items.keys())

    @override
    def values(self) -> list[TValue]:
        """
        Return a list of all values in the dictionary.

        This method does not modify the dictionary or trigger any callbacks.

        Returns:
            A list of values.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            values = user_data.values()  # Returns: ["Alice", "alice@example.com"]
            ```
        """
        return list(self._items.values())

    @override
    def items(self) -> list[tuple[TKey, TValue]]:
        """
        Return a list of all (key, value) pairs in the dictionary.

        This method does not modify the dictionary or trigger any callbacks.

        Returns:
            A list of (key, value) pairs.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            items = user_data.items()  # Returns: [("name", "Alice"), ("email", "alice@example.com")]
            ```
        """
        return list(self._items.items())

    @override
    def copy(self) -> dict[TKey, TValue]:
        """
        Return a shallow copy of the dictionary.

        This method returns a regular Python dictionary, not an ObservableDict.
        It does not modify the dictionary or trigger any callbacks.

        Returns:
            A shallow copy of the dictionary as a regular Python dictionary.

        Examples:
            ```python
            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            copy = user_data.copy()  # Returns: {"name": "Alice", "email": "alice@example.com"} as a regular dict
            ```
        """
        return self._items.copy()

    @override
    def on_change(self, callback: Callable[[ObservableDictChange[TKey, TValue]], None]) -> None:
        """
        Add a callback to be called when the dictionary changes.

        The callback will be called with an ObservableDictChange object that contains
        information about the type of change (add, remove, update, clear) and the affected items.

        Args:
            callback: A function that takes an ObservableDictChange object.

        Examples:
            ```python
            def on_dict_change(change):
                print(f"Change type: {change.type}")
                if change.type == ObservableCollectionChangeType.ADD:
                    print(f"Added key: {change.key}, value: {change.value}")
                elif change.type == ObservableCollectionChangeType.UPDATE:
                    print(f"Updated key: {change.key}, new value: {change.value}")

            user_data = ObservableDict[str, str]({"name": "Alice"})
            user_data.on_change(on_dict_change)
            user_data["email"] = "alice@example.com"  # Triggers the callback
            ```
        """
        self._change_callbacks.append(callback)

    @override
    def on_add(self, callback: Callable[[TKey, TValue], None]) -> None:
        """
        Register for add events with key and value.

        This is a more specific alternative to on_change that only triggers
        for add operations and provides a simpler callback signature.

        Args:
            callback: A function that takes a key and value.

        Examples:
            ```python
            def on_item_added(key, value):
                print(f"Added {key}: {value}")

            user_data = ObservableDict[str, str]({"name": "Alice"})
            user_data.on_add(on_item_added)
            user_data["email"] = "alice@example.com"  # Triggers the callback with ("email", "alice@example.com")
            ```
        """
        self._add_callbacks.append(callback)

    @override
    def on_remove(self, callback: Callable[[TKey, TValue], None]) -> None:
        """
        Register for remove events with key and value.

        This is a more specific alternative to on_change that only triggers
        for remove operations and provides a simpler callback signature.

        Args:
            callback: A function that takes a key and value.

        Examples:
            ```python
            def on_item_removed(key, value):
                print(f"Removed {key}: {value}")

            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            user_data.on_remove(on_item_removed)
            del user_data["email"]  # Triggers the callback with ("email", "alice@example.com")
            ```
        """
        self._remove_callbacks.append(callback)

    @override
    def on_update(self, callback: Callable[[TKey, TValue], None]) -> None:
        """
        Register for update events with key and new value.

        This is a more specific alternative to on_change that only triggers
        for update operations and provides a simpler callback signature.

        Args:
            callback: A function that takes a key and new value.

        Examples:
            ```python
            def on_item_updated(key, value):
                print(f"Updated {key} to {value}")

            user_data = ObservableDict[str, str]({"name": "Alice"})
            user_data.on_update(on_item_updated)
            user_data["name"] = "Alicia"  # Triggers the callback with ("name", "Alicia")
            ```
        """
        self._update_callbacks.append(callback)

    @override
    def on_clear(self, callback: Callable[[dict[TKey, TValue]], None]) -> None:
        """
        Register for clear events with the cleared items.

        This is a more specific alternative to on_change that only triggers
        for clear operations and provides a simpler callback signature.

        Args:
            callback: A function that takes a dict of cleared items.

        Examples:
            ```python
            def on_dict_cleared(items):
                print(f"Cleared {len(items)} items: {items}")

            user_data = ObservableDict[str, str]({"name": "Alice", "email": "alice@example.com"})
            user_data.on_clear(on_dict_cleared)
            user_data.clear()  # Triggers the callback with {"name": "Alice", "email": "alice@example.com"}
            ```
        """
        self._clear_callbacks.append(callback)

    def _notify_add(self, key: TKey, value: TValue) -> None:
        """
        Notify all callbacks of an item being added.

        This internal method is called by methods that add items to the dictionary.
        It notifies both specific add callbacks and general change callbacks.

        Args:
            key: The key that was added.
            value: The value that was added.
        """
        # Call specific callbacks
        for callback in self._add_callbacks:
            callback(key, value)

        # Create a dictionary with the single item for the items field
        items_dict = {key: value}

        # Call general change callbacks
        change = ObservableDictChange(
            type=ObservableCollectionChangeType.ADD,
            key=key,
            value=value,
            items=items_dict,
        )
        for callback in self._change_callbacks:
            callback(change)

    def _notify_remove(self, key: TKey, value: TValue) -> None:
        """
        Notify all callbacks of an item being removed.

        This internal method is called by methods that remove items from the dictionary.
        It notifies both specific remove callbacks and general change callbacks.

        Args:
            key: The key that was removed.
            value: The value that was removed.
        """
        # Call specific callbacks
        for callback in self._remove_callbacks:
            callback(key, value)

        # Create a dictionary with the single item for the items field
        items_dict = {key: value}

        # Call general change callbacks
        change = ObservableDictChange(
            type=ObservableCollectionChangeType.REMOVE,
            key=key,
            value=value,
            items=items_dict,
        )
        for callback in self._change_callbacks:
            callback(change)

    def _notify_update(self, key: TKey, value: TValue) -> None:
        """
        Notify all callbacks of an item being updated.

        This internal method is called by methods that update items in the dictionary.
        It notifies both specific update callbacks and general change callbacks.

        Args:
            key: The key that was updated.
            value: The new value.
        """
        # Call specific callbacks
        for callback in self._update_callbacks:
            callback(key, value)

        # Create a dictionary with the single item for the items field
        items_dict = {key: value}

        # Call general change callbacks
        change = ObservableDictChange(
            type=ObservableCollectionChangeType.UPDATE,
            key=key,
            value=value,
            items=items_dict,
        )
        for callback in self._change_callbacks:
            callback(change)

    def _notify_clear(self, items: dict[TKey, TValue]) -> None:
        """
        Notify all callbacks of the dictionary being cleared.

        This internal method is called by the clear method.
        It notifies both specific clear callbacks and general change callbacks.

        Args:
            items: The items that were cleared.
        """
        # Call specific callbacks
        for callback in self._clear_callbacks:
            callback(items)

        # Call general change callbacks
        change = ObservableDictChange(type=ObservableCollectionChangeType.CLEAR, items=items)
        for callback in self._change_callbacks:
            callback(change)
