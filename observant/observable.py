from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Generic, TypeVar

from observant.interfaces.observable import IObservable

T = TypeVar("T")


@dataclass
class Observable(Generic[T], IObservable[T]):
    _value: T
    _callbacks: list[Callable[[T], None]] = field(
        default_factory=list[Callable[[T], None]]
    )

    def get(self) -> T:
        return self._value

    def set(self, value: T) -> None:
        self._value = value
        for callback in self._callbacks:
            callback(value)

    def on_change(self, callback: Callable[[T], None]) -> None:
        self._callbacks.append(callback)


class ObservableCollectionChangeType(Enum):
    """Type of change that occurred in a collection."""

    ADD = auto()
    REMOVE = auto()
    CLEAR = auto()
    UPDATE = auto()  # For dictionaries, when a value is updated
