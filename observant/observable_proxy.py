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

        # Validation related fields
        self._validators: dict[str, list[Callable[[Any], str | None]]] = {}
        self._validation_errors_dict = ObservableDict[str, list[str]]({})
        self._validation_for_cache: dict[str, Observable[list[str]]] = {}
        self._is_valid_obs = Observable[bool](True)

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
            # Register validation callback
            obs.on_change(lambda v: self._validate_field(attr, v))
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
            # Register validation callback
            obs.on_change(lambda _: self._validate_field(attr, obs.copy()))
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
            # Register validation callback
            obs.on_change(lambda _: self._validate_field(attr, obs.copy()))
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

    @override
    def add_validator(
        self,
        attr: str,
        validator: Callable[[Any], str | None],
    ) -> None:
        """
        Add a validator function for a field.

        Args:
            attr: The field name to validate.
            validator: A function that takes the field value and returns an error message
                       if invalid, or None if valid.
        """
        if attr not in self._validators:
            self._validators[attr] = []

        self._validators[attr].append(validator)

        # Validate the current value if it exists
        self._validate_field_if_exists(attr)

    def _validate_field_if_exists(self, attr: str) -> None:
        """
        Validate a field if it exists in any of the observable collections.
        """
        # Check in scalars
        for key in self._scalars:
            if key.attr == attr:
                value = self._scalars[key].get()
                self._validate_field(attr, value)
                return

        # Check in lists
        for key in self._lists:
            if key.attr == attr:
                value = self._lists[key].copy()
                self._validate_field(attr, value)
                return

        # Check in dicts
        for key in self._dicts:
            if key.attr == attr:
                value = self._dicts[key].copy()
                self._validate_field(attr, value)
                return

        # If we get here, the field doesn't exist in any observable collection yet
        # Try to get it directly from the object
        try:
            value = getattr(self._obj, attr)
            self._validate_field(attr, value)
        except (AttributeError, TypeError):
            # If we can't get the value, we can't validate it yet
            pass

    def _validate_field(self, attr: str, value: Any) -> None:
        """
        Validate a field value against all its validators.

        Args:
            attr: The field name.
            value: The value to validate.
        """
        if attr not in self._validators:
            # No validators for this field, it's always valid
            if attr in self._validation_errors_dict:
                del self._validation_errors_dict[attr]
            return

        errors: list[str] = []

        for validator in self._validators[attr]:
            try:
                result = validator(value)
                if result is not None:
                    errors.append(result)
            except Exception as e:
                errors.append(f"Validation error: {str(e)}")

        if errors:
            self._validation_errors_dict[attr] = errors
        elif attr in self._validation_errors_dict:
            del self._validation_errors_dict[attr]

        # Update the is_valid observable
        self._is_valid_obs.set(len(self._validation_errors_dict) == 0)

    @override
    def is_valid(self) -> IObservable[bool]:
        """
        Get an observable that indicates whether all fields are valid.

        Returns:
            An observable that emits True if all fields are valid, False otherwise.
        """
        return self._is_valid_obs

    @override
    def validation_errors(self) -> IObservableDict[str, list[str]]:
        """
        Get an observable dictionary of validation errors.

        Returns:
            An observable dictionary mapping field names to lists of error messages.
        """
        return self._validation_errors_dict

    @override
    def validation_for(self, attr: str) -> IObservable[list[str]]:
        """
        Get an observable list of validation errors for a specific field.

        Args:
            attr: The field name to get validation errors for.

        Returns:
            An observable that emits a list of error messages for the field.
            An empty list means the field is valid.
        """
        if attr not in self._validation_for_cache:
            # Create a computed observable that depends on the validation errors dict
            initial_value = self._validation_errors_dict.get(attr) or []
            obs = Observable[list[str]](initial_value)

            # Update the observable when the validation errors dict changes
            def update_validation(_: Any) -> None:
                new_value = self._validation_errors_dict.get(attr) or []
                current = obs.get()
                if new_value != current:
                    obs.set(new_value)

            self._validation_errors_dict.on_change(update_validation)
            self._validation_for_cache[attr] = obs

        return self._validation_for_cache[attr]
