from typing import Any, Callable, Generic, TypeVar, cast, override

from observant.interfaces.dict import IObservableDict
from observant.interfaces.list import IObservableList
from observant.interfaces.observable import IObservable
from observant.interfaces.proxy import IObservableProxy
from observant.observable import Observable
from observant.observable_dict import ObservableDict
from observant.observable_list import ObservableList
from observant.types.proxy_field_key import ProxyFieldKey

T = TypeVar("T")
TValue = TypeVar("TValue")
TDictKey = TypeVar("TDictKey")
TDictValue = TypeVar("TDictValue")


class ObservableProxy(Generic[T], IObservableProxy[T]):
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

        self._scalars: dict[ProxyFieldKey, Observable[Any]] = {}
        self._lists: dict[ProxyFieldKey, ObservableList[Any]] = {}
        self._dicts: dict[ProxyFieldKey, ObservableDict[Any, Any]] = {}
        self._computeds: dict[str, Observable[Any]] = {}
        self._dirty_fields: set[str] = set()

    @override
    def observable(
        self,
        typ: type[TValue],
        attr: str,
        *,
        sync: bool | None = None,
    ) -> IObservable[TValue]:
        """
        Get or create an Observable[T] for a scalar field.
        """
        sync = self._sync_default if sync is None else sync
        key = ProxyFieldKey(attr, sync)

        if key not in self._scalars:
            val = getattr(self._obj, attr)
            obs = Observable(val)
            if sync:
                obs.on_change(lambda v: setattr(self._obj, attr, v))
            # Register dirty tracking callback
            obs.on_change(lambda _: self._dirty_fields.add(attr))
            self._scalars[key] = obs

        return self._scalars[key]

    @override
    def observable_list(
        self,
        typ: type[TValue],
        attr: str,
        *,
        sync: bool | None = None,
    ) -> IObservableList[TValue]:
        """
        Get or create an ObservableList[T] for a list field.
        """
        sync = self._sync_default if sync is None else sync
        key = ProxyFieldKey(attr, sync)

        if key not in self._lists:
            val_raw = getattr(self._obj, attr)
            val: list[T] = cast(list[T], val_raw)
            obs = ObservableList(val, copy=not sync)
            if sync:
                obs.on_change(lambda _: setattr(self._obj, attr, obs.copy()))
            # Register dirty tracking callback
            obs.on_change(lambda _: self._dirty_fields.add(attr))
            self._lists[key] = obs

        return self._lists[key]

    @override
    def observable_dict(
        self,
        typ: tuple[type[TDictKey], type[TDictValue]],
        attr: str,
        *,
        sync: bool | None = None,
    ) -> IObservableDict[TDictKey, TDictValue]:
        """
        Get or create an ObservableDict for a dict field.
        """
        sync = self._sync_default if sync is None else sync
        key = ProxyFieldKey(attr, sync)

        if key not in self._dicts:
            val_raw = getattr(self._obj, attr)
            val: dict[Any, Any] = cast(dict[Any, Any], val_raw)
            obs = ObservableDict(val, copy=not sync)
            if sync:
                obs.on_change(lambda _: setattr(self._obj, attr, obs.copy()))
            # Register dirty tracking callback
            obs.on_change(lambda _: self._dirty_fields.add(attr))
            self._dicts[key] = obs

        return self._dicts[key]

    @override
    def get(self) -> T:
        """
        Get the original object being proxied.
        """
        return self._obj

    @override
    def update(self, **kwargs: Any) -> None:
        """
        Set one or more scalar observable values.
        """
        for attr, value in kwargs.items():
            self.observable(object, attr).set(value)

    @override
    def load_dict(self, values: dict[str, Any]) -> None:
        """
        Set multiple scalar observable values from a dict.
        """
        for attr, value in values.items():
            self.observable(object, attr).set(value)

    @override
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

        # Reset dirty state after saving
        self.reset_dirty()

    @override
    def is_dirty(self) -> bool:
        """
        Check if any fields have been modified since initialization or last reset.

        Returns:
            True if any fields have been modified, False otherwise.
        """
        return bool(self._dirty_fields)

    @override
    def dirty_fields(self) -> set[str]:
        """
        Get the set of field names that have been modified.

        Returns:
            A set of field names that have been modified.
        """
        return set(self._dirty_fields)

    @override
    def reset_dirty(self) -> None:
        """
        Reset the dirty state of all fields.
        """
        self._dirty_fields.clear()

    @override
    def register_computed(
        self,
        name: str,
        compute: Callable[[], TValue],
        dependencies: list[str],
    ) -> None:
        """
        Register a computed property that depends on other observables.

        Args:
            name: The name of the computed property.
            compute: A function that returns the computed value.
            dependencies: List of field names that this computed property depends on.
        """
        # Create an observable for the computed property
        initial_value = compute()
        obs = Observable(initial_value)
        self._computeds[name] = obs

        # Register callbacks for each dependency
        for dep in dependencies:
            # For scalar dependencies
            def update_computed(_: Any) -> None:
                new_value = compute()
                current = obs.get()
                if new_value != current:
                    obs.set(new_value)

            # Try to find the dependency in scalars, lists, or dicts
            for sync in [True, False]:
                key = ProxyFieldKey(dep, sync)

                if key in self._scalars:
                    self._scalars[key].on_change(update_computed)
                    break

                if key in self._lists:
                    self._lists[key].on_change(update_computed)
                    break

                if key in self._dicts:
                    self._dicts[key].on_change(update_computed)
                    break

            # Check if the dependency is another computed property
            if dep in self._computeds:
                self._computeds[dep].on_change(update_computed)

    @override
    def computed(
        self,
        typ: type[TValue],
        name: str,
    ) -> IObservable[TValue]:
        """
        Get a computed property by name.

        Args:
            typ: The type of the computed property.
            name: The name of the computed property.

        Returns:
            An observable containing the computed value.
        """
        if name not in self._computeds:
            raise KeyError(f"Computed property '{name}' not found")

        return self._computeds[name]
