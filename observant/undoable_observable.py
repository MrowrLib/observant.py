from typing import Generic, TypeVar, override

from observant.interfaces.proxy import IObservableProxy
from observant.observable import Observable

T = TypeVar("T")
TValue = TypeVar("TValue")


class UndoableObservable(Observable[T], Generic[T]):
    """
    An observable that tracks changes for undo/redo functionality.

    UndoableObservable extends Observable to add undo/redo support. It tracks
    value changes and reports them to an ObservableProxy, which manages the
    undo/redo stacks.

    This class is typically not instantiated directly by users, but is created
    internally by ObservableProxy when undo functionality is enabled.

    Attributes:
        _attr: The attribute name this observable is tracking.
        _proxy: The proxy that manages undo/redo for this observable.
        _is_undoing: Flag to prevent recursive tracking during undo/redo operations.
    """

    def __init__(self, value: T, attr: str, proxy: IObservableProxy[TValue], *, on_change_enabled: bool = True) -> None:
        """
        Initialize an UndoableObservable with a value, attribute name, and proxy.

        Args:
            value: The initial value of the observable.
            attr: The attribute name this observable is tracking.
            proxy: The proxy that manages undo/redo for this observable.
            on_change_enabled: Whether callbacks should be enabled initially.
        """
        super().__init__(value, on_change_enabled=on_change_enabled)
        self._attr = attr
        self._proxy = proxy
        self._is_undoing = False  # Flag to prevent recursive tracking during undo/redo

    @override
    def set(self, value: T, notify: bool = True) -> None:
        """
        Set a new value and track the change for undo/redo if appropriate.

        This method extends the base Observable.set() method to track changes
        for undo/redo functionality. Changes are only tracked if:
        - The new value is different from the old value
        - notify is True (changes with notify=False are not tracked)
        - _is_undoing is False (prevents recursive tracking during undo/redo)

        Args:
            value: The new value to set.
            notify: Whether to notify callbacks and track for undo/redo.
        """
        old_value = self.get()

        # Only track changes if not already undoing and notify is True
        if old_value != value and notify and not self._is_undoing:
            self._proxy.track_scalar_change(self._attr, old_value, value)

        super().set(value, notify=notify)

    def set_undoing(self, is_undoing: bool) -> None:
        """
        Set the undoing flag to prevent recursive tracking during undo/redo.

        This method is called by ObservableProxy before and after performing
        undo/redo operations to prevent those operations from being tracked
        as new changes.

        Args:
            is_undoing: Whether an undo/redo operation is in progress.
        """
        self._is_undoing = is_undoing
