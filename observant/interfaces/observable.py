from enum import Enum, auto
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class IObservable(Generic[T]):
    def get(self) -> T: ...

    def set(self, value: T) -> None: ...

    def set_if_changed(self, value: T) -> None: ...

    def on_change(self, callback: Callable[[T], None]) -> None: ...


class ObservableCollectionChangeType(Enum):
    """Type of change that occurred in a collection."""

    ADD = auto()
    REMOVE = auto()
    CLEAR = auto()
    UPDATE = auto()  # For dictionaries, when a value is updated
