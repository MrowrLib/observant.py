from typing import Any, Callable, Generic, Iterator, TypeVar, cast, override

from observant.interfaces.list import IObservableList, ObservableListChange
from observant.types.collection_change_type import ObservableCollectionChangeType

T = TypeVar("T")


class ObservableListBase(Generic[T], IObservableList[T]):
    """Base implementation that can work with an external list or create its own."""

    def __init__(self, items: list[T] | None = None, *, copy: bool = False):
        """
        Initialize with optional external list reference.

        Args:
            items: Optional external list to observe. If None, creates a new list.
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
        """Return the number of items in the list."""
        return len(self._items)

    @override
    def __getitem__(self, index: int | slice) -> T | list[T]:
        """Get an item or slice of items from the list."""
        return self._items[index]

    @override
    def __setitem__(self, index: int | slice, value: T | list[T]) -> None:
        """Set an item or slice of items in the list."""
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
        """Delete an item or slice of items from the list."""
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
        """Return an iterator over the items in the list."""
        return iter(self._items)

    @override
    def __contains__(self, item: T) -> bool:
        """Check if an item is in the list."""
        return item in self._items

    @override
    def append(self, item: T) -> None:
        """
        Add an item to the end of the list.

        Args:
            item: The item to add
        """
        self._items.append(item)
        self._notify_add(item, len(self._items) - 1)

    @override
    def extend(self, items: list[T]) -> None:
        """
        Extend the list by appending all items from the iterable.

        Args:
            items: The items to add
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

        Args:
            index: The position to insert the item
            item: The item to insert
        """
        self._items.insert(index, item)
        self._notify_add(item, index)

    @override
    def remove(self, item: T) -> None:
        """
        Remove the first occurrence of an item from the list.

        Args:
            item: The item to remove

        Raises:
            ValueError: If the item is not in the list
        """
        index = self._items.index(item)
        self._items.remove(item)
        self._notify_remove(item, index)

    @override
    def pop(self, index: int = -1) -> T:
        """
        Remove and return an item at a given position.

        Args:
            index: The position to remove the item from (default is -1, which is the last item)

        Returns:
            The removed item
        """
        item = self._items[index]
        self._items.pop(index)
        self._notify_remove(item, index)
        return item

    @override
    def clear(self) -> None:
        """Remove all items from the list."""
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
            item: The item to find
            start: The start index to search from
            end: The end index to search to

        Returns:
            The index of the item

        Raises:
            ValueError: If the item is not in the list
        """
        if end is None:
            return self._items.index(item, start)
        return self._items.index(item, start, end)

    @override
    def count(self, item: T) -> int:
        """
        Return the number of occurrences of an item in the list.

        Args:
            item: The item to count

        Returns:
            The number of occurrences
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

        Args:
            key: A function that takes an item and returns a key for sorting
            reverse: Whether to sort in reverse order
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
        """Reverse the list in place."""
        self._items.reverse()
        # No notification needed as the items themselves haven't changed

    @override
    def copy(self) -> list[T]:
        """
        Return a shallow copy of the list.

        Returns:
            A copy of the list
        """
        return self._items.copy()

    @override
    def on_change(self, callback: Callable[[ObservableListChange[T]], None]) -> None:
        """
        Add a callback to be called when the list changes.

        Args:
            callback: A function that takes a ListChange object
        """
        self._change_callbacks.append(callback)

    @override
    def on_add(self, callback: Callable[[T, int], None]) -> None:
        """
        Register for add events with item and index.

        Args:
            callback: A function that takes an item and its index
        """
        self._add_callbacks.append(callback)

    @override
    def on_remove(self, callback: Callable[[T, int], None]) -> None:
        """
        Register for remove events with item and index.

        Args:
            callback: A function that takes an item and its index
        """
        self._remove_callbacks.append(callback)

    @override
    def on_clear(self, callback: Callable[[list[T]], None]) -> None:
        """
        Register for clear events with the cleared items.

        Args:
            callback: A function that takes a list of cleared items
        """
        self._clear_callbacks.append(callback)

    def _notify_add(self, item: T, index: int) -> None:
        """
        Notify all callbacks of an item being added.

        Args:
            item: The item that was added
            index: The index where the item was added
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

        Args:
            items: The items that were added
            start_index: The index where the items were added
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

        Args:
            item: The item that was removed
            index: The index where the item was removed
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

        Args:
            items: The items that were removed
            start_index: The index where the items were removed
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

        Args:
            items: The items that were cleared
        """
        # Call specific callbacks
        for callback in self._clear_callbacks:
            callback(items)

        # Call general change callbacks
        change = ObservableListChange(type=ObservableCollectionChangeType.CLEAR, items=items)
        for callback in self._change_callbacks:
            callback(change)


class ObservableList(ObservableListBase[T]):
    """A list that notifies observers when items are added or removed."""

    def __init__(self, initial_items: list[T] | None = None, *, copy: bool = False):
        """
        Initialize an ObservableList.

        Args:
            initial_items: Initial items to add to the list
        """
        super().__init__(initial_items, copy=copy)
