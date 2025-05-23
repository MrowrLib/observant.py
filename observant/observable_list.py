from typing import Any, Callable, Generic, Iterator, TypeVar, cast, override

from observant.interfaces.list import IObservableList, ObservableListChange
from observant.types.collection_change_type import ObservableCollectionChangeType

T = TypeVar("T")


class ObservableList(Generic[T], IObservableList[T]):
    """
    An observable implementation of Python's list that notifies listeners of changes.

    ObservableList wraps a Python list and provides the same interface, but with
    additional notification capabilities. It can either create its own internal
    list or work with an existing list.

    When the list is modified (items added, removed, etc.), registered callbacks
    are notified with details about the change. This allows other components to
    react to changes in the list.

    Attributes:
        _items: The internal list being observed.
        _change_callbacks: Callbacks for all types of changes.
        _add_callbacks: Callbacks specifically for add operations.
        _remove_callbacks: Callbacks specifically for remove operations.
        _clear_callbacks: Callbacks specifically for clear operations.

    Examples:
        ```python
        # Create an empty observable list
        numbers = ObservableList[int]()

        # Create with initial items
        names = ObservableList[str](["Alice", "Bob", "Charlie"])

        # Register a callback for all changes
        names.on_change(lambda change: print(f"Change: {change.type}"))

        # Register a callback for adds
        names.on_add(lambda item, index: print(f"Added {item} at index {index}"))

        # Modify the list
        names.append("David")  # Triggers callbacks
        ```
    """

    def __init__(self, items: list[T] | None = None, *, copy: bool = False):
        """
        Initialize with optional external list reference.

        Args:
            items: Optional external list to observe. If None, creates a new list.
            copy: If True, creates a copy of the provided list instead of using it directly.
                This is useful when you want to avoid modifying the original list.

        Examples:
            ```python
            # Create an empty observable list
            empty_list = ObservableList[int]()

            # Create with initial items
            names = ObservableList[str](["Alice", "Bob"])

            # Create with a copy of initial items
            original = ["Red", "Green", "Blue"]
            colors = ObservableList[str](original, copy=True)
            colors.append("Yellow")  # original list is not modified
            ```
        """
        if copy:
            self._items: list[T] = list(items) if items is not None else []
        else:
            self._items: list[T] = items if items is not None else []
        self._change_callbacks: list[Callable[[ObservableListChange[T]], None]] = []
        self._add_callbacks: list[Callable[[T, int], None]] = []
        self._remove_callbacks: list[Callable[[T, int], None]] = []
        self._clear_callbacks: list[Callable[[list[T]], None]] = []

    @override
    def __len__(self) -> int:
        """
        Return the number of items in the list.

        Returns:
            The number of items in the list.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob"])
            length = len(names)  # Returns: 2
            ```
        """
        return len(self._items)

    @override
    def __getitem__(self, index: int | slice) -> T | list[T]:
        """
        Get an item or slice of items from the list.

        Args:
            index: The index or slice to retrieve.

        Returns:
            The item at the specified index, or a list of items if a slice was provided.

        Raises:
            IndexError: If the index is out of range.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            first = names[0]  # Returns: "Alice"
            subset = names[1:3]  # Returns: ["Bob", "Charlie"]
            ```
        """
        return self._items[index]

    @override
    def __setitem__(self, index: int | slice, value: T | list[T]) -> None:
        """
        Set an item or slice of items in the list.

        This method notifies callbacks about the removed items and then about the
        added items. For a single item replacement, this results in a remove notification
        followed by an add notification.

        Args:
            index: The index or slice to set.
            value: The item or list of items to set.

        Raises:
            IndexError: If the index is out of range.
            TypeError: If the value is not of the correct type.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            names[1] = "Robert"  # Replace "Bob" with "Robert"
            names[1:3] = ["Eve", "Frank"]  # Replace "Robert" and "Charlie"
            ```
        """
        if isinstance(index, slice):
            # Remove old items
            old_items = self._items[index]
            if old_items:
                self._notify_remove_items(old_items, index.start)

            # Add new items
            if isinstance(value, list):
                # Explicitly cast to list[C] to help Pylance
                self._items[index] = value
                if value:
                    typed_value: list[T] = cast(list[T], value)
                    self._notify_add_items(typed_value, index.start)
            else:
                # Handle single item assigned to slice
                single_value: T = cast(T, value)
                items_list: list[T] = [single_value]
                self._items[index] = items_list
                self._notify_add_items(items_list, index.start)
        else:
            # Remove old item
            old_item = self._items[index]
            self._notify_remove(old_item, index)

            # Add new item
            new_value: T = cast(T, value)  # Cast to T since we know it's a single item
            self._items[index] = new_value
            self._notify_add(new_value, index)

    @override
    def __delitem__(self, index: int | slice) -> None:
        """
        Delete an item or slice of items from the list.

        This method notifies callbacks about the removed items.

        Args:
            index: The index or slice to delete.

        Raises:
            IndexError: If the index is out of range.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            del names[1]  # Remove "Bob"
            del names[0:1]  # Remove "Alice"
            ```
        """
        if isinstance(index, slice):
            items = self._items[index]
            if items:
                self._notify_remove_items(items, index.start)
        else:
            item = self._items[index]
            self._notify_remove(item, index)
        del self._items[index]

    @override
    def __iter__(self) -> Iterator[T]:
        """
        Return an iterator over the items in the list.

        Returns:
            An iterator over the items in the list.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            for name in names:
                print(name)
            ```
        """
        return iter(self._items)

    @override
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is in the list.

        Args:
            item: The item to check for.

        Returns:
            True if the item is in the list, False otherwise.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            if "Bob" in names:
                print("Bob is in the list")
            ```
        """
        return item in self._items

    @override
    def append(self, item: T) -> None:
        """
        Add an item to the end of the list.

        This method notifies callbacks about the added item.

        Args:
            item: The item to add.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob"])
            names.append("Charlie")  # List becomes ["Alice", "Bob", "Charlie"]
            ```
        """
        self._items.append(item)
        self._notify_add(item, len(self._items) - 1)

    @override
    def extend(self, items: list[T]) -> None:
        """
        Extend the list by appending all items from the iterable.

        This method notifies callbacks about the added items.
        If the items list is empty, no notifications are sent.

        Args:
            items: The items to add.

        Examples:
            ```python
            names = ObservableList[str](["Alice"])
            names.extend(["Bob", "Charlie"])  # List becomes ["Alice", "Bob", "Charlie"]
            ```
        """
        if not items:
            return
        start_index = len(self._items)
        self._items.extend(items)
        self._notify_add_items(items, start_index)

    @override
    def insert(self, index: int, item: T) -> None:
        """
        Insert an item at a given position.

        This method notifies callbacks about the added item.
        If index is greater than the length of the list, the item is appended.
        If index is negative, the item is inserted at index + len(self).

        Args:
            index: The position to insert the item.
            item: The item to insert.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Charlie"])
            names.insert(1, "Bob")  # List becomes ["Alice", "Bob", "Charlie"]
            ```
        """
        self._items.insert(index, item)
        self._notify_add(item, index)

    @override
    def remove(self, item: T) -> None:
        """
        Remove the first occurrence of an item from the list.

        This method notifies callbacks about the removed item.

        Args:
            item: The item to remove.

        Raises:
            ValueError: If the item is not in the list.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie", "Bob"])
            names.remove("Bob")  # List becomes ["Alice", "Charlie", "Bob"]
            ```
        """
        index = self._items.index(item)
        self._items.remove(item)
        self._notify_remove(item, index)

    @override
    def pop(self, index: int = -1) -> T:
        """
        Remove and return an item at a given position.

        This method notifies callbacks about the removed item.

        Args:
            index: The position to remove the item from (default is -1, which is the last item).

        Returns:
            The removed item.

        Raises:
            IndexError: If the list is empty or index is out of range.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            last = names.pop()  # Returns: "Charlie", list becomes ["Alice", "Bob"]
            first = names.pop(0)  # Returns: "Alice", list becomes ["Bob"]
            ```
        """
        item = self._items[index]
        self._items.pop(index)
        self._notify_remove(item, index)
        return item

    @override
    def clear(self) -> None:
        """
        Remove all items from the list.

        This method notifies callbacks about the cleared items.
        If the list is already empty, no notifications are sent.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            names.clear()  # List becomes []
            ```
        """
        if not self._items:
            return
        items = self._items.copy()
        self._items.clear()
        self._notify_clear(items)

    @override
    def index(self, item: T, start: int = 0, end: int | None = None) -> int:
        """
        Return the index of the first occurrence of an item.

        Args:
            item: The item to find.
            start: The start index to search from.
            end: The end index to search to.

        Returns:
            The index of the item.

        Raises:
            ValueError: If the item is not in the list.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie", "Bob"])
            index = names.index("Bob")  # Returns: 1
            index = names.index("Bob", 2)  # Returns: 3 (search starts at index 2)
            ```
        """
        if end is None:
            return self._items.index(item, start)
        return self._items.index(item, start, end)

    @override
    def count(self, item: T) -> int:
        """
        Return the number of occurrences of an item in the list.

        Args:
            item: The item to count.

        Returns:
            The number of occurrences.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie", "Bob"])
            count = names.count("Bob")  # Returns: 2
            ```
        """
        return self._items.count(item)

    @override
    def sort(
        self,
        *,
        key: Callable[[T], Any] | None = None,
        reverse: bool = False,
    ) -> None:
        """
        Sort the list in place.

        This method does not notify callbacks as the items themselves haven't changed,
        only their order.

        Args:
            key: A function that takes an item and returns a key for sorting.
            reverse: Whether to sort in reverse order.

        Examples:
            ```python
            names = ObservableList[str](["Charlie", "Alice", "Bob"])
            names.sort()  # List becomes ["Alice", "Bob", "Charlie"]

            # Sort by length of name
            names.sort(key=len)  # List becomes ["Bob", "Alice", "Charlie"]

            # Sort in reverse order
            names.sort(reverse=True)  # List becomes ["Charlie", "Bob", "Alice"]
            ```
        """

        # Note: pylance is just WRONG about the keys being wrong types.

        if key is None:
            if reverse:
                self._items.sort(key=None, reverse=True)  # type: ignore
            else:
                self._items.sort(key=None, reverse=False)  # type: ignore
        else:
            self._items.sort(key=key, reverse=reverse)

    @override
    def reverse(self) -> None:
        """
        Reverse the list in place.

        This method does not notify callbacks as the items themselves haven't changed,
        only their order.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            names.reverse()  # List becomes ["Charlie", "Bob", "Alice"]
            ```
        """
        self._items.reverse()
        # No notification needed as the items themselves haven't changed

    @override
    def copy(self) -> list[T]:
        """
        Return a shallow copy of the list.

        This method returns a regular Python list, not an ObservableList.

        Returns:
            A shallow copy of the list as a regular Python list.

        Examples:
            ```python
            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            copy = names.copy()  # Returns: ["Alice", "Bob", "Charlie"] as a regular list
            ```
        """
        return self._items.copy()

    @override
    def on_change(self, callback: Callable[[ObservableListChange[T]], None]) -> None:
        """
        Add a callback to be called when the list changes.

        The callback will be called with an ObservableListChange object that contains
        information about the type of change (add, remove, clear) and the affected items.

        Args:
            callback: A function that takes an ObservableListChange object.

        Examples:
            ```python
            def on_list_change(change):
                print(f"Change type: {change.type}")
                if change.type == ObservableCollectionChangeType.ADD:
                    print(f"Added at index {change.index}")
                    if change.item:
                        print(f"Added item: {change.item}")
                    elif change.items:
                        print(f"Added items: {change.items}")

            names = ObservableList[str](["Alice"])
            names.on_change(on_list_change)
            names.append("Bob")  # Triggers the callback
            ```
        """
        self._change_callbacks.append(callback)

    @override
    def on_add(self, callback: Callable[[T, int], None]) -> None:
        """
        Register for add events with item and index.

        This is a more specific alternative to on_change that only triggers
        for add operations and provides a simpler callback signature.

        Args:
            callback: A function that takes an item and its index.

        Examples:
            ```python
            def on_item_added(item, index):
                print(f"Added {item} at index {index}")

            names = ObservableList[str](["Alice"])
            names.on_add(on_item_added)
            names.append("Bob")  # Triggers the callback with ("Bob", 1)
            ```
        """
        self._add_callbacks.append(callback)

    @override
    def on_remove(self, callback: Callable[[T, int], None]) -> None:
        """
        Register for remove events with item and index.

        This is a more specific alternative to on_change that only triggers
        for remove operations and provides a simpler callback signature.

        Args:
            callback: A function that takes an item and its index.

        Examples:
            ```python
            def on_item_removed(item, index):
                print(f"Removed {item} from index {index}")

            names = ObservableList[str](["Alice", "Bob"])
            names.on_remove(on_item_removed)
            names.pop(1)  # Triggers the callback with ("Bob", 1)
            ```
        """
        self._remove_callbacks.append(callback)

    @override
    def on_clear(self, callback: Callable[[list[T]], None]) -> None:
        """
        Register for clear events with the cleared items.

        This is a more specific alternative to on_change that only triggers
        for clear operations and provides a simpler callback signature.

        Args:
            callback: A function that takes a list of cleared items.

        Examples:
            ```python
            def on_list_cleared(items):
                print(f"Cleared {len(items)} items: {items}")

            names = ObservableList[str](["Alice", "Bob", "Charlie"])
            names.on_clear(on_list_cleared)
            names.clear()  # Triggers the callback with ["Alice", "Bob", "Charlie"]
            ```
        """
        self._clear_callbacks.append(callback)

    def _notify_add(self, item: T, index: int) -> None:
        """
        Notify all callbacks of an item being added.

        This internal method is called by methods that add items to the list.
        It notifies both specific add callbacks and general change callbacks.

        Args:
            item: The item that was added.
            index: The index where the item was added.
        """
        # Call specific callbacks
        for callback in self._add_callbacks:
            callback(item, index)

        # Call general change callbacks
        change = ObservableListChange(type=ObservableCollectionChangeType.ADD, index=index, item=item)
        for callback in self._change_callbacks:
            callback(change)

    def _notify_add_items(self, items: list[T], start_index: int) -> None:
        """
        Notify all callbacks of multiple items being added.

        This internal method is called by methods that add multiple items to the list.
        It notifies both specific add callbacks for each item and general change callbacks
        with all items.

        Args:
            items: The items that were added.
            start_index: The index where the items were added.
        """
        # Call specific callbacks for each item
        for i, item in enumerate(items):
            index = start_index + i
            for callback in self._add_callbacks:
                callback(item, index)

        # Call general change callbacks
        change = ObservableListChange(type=ObservableCollectionChangeType.ADD, index=start_index, items=items)
        for callback in self._change_callbacks:
            callback(change)

    def _notify_remove(self, item: T, index: int) -> None:
        """
        Notify all callbacks of an item being removed.

        This internal method is called by methods that remove items from the list.
        It notifies both specific remove callbacks and general change callbacks.

        Args:
            item: The item that was removed.
            index: The index where the item was removed.
        """
        # Call specific callbacks
        for callback in self._remove_callbacks:
            callback(item, index)

        # Call general change callbacks
        change = ObservableListChange(type=ObservableCollectionChangeType.REMOVE, index=index, item=item)
        for callback in self._change_callbacks:
            callback(change)

    def _notify_remove_items(self, items: list[T], start_index: int) -> None:
        """
        Notify all callbacks of multiple items being removed.

        This internal method is called by methods that remove multiple items from the list.
        It notifies both specific remove callbacks for each item and general change callbacks
        with all items.

        Args:
            items: The items that were removed.
            start_index: The index where the items were removed.
        """
        # Call specific callbacks for each item
        for i, item in enumerate(items):
            index = start_index + i
            for callback in self._remove_callbacks:
                callback(item, index)

        # Call general change callbacks
        change = ObservableListChange(type=ObservableCollectionChangeType.REMOVE, index=start_index, items=items)
        for callback in self._change_callbacks:
            callback(change)

    def _notify_clear(self, items: list[T]) -> None:
        """
        Notify all callbacks of the list being cleared.

        This internal method is called by the clear method.
        It notifies both specific clear callbacks and general change callbacks.

        Args:
            items: The items that were cleared.
        """
        # Call specific callbacks
        for callback in self._clear_callbacks:
            callback(items)

        # Call general change callbacks
        change = ObservableListChange(type=ObservableCollectionChangeType.CLEAR, items=items)
        for callback in self._change_callbacks:
            callback(change)
