from typing import Callable, Generic, TypeVar, override

from observant.interfaces.observable import IObservable

T = TypeVar("T")


class Observable(Generic[T], IObservable[T]):
    """
    A generic observable value that notifies listeners when its value changes.

    Observable is the core building block of Observant's reactive system. It wraps
    a single value and provides methods to get, set, and observe changes to that value.

    Attributes:
        _value: The current value of the observable.
        _callbacks: List of callback functions to be called when the value changes.
        _on_change_enabled: Whether callbacks are enabled.

    Examples:
        ```python
        # Create an observable integer
        counter = Observable[int](0)

        # Register a callback to be notified when the value changes
        counter.on_change(lambda value: print(f"Counter changed to {value}"))

        # Update the value
        counter.set(1)  # Prints: "Counter changed to 1"

        # Get the current value
        current_value = counter.get()  # Returns: 1
        ```
    """

    _value: T
    _callbacks: list[Callable[[T], None]]
    _on_change_enabled: bool = True

    def __init__(self, value: T, *, on_change: Callable[[T], None] | None = None, on_change_enabled: bool = True) -> None:
        """
        Initialize the Observable with a value.

        Args:
            value: The initial value of the observable.
            on_change: Optional callback function to register immediately.
            on_change_enabled: Whether callbacks should be enabled initially.
        """
        self._value = value
        self._callbacks = []
        self._on_change_enabled = on_change_enabled

    @override
    def get(self) -> T:
        """
        Get the current value of the observable.

        Returns:
            The current value stored in this observable.

        Examples:
            ```python
            counter = Observable[int](0)
            value = counter.get()  # Returns: 0
            ```
        """
        return self._value

    @override
    def set(self, value: T, notify: bool = True) -> None:
        """
        Set a new value for the observable and notify all registered callbacks.

        This method updates the internal value and, if notify is True and callbacks
        are enabled, calls all registered callbacks with the new value.

        Args:
            value: The new value to set.
            notify: Whether to notify the callbacks after setting the value.

        Examples:
            ```python
            counter = Observable[int](0)
            counter.on_change(lambda value: print(f"Counter changed to {value}"))

            # Update with notification
            counter.set(1)  # Prints: "Counter changed to 1"

            # Update without notification
            counter.set(2, notify=False)  # No output
            ```
        """
        self._value = value

        if not notify or not self._on_change_enabled:
            return

        for callback in self._callbacks:
            callback(value)

    @override
    def on_change(self, callback: Callable[[T], None]) -> None:
        """
        Register a callback function to be called when the value changes.

        The callback will be called with the new value whenever set() is called
        with notify=True and callbacks are enabled. Callbacks are called in the
        order they were registered.

        If the same callback function is registered multiple times, it will only
        be added once.

        Args:
            callback: A function that takes the new value as its argument.

        Examples:
            ```python
            counter = Observable[int](0)

            # Register a callback
            counter.on_change(lambda value: print(f"Counter changed to {value}"))

            # Register another callback
            counter.on_change(lambda value: print(f"Counter is now {value}"))

            # Update the value
            counter.set(1)
            # Prints:
            # "Counter changed to 1"
            # "Counter is now 1"
            ```
        """
        # Check if this callback is already registered to avoid duplicates
        for existing_cb in self._callbacks:
            if existing_cb == callback:
                return

        self._callbacks.append(callback)

    @override
    def enable(self) -> None:
        """
        Enable the observable to notify changes.

        After calling this method, subsequent calls to set() with notify=True
        will trigger callbacks.

        Examples:
            ```python
            counter = Observable[int](0)
            counter.on_change(lambda value: print(f"Counter changed to {value}"))

            # Disable notifications
            counter.disable()
            counter.set(1)  # No output

            # Enable notifications
            counter.enable()
            counter.set(2)  # Prints: "Counter changed to 2"
            ```
        """
        self._on_change_enabled = True

    @override
    def disable(self) -> None:
        """
        Disable the observable from notifying changes.

        After calling this method, subsequent calls to set() will not trigger
        callbacks, even if notify=True.

        Examples:
            ```python
            counter = Observable[int](0)
            counter.on_change(lambda value: print(f"Counter changed to {value}"))

            # Disable notifications
            counter.disable()
            counter.set(1)  # No output
            ```
        """
        self._on_change_enabled = False

    def __bool__(self) -> bool:
        """
        Convert the observable to a boolean.

        This allows using the observable directly in boolean contexts.

        Returns:
            The boolean value of the current value.

        Examples:
            ```python
            counter = Observable[int](0)
            if not counter:
                print("Counter is zero")  # This will print

            counter.set(1)
            if counter:
                print("Counter is non-zero")  # This will print
            ```
        """
        return bool(self.get())

    @override
    def __str__(self) -> str:
        """
        Convert the observable to a string.

        This allows using the observable directly in string contexts.

        Returns:
            The string representation of the current value.

        Examples:
            ```python
            counter = Observable[int](42)
            print(f"The counter is {counter}")  # Prints: "The counter is 42"
            ```
        """
        return str(self.get())

    @override
    def __repr__(self) -> str:
        """
        Get the representation of the observable.

        Returns:
            A string representation of the observable, including its class name
            and current value.

        Examples:
            ```python
            counter = Observable[int](42)
            repr(counter)  # Returns: "Observable(42)"
            ```
        """
        return f"{self.__class__.__name__}({self.get()!r})"
