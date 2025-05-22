from abc import ABC
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from observant.observable import Observable
from observant.observable_dict import ObservableDict
from observant.observable_list import ObservableList

T = TypeVar("T")


@dataclass(frozen=True)
class FieldKey:
    attr: str
    sync: bool


# TODO
class IObservableProxy(Generic[T], ABC):
    pass


class ObservableProxy(Generic[T]):
    """
    Proxy for a data object that exposes its fields as Observable, ObservableList, or ObservableDict.
    Provides optional sync behavior to automatically write back to the source model.
    """

    def __init__(self, obj: T, *, sync: bool) -> None:
        """
        Args:
            obj: The object to proxy.
            sync: If True, observables will sync back to the model immediately. If False, changes must be saved explicitly.
        """
        self._obj = obj
        self._sync_default = sync

        self._scalars: dict[FieldKey, Observable[Any]] = {}
        self._lists: dict[FieldKey, ObservableList[Any]] = {}
        self._dicts: dict[FieldKey, ObservableDict[Any, Any]] = {}

    def observable(
        self,
        typ: type[T],
        attr: str,
        *,
        sync: bool | None = None,
    ) -> Observable[T]:
        """
        Get or create an Observable[T] for a scalar field.
        """
        sync = self._sync_default if sync is None else sync
        key = FieldKey(attr, sync)

        if key not in self._scalars:
            val = getattr(self._obj, attr)
            obs = Observable(val)
            if sync:
                obs.on_change(lambda v: setattr(self._obj, attr, v))
            self._scalars[key] = obs

        return self._scalars[key]

    def observable_list(
        self,
        typ: type[T],
        attr: str,
        *,
        sync: bool | None = None,
    ) -> ObservableList[T]:
        """
        Get or create an ObservableList[T] for a list field.
        """
        sync = self._sync_default if sync is None else sync
        key = FieldKey(attr, sync)

        if key not in self._lists:
            val_raw = getattr(self._obj, attr)
            val: list[T] = cast(list[T], val_raw)
            obs = ObservableList(val, copy=not sync)
            if sync:
                obs.on_change(lambda _: setattr(self._obj, attr, obs.copy()))
            self._lists[key] = obs

        return self._lists[key]

    def observable_dict(
        self,
        attr: str,
        *,
        sync: bool | None = None,
    ) -> ObservableDict[Any, Any]:
        """
        Get or create an ObservableDict for a dict field.
        """
        sync = self._sync_default if sync is None else sync
        key = FieldKey(attr, sync)

        if key not in self._dicts:
            val_raw = getattr(self._obj, attr)
            val: dict[Any, Any] = cast(dict[Any, Any], val_raw)
            obs = ObservableDict(val, copy=not sync)
            if sync:
                obs.on_change(lambda _: setattr(self._obj, attr, obs.copy()))
            self._dicts[key] = obs

        return self._dicts[key]

    def get(self) -> T:
        """
        Get the original object being proxied.
        """
        return self._obj

    def update(self, **kwargs: T) -> None:
        """
        Set one or more scalar observable values.
        """
        for attr, value in kwargs.items():
            self.observable(type(value), attr).set(value)

    def load_dict(self, values: dict[str, T]) -> None:
        """
        Set multiple scalar observable values from a dict.
        """
        for attr, value in values.items():
            self.observable(type(value), attr).set(value)

    def save_to(self, obj: T) -> None:
        """
        Write all observable values back into the given object.
        """
        for key, obs in self._scalars.items():
            setattr(obj, key.attr, obs.get())

        for key, obs in self._lists.items():
            setattr(obj, key.attr, obs.copy())

        for key, obs in self._dicts.items():
            setattr(obj, key.attr, obs.copy())
