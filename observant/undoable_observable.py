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

    @override
    def set(self, value: T) -> None:
        old_value = self.get()
        if old_value != value:
            self._proxy.track_scalar_change(self._attr, old_value, value)
        super().set(value)
