from dataclasses import dataclass, field
from typing import Callable, Generic, TypeVar, override

from observant.interfaces.observable import IObservable

T = TypeVar("T")


@dataclass
class Observable(Generic[T], IObservable[T]):
    _value: T
    _callbacks: list[Callable[[T], None]] = field(default_factory=list[Callable[[T], None]])

    @override
    def get(self) -> T:
        """
        Get the current value of the observable.

        Returns:
            The current value.
        """
        return self._value

    @override
    def set(self, value: T) -> None:
        """
        Set a new value for the observable and notify all registered callbacks.

        Args:
            value: The new value to set.
        """
        self._value = value
        for callback in self._callbacks:
            callback(value)

    @override
    def on_change(self, callback: Callable[[T], None]) -> None:
        """
        Register a callback function to be called when the value changes.

        Args:
            callback: A function that takes the new value as its argument.
        """
        self._callbacks.append(callback)
