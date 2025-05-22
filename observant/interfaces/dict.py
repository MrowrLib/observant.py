from abc import ABC, abstractmethod
from typing import Callable, Generic, Iterator, TypeVar

from observant.types.dict_change import ObservableDictChange

TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


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
    def on_change(
        self, callback: Callable[[ObservableDictChange[TKey, TValue]], None]
    ) -> None:
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
