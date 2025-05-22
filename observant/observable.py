from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Generic, Protocol, TypeVar, runtime_checkable

H = TypeVar("H", contravariant=True)


@runtime_checkable
class SupportsLessThan(Protocol[H]):
    def __lt__(self, other: H) -> bool: ...


class Comparable(SupportsLessThan["Comparable"], Protocol):
    pass


ComparableOrPrimitive = Comparable | str | int | float | bool | None


T = TypeVar("T")


@dataclass
class Observable(Generic[T]):
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

    def set_if_changed(self, value: T) -> None:
        if self._value != value:
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
