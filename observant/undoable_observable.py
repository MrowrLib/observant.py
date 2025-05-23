from typing import Generic, TypeVar, override

from observant.interfaces.proxy import IObservableProxy
from observant.observable import Observable

T = TypeVar("T")
TValue = TypeVar("TValue")


class UndoableObservable(Observable[T], Generic[T]):
    def __init__(self, value: T, attr: str, proxy: IObservableProxy[TValue], *, on_change_enabled: bool = True) -> None:
        super().__init__(value, on_change_enabled=on_change_enabled)
        self._attr = attr
        self._proxy = proxy
        self._is_undoing = False  # Flag to prevent recursive tracking during undo/redo

    @override
    def set(self, value: T, notify: bool = True) -> None:
        old_value = self.get()

        # Only track changes if not already undoing and notify is True
        if old_value != value and notify and not self._is_undoing:
            self._proxy.track_scalar_change(self._attr, old_value, value)

        super().set(value, notify=notify)

    def set_undoing(self, is_undoing: bool) -> None:
        """Set the undoing flag to prevent recursive tracking during undo/redo."""
        self._is_undoing = is_undoing
