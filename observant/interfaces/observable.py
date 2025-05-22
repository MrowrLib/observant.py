from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class IObservable(Generic[T]):
    def get(self) -> T:
        """
        Get the current value of the observable.

        Returns:
            The current value.
        """
        ...

    def set(self, value: T, notify: bool = True) -> None:
        """
        Set a new value for the observable and notify all registered callbacks.

        Args:
            value: The new value to set.
            notify: Whether to notify the callbacks after setting the value.
        """
        ...

    def on_change(self, callback: Callable[[T], None]) -> None:
        """
        Register a callback function to be called when the value changes.

        Args:
            callback: A function that takes the new value as its argument.
        """
        ...

    def enable(self) -> None:
        """
        Enable the observable to notify changes.
        """
        ...

    def disable(self) -> None:
        """
        Disable the observable from notifying changes.
        """
        ...
