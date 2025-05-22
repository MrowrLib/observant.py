from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Iterator, TypeVar, overload

from observant.types.list_change import ObservableListChange

T = TypeVar("T")


class IObservableList(Generic[T], ABC):
    """Interface for observable lists with specific event types."""

    @abstractmethod
    def __len__(self) -> int:
        """Return the number of items in the list."""
        ...

    @abstractmethod
    def __getitem__(self, index: int | slice) -> T | list[T]:
        """Get an item or slice of items from the list."""
        ...

    @abstractmethod
    def __setitem__(self, index: int | slice, value: T | list[T]) -> None:
        """Set an item or slice of items in the list."""
        ...

    @abstractmethod
    def __delitem__(self, index: int | slice) -> None:
        """Delete an item or slice of items from the list."""
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the items in the list."""
        ...

    @abstractmethod
    def __contains__(self, item: T) -> bool:
        """Check if an item is in the list."""
        ...

    @abstractmethod
    def append(self, item: T) -> None:
        """Add an item to the end of the list."""
        ...

    @abstractmethod
    def extend(self, items: list[T]) -> None:
        """Extend the list by appending all items from the iterable."""
        ...

    @abstractmethod
    def insert(self, index: int, item: T) -> None:
        """Insert an item at a given position."""
        ...

    @abstractmethod
    def remove(self, item: T) -> None:
        """Remove the first occurrence of an item from the list."""
        ...

    @abstractmethod
    def pop(self, index: int = -1) -> T:
        """Remove and return an item at a given position."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all items from the list."""
        ...

    @abstractmethod
    def index(self, item: T, start: int = 0, end: int | None = None) -> int:
        """Return the index of the first occurrence of an item."""
        ...

    @abstractmethod
    def count(self, item: T) -> int:
        """Return the number of occurrences of an item in the list."""
        ...

    @overload
    def sort(self, *, key: None = None, reverse: bool = False) -> None: ...

    @overload
    def sort(self, *, key: Callable[[T], Any], reverse: bool = False) -> None: ...

    @abstractmethod
    def sort(
        self,
        *,
        key: Callable[[T], Any] | None = None,
        reverse: bool = False,
    ) -> None: ...

    @abstractmethod
    def reverse(self) -> None:
        """Reverse the list in place."""
        ...

    @abstractmethod
    def copy(self) -> list[T]:
        """Return a shallow copy of the list."""
        ...

    @abstractmethod
    def on_change(self, callback: Callable[[ObservableListChange[T]], None]) -> None:
        """Register for all change events with detailed information."""
        ...

    @abstractmethod
    def on_add(self, callback: Callable[[T, int], None]) -> None:
        """Register for add events with item and index."""
        ...

    @abstractmethod
    def on_remove(self, callback: Callable[[T, int], None]) -> None:
        """Register for remove events with item and index."""
        ...

    @abstractmethod
    def on_clear(self, callback: Callable[[list[T]], None]) -> None:
        """Register for clear events with the cleared items."""
        ...
