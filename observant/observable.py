from typing import Callable, Generic, TypeVar, override

from observant.interfaces.observable import IObservable

T = TypeVar("T")


class Observable(Generic[T], IObservable[T]):
    _value: T
    _callbacks: list[Callable[[T], None]]
    _on_change_enabled: bool = True

    def __init__(self, value: T, *, on_change: Callable[[T], None] | None = None, on_change_enabled: bool = True) -> None:
        """
        Initialize the Observable with a value.

        Args:
            value: The initial value of the observable.
        """
        print(f"DEBUG: Observable.__init__ called with value {value}")
        self._value = value
        self._callbacks = []
        self._on_change_enabled = on_change_enabled
        print("DEBUG: Observable.__init__ - Initialized with empty callbacks list")

    @override
    def get(self) -> T:
        """
        Get the current value of the observable.

        Returns:
            The current value.
        """
        return self._value

    @override
    def set(self, value: T, notify: bool = True) -> None:
        """
        Set a new value for the observable and notify all registered callbacks.

        Args:
            value: The new value to set.
            notify: Whether to notify the callbacks after setting the value.
        """
        print(f"DEBUG: Observable.set called with value {value}")
        self._value = value

        if not notify or not self._on_change_enabled:
            print("DEBUG: Observable.set - on_change is disabled, skipping callbacks")
            return

        print(f"DEBUG: Observable.set - Notifying {len(self._callbacks)} callbacks")
        for i, callback in enumerate(self._callbacks):
            print(f"DEBUG: Observable.set - Calling callback {i}")
            callback(value)
            print(f"DEBUG: Observable.set - Callback {i} completed")
        print("DEBUG: Observable.set - Completed")

    @override
    def on_change(self, callback: Callable[[T], None]) -> None:
        """
        Register a callback function to be called when the value changes.

        Args:
            callback: A function that takes the new value as its argument.
        """
        print(f"DEBUG: Observable.on_change called, current callbacks: {len(self._callbacks)}")
        # Check if this callback is already registered to avoid duplicates
        for existing_cb in self._callbacks:
            if existing_cb == callback:
                print("DEBUG: Observable.on_change - Callback already registered, skipping")
                return

        self._callbacks.append(callback)
        print(f"DEBUG: Observable.on_change - Added callback, now have {len(self._callbacks)} callbacks")

    @override
    def enable(self) -> None:
        """
        Enable the observable to notify changes.
        """
        print("DEBUG: Observable.enable called")
        self._on_change_enabled = True

    @override
    def disable(self) -> None:
        """
        Disable the observable from notifying changes.
        """
        print("DEBUG: Observable.disable called")
        self._on_change_enabled = False

    def __bool__(self) -> bool:
        """
        Convert the observable to a boolean.

        Returns:
            The boolean value of the current value.
        """
        return bool(self.get())

    @override
    def __str__(self) -> str:
        """
        Convert the observable to a string.

        Returns:
            The string representation of the current value.
        """
        return str(self.get())

    @override
    def __repr__(self) -> str:
        """
        Get the representation of the observable.

        Returns:
            A string representation of the observable.
        """
        return f"{self.__class__.__name__}({self.get()!r})"
