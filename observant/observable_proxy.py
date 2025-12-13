import time
from typing import Any, Callable, Generic, TypeVar, cast, override

from observant.interfaces.dict import IObservableDict
from observant.interfaces.list import IObservableList
from observant.interfaces.observable import IObservable
from observant.interfaces.proxy import IObservableProxy
from observant.observable import Observable
from observant.observable_dict import ObservableDict
from observant.observable_list import ObservableList
from observant.types.collection_change_type import ObservableCollectionChangeType
from observant.types.proxy_field_key import ProxyFieldKey
from observant.types.undo_config import UndoConfig
from observant.undoable_observable import UndoableObservable

T = TypeVar("T")
TValue = TypeVar("TValue")
TDictKey = TypeVar("TDictKey")
TDictValue = TypeVar("TDictValue")


class _PathObservable(IObservable[Any]):
    """
    Observable wrapper for nested paths with optional chaining support.
    Provides two-way binding through the path.
    """

    def __init__(
        self,
        inner: Observable[Any],
        proxy: "ObservableProxy[Any]",
        segments: list[tuple[str, bool]],
    ):
        self._inner = inner
        self._proxy = proxy
        self._segments = segments

    def get(self) -> Any:
        return self._inner.get()

    def set(self, value: Any, notify: bool = True) -> None:
        # Try to set the value at the path
        current_obj: Any = self._proxy._obj
        for part, _ in self._segments[:-1]:
            if current_obj is None:
                return  # Can't set - path is broken
            current_obj = getattr(current_obj, part, None)
        if current_obj is None:
            return  # Can't set - path is broken
        setattr(current_obj, self._segments[-1][0], value)
        self._inner.set(value, notify)

    def on_change(self, callback: Callable[[Any], None]) -> None:
        self._inner.on_change(callback)

    def enable(self) -> None:
        self._inner.enable()

    def disable(self) -> None:
        self._inner.disable()


class ObservableProxy(Generic[T], IObservableProxy[T]):
    """
    Proxy for a data object that exposes its fields as Observable, ObservableList, or ObservableDict.

    ObservableProxy is the central class in the observant library, providing a reactive
    interface to any Python object. It wraps a data object and exposes its fields as
    observable properties that can be watched for changes.

    Key features:
    - Expose scalar fields as Observable objects
    - Expose list fields as ObservableList objects
    - Expose dictionary fields as ObservableDict objects
    - Optional synchronization with the source model
    - Validation with error tracking
    - Computed properties that depend on other observables
    - Undo/redo functionality with configurable history
    - Change tracking (dirty state)

    The proxy can be configured to automatically sync changes back to the source model,
    or to require explicit saving. It also supports undo/redo functionality with
    configurable history size and debounce timing.

    Attributes:
        _obj: The object being proxied.
        _sync_default: Whether to sync changes back to the model by default.
        _scalars: Dictionary of scalar observables.
        _lists: Dictionary of list observables.
        _dicts: Dictionary of dictionary observables.
        _computeds: Dictionary of computed observables.
        _dirty_fields: Set of field names that have been modified.
        _validators: Dictionary of validator functions for each field.
        _validation_errors_dict: Observable dictionary of validation errors.
        _validation_for_cache: Cache of validation observables for each field.
        _is_valid_obs: Observable indicating whether all fields are valid.
        _default_undo_config: Default undo configuration.
        _field_undo_configs: Dictionary of undo configurations for each field.
        _undo_stacks: Dictionary of undo stacks for each field.
        _redo_stacks: Dictionary of redo stacks for each field.
        _last_change_times: Dictionary of last change times for each field.
        _pending_undo_groups: Dictionary of pending undo groups for each field.
        _initial_values: Dictionary of initial values for each field.

    Examples:
        ```python
        from dataclasses import dataclass
        from observant import ObservableProxy

        @dataclass
        class User:
            name: str
            age: int
            tags: list[str]

        # Create a user object
        user = User(name="Alice", age=30, tags=["developer", "python"])

        # Create a proxy with automatic sync
        proxy = ObservableProxy(user, sync=True)

        # Get observables for fields
        name_obs = proxy.observable(str, "name")
        age_obs = proxy.observable(int, "age")
        tags_obs = proxy.observable_list(str, "tags")

        # Register change callbacks
        name_obs.on_change(lambda v: print(f"Name changed to {v}"))

        # Modify values through the observables
        name_obs.set("Bob")  # Prints: "Name changed to Bob"
        tags_obs.append("observant")

        # The original object is updated automatically with sync=True
        print(user.name)  # Prints: "Bob"
        print(user.tags)  # Prints: ["developer", "python", "observant"]
        ```
    """

    def __init__(
        self,
        obj: T,
        *,
        sync: bool = False,
        undo: bool = False,  # Undo is disabled by default
        undo_max: int | None = None,
        undo_debounce_ms: int | None = None,
    ) -> None:
        """
        Initialize a new ObservableProxy for a data object.

        Creates a proxy that wraps a data object and exposes its fields as observable
        properties. The proxy can be configured to automatically sync changes back to
        the source model, or to require explicit saving.

        Args:
            obj: The object to proxy. This can be any Python object with attributes.
            sync: If True, observables will sync back to the model immediately when changed.
                 If False, changes must be saved explicitly using save_to().
            undo: If True, enables undo/redo functionality for all fields.
                 Individual fields can override this setting.
            undo_max: Maximum number of undo steps to store per field.
                     None means unlimited (though default is 100 if not specified).
            undo_debounce_ms: Time window in milliseconds to group changes into a single undo step.
                             None means no debouncing (every change is a separate undo step).

        Examples:
            ```python
            # Create a proxy with no automatic sync
            user = User(name="Alice", age=30)
            proxy = ObservableProxy(user)

            # Create a proxy with automatic sync
            settings = Settings(theme="dark", font_size=12)
            proxy = ObservableProxy(settings, sync=True)

            # Create a proxy with undo/redo enabled
            document = Document(title="Draft", content="Hello world")
            proxy = ObservableProxy(document, undo=True, undo_max=50, undo_debounce_ms=500)
            ```
        """
        self._obj = obj
        self._sync_default = sync

        # Print a warning if sync and undo are both enabled
        if sync and undo:
            print("Warning: sync=True with undo=True may cause unexpected model mutations during undo/redo.")

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

        # Undo/redo related fields
        self._default_undo_config = UndoConfig(enabled=undo, undo_max=undo_max, undo_debounce_ms=undo_debounce_ms)
        self._field_undo_configs: dict[str, UndoConfig] = {}
        self._undo_stacks: dict[str, list[Callable[[], None]]] = {}
        self._redo_stacks: dict[str, list[Callable[[], None]]] = {}
        self._last_change_times: dict[str, float] = {}
        self._pending_undo_groups: dict[str, Callable[[], None] | None] = {}
        self._initial_values: dict[str, Any] = {}  # Store initial values for undo

        # Nested proxy support for observable_for_path
        self._nested_proxies: dict[str, "ObservableProxy[Any]"] = {}

    @override
    def observable(
        self,
        typ: type[TValue],
        attr: str,
        *,
        sync: bool | None = None,
        undo_max: int | None = None,
        undo_debounce_ms: int | None = None,
    ) -> IObservable[TValue]:
        """
        Get or create an Observable[T] for a scalar field.

        Creates or returns an existing Observable for a scalar field of the proxied object.
        The Observable allows watching for changes to the field value and modifying it.

        Args:
            typ: The type of the field.
            attr: The field name.
            sync: Whether to sync changes back to the model immediately.
                 If None, uses the default sync setting from the proxy.
            undo_max: Maximum number of undo steps to store. None means use the default.
            undo_debounce_ms: Time window in milliseconds to group changes. None means use the default.

        Returns:
            An Observable containing the field value.

        Examples:
            ```python
            # Get an observable for a string field
            name_obs = proxy.observable(str, "name")

            # Register a callback
            name_obs.on_change(lambda value: print(f"Name changed to {value}"))

            # Get the current value
            current_name = name_obs.get()

            # Set a new value
            name_obs.set("New Name")
            ```
        """
        sync = self._sync_default if sync is None else sync
        key = ProxyFieldKey(attr, sync)

        # Set up undo config if provided
        if undo_max is not None or undo_debounce_ms is not None:
            self.set_undo_config(attr, undo_max=undo_max, undo_debounce_ms=undo_debounce_ms)

        # Get the initial value
        val = getattr(self._obj, attr)

        if key not in self._scalars:
            # Create observable with callbacks disabled to prevent premature tracking
            # obs = Observable(val, on_change_enabled=False)
            obs = UndoableObservable(val, attr, self, on_change_enabled=False)

            # Store the observable first so it can be found by _track_scalar_change
            self._scalars[key] = obs

            if sync:
                obs.on_change(lambda v: setattr(self._obj, attr, v))
            # Register dirty tracking callback
            obs.on_change(lambda _: self._dirty_fields.add(attr))
            # Register validation callback
            obs.on_change(lambda v: self._validate_field(attr, v))
            # Undo tracking is now handled by UndoableObservable

            # Initial value tracking is now handled by UndoableObservable

            # Now enable callbacks for future changes
            obs.enable()
        else:
            # Get the existing observable
            obs = self._scalars[key]

        return self._scalars[key]

    @override
    def observable_list(
        self,
        typ: type[TValue],
        attr: str,
        *,
        sync: bool | None = None,
        undo_max: int | None = None,
        undo_debounce_ms: int | None = None,
    ) -> IObservableList[TValue]:
        """
        Get or create an ObservableList[T] for a list field.

        Creates or returns an existing ObservableList for a list field of the proxied object.
        The ObservableList provides the same interface as a regular Python list, but with
        change notification capabilities.

        Args:
            typ: The type of the list elements.
            attr: The field name.
            sync: Whether to sync changes back to the model immediately.
                 If None, uses the default sync setting from the proxy.
            undo_max: Maximum number of undo steps to store. None means use the default.
            undo_debounce_ms: Time window in milliseconds to group changes. None means use the default.

        Returns:
            An ObservableList containing the field value.

        Examples:
            ```python
            # Get an observable list for a tags field
            tags_obs = proxy.observable_list(str, "tags")

            # Register a callback
            tags_obs.on_change(lambda change: print(f"Tags changed: {change.type}"))

            # Modify the list
            tags_obs.append("new_tag")
            tags_obs.remove("old_tag")
            ```
        """
        sync = self._sync_default if sync is None else sync
        key = ProxyFieldKey(attr, sync)

        # Set up undo config if provided
        if undo_max is not None or undo_debounce_ms is not None:
            self.set_undo_config(attr, undo_max=undo_max, undo_debounce_ms=undo_debounce_ms)

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
            # Register undo tracking callback
            obs.on_change(lambda c: self._track_list_change(attr, c))
            self._lists[key] = obs

        return self._lists[key]

    @override
    def observable_dict(
        self,
        typ: tuple[type[TDictKey], type[TDictValue]],
        attr: str,
        *,
        sync: bool | None = None,
        undo_max: int | None = None,
        undo_debounce_ms: int | None = None,
    ) -> IObservableDict[TDictKey, TDictValue]:
        """
        Get or create an ObservableDict for a dict field.

        Creates or returns an existing ObservableDict for a dictionary field of the proxied object.
        The ObservableDict provides the same interface as a regular Python dictionary, but with
        change notification capabilities.

        Args:
            typ: A tuple of (key_type, value_type) for the dictionary.
            attr: The field name.
            sync: Whether to sync changes back to the model immediately.
                 If None, uses the default sync setting from the proxy.
            undo_max: Maximum number of undo steps to store. None means use the default.
            undo_debounce_ms: Time window in milliseconds to group changes. None means use the default.

        Returns:
            An ObservableDict containing the field value.

        Examples:
            ```python
            # Get an observable dict for a metadata field
            metadata_obs = proxy.observable_dict((str, str), "metadata")

            # Register a callback
            metadata_obs.on_change(lambda change: print(f"Metadata changed: {change.type}"))

            # Modify the dictionary
            metadata_obs["author"] = "Alice"
            del metadata_obs["draft"]
            ```
        """
        sync = self._sync_default if sync is None else sync
        key = ProxyFieldKey(attr, sync)

        # Set up undo config if provided
        if undo_max is not None or undo_debounce_ms is not None:
            self.set_undo_config(attr, undo_max=undo_max, undo_debounce_ms=undo_debounce_ms)

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
            # Register undo tracking callback
            obs.on_change(lambda c: self._track_dict_change(attr, c))
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

        This is a convenience method for setting multiple scalar values at once.
        It creates observables for any fields that don't already have them.

        Args:
            **kwargs: Keyword arguments where each key is a field name and each value
                     is the new value to set for that field.

        Examples:
            ```python
            # Update multiple fields at once
            proxy.update(name="Alice", age=30, active=True)
            ```
        """
        for attr, value in kwargs.items():
            self.observable(object, attr).set(value)

    @override
    def load_dict(self, values: dict[str, Any]) -> None:
        """
        Set multiple scalar observable values from a dict.

        This is similar to update(), but takes a dictionary instead of keyword arguments.
        It creates observables for any fields that don't already have them.

        Args:
            values: A dictionary where each key is a field name and each value
                   is the new value to set for that field.

        Examples:
            ```python
            # Load values from a dictionary
            data = {"name": "Alice", "age": 30, "active": True}
            proxy.load_dict(data)
            ```
        """
        for attr, value in values.items():
            self.observable(object, attr).set(value)

    @override
    def save_to(self, obj: T) -> None:
        """
        Write all observable values back into the given object.

        This method copies all values from the observables back to the target object.
        It's useful when sync=False and you want to explicitly save changes.

        Args:
            obj: The object to write values to. This can be the original object
                 or a different object of the same type.

        Examples:
            ```python
            # Create a proxy with no automatic sync
            user = User(name="Alice", age=30)
            proxy = ObservableProxy(user)

            # Make changes through the proxy
            proxy.observable(str, "name").set("Bob")

            # At this point, user.name is still "Alice"
            print(user.name)  # Prints: "Alice"

            # Save changes back to the original object
            proxy.save_to(user)
            print(user.name)  # Prints: "Bob"

            # Or save to a new object
            new_user = User(name="", age=0)
            proxy.save_to(new_user)
            print(new_user.name)  # Prints: "Bob"
            ```
        """
        for key, obs in self._scalars.items():
            setattr(obj, key.attr, obs.get())

        for key, obs in self._lists.items():
            setattr(obj, key.attr, obs.copy())

        for key, obs in self._dicts.items():
            setattr(obj, key.attr, obs.copy())

        # Save computed fields that shadow real fields
        for name, obs in self._computeds.items():
            try:
                # Check if the target object has this field
                getattr(obj, name)
                # If we get here, the field exists, so save the computed value
                setattr(obj, name, obs.get())
            except (AttributeError, TypeError):
                # Field doesn't exist in the target object, skip it
                pass

        # Reset dirty state after saving
        self.reset_dirty()

    @override
    def is_dirty(self) -> bool:
        """
        Check if any fields have been modified since initialization or last reset.

        This method returns True if any observable field has been modified since
        the proxy was created or since the last call to reset_dirty().

        Returns:
            True if any fields have been modified, False otherwise.

        Examples:
            ```python
            # Create a proxy
            user = User(name="Alice", age=30)
            proxy = ObservableProxy(user)

            # Check if dirty initially
            print(proxy.is_dirty())  # Prints: False

            # Make a change
            proxy.observable(str, "name").set("Bob")

            # Check if dirty after change
            print(proxy.is_dirty())  # Prints: True

            # Reset dirty state
            proxy.reset_dirty()

            # Check if dirty after reset
            print(proxy.is_dirty())  # Prints: False
            ```
        """
        return bool(self._dirty_fields)

    @override
    def dirty_fields(self) -> set[str]:
        """
        Get the set of field names that have been modified.

        This method returns a set containing the names of all fields that have been
        modified since the proxy was created or since the last call to reset_dirty().

        Returns:
            A set of field names that have been modified.

        Examples:
            ```python
            # Create a proxy
            user = User(name="Alice", age=30, active=True)
            proxy = ObservableProxy(user)

            # Make some changes
            proxy.observable(str, "name").set("Bob")
            proxy.observable(int, "age").set(31)

            # Get the dirty fields
            dirty = proxy.dirty_fields()
            print(dirty)  # Prints: {'name', 'age'}
            ```
        """
        return set(self._dirty_fields)

    @override
    def reset_dirty(self) -> None:
        """
        Reset the dirty state of all fields.

        This method clears the dirty state of all fields, marking them as clean.
        It's typically called after saving changes back to the model.

        Examples:
            ```python
            # Create a proxy
            user = User(name="Alice", age=30)
            proxy = ObservableProxy(user)

            # Make a change
            proxy.observable(str, "name").set("Bob")
            print(proxy.is_dirty())  # Prints: True

            # Reset dirty state
            proxy.reset_dirty()
            print(proxy.is_dirty())  # Prints: False
            ```
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

        Computed properties are read-only observables that automatically update
        when their dependencies change. They can depend on scalar fields, list fields,
        dictionary fields, or other computed properties.

        Args:
            name: The name of the computed property.
            compute: A function that returns the computed value.
            dependencies: List of field names that this computed property depends on.

        Examples:
            ```python
            # Create a proxy for a user object
            user = User(name="Alice", age=30)
            proxy = ObservableProxy(user)

            # Register a computed property for the user's greeting
            proxy.register_computed(
                name="greeting",
                compute=lambda: f"Hello, {proxy.observable(str, 'name').get()}!",
                dependencies=["name"]
            )

            # Get the computed property
            greeting_obs = proxy.computed(str, "greeting")
            print(greeting_obs.get())  # Prints: "Hello, Alice!"

            # When the name changes, the greeting updates automatically
            proxy.observable(str, "name").set("Bob")
            print(greeting_obs.get())  # Prints: "Hello, Bob!"
            ```
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

        # Validate the computed property when it changes
        def validate_computed(_: Any) -> None:
            value = compute()
            self._validate_field(name, value)

        obs.on_change(validate_computed)

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

        Validators are functions that check if a field value is valid.
        Multiple validators can be added for the same field.
        Validation errors are tracked and can be observed.

        Args:
            attr: The field name to validate.
            validator: A function that takes the field value and returns an error message
                       if invalid, or None if valid.

        Examples:
            ```python
            # Create a proxy for a user object
            user = User(name="Alice", age=30)
            proxy = ObservableProxy(user)

            # Add validators for the name field
            proxy.add_validator(
                "name",
                lambda name: "Name cannot be empty" if not name else None
            )
            proxy.add_validator(
                "name",
                lambda name: "Name too long" if len(name) > 50 else None
            )

            # Add a validator for the age field
            proxy.add_validator(
                "age",
                lambda age: "Age must be positive" if age < 0 else None
            )

            # Check if all fields are valid
            is_valid = proxy.is_valid()
            print(is_valid.get())  # Prints: True

            # Set an invalid value
            proxy.observable(str, "name").set("")
            print(is_valid.get())  # Prints: False

            # Get validation errors for a specific field
            name_errors = proxy.validation_for("name")
            print(name_errors.get())  # Prints: ["Name cannot be empty"]
            ```
        """
        if attr not in self._validators:
            self._validators[attr] = []

        self._validators[attr].append(validator)

        # Validate the current value if it exists
        self._validate_field_if_exists(attr)

    def _validate_field_if_exists(self, attr: str) -> None:
        """
        Validate a field if it exists in any of the observable collections.

        This method attempts to find the field in scalars, lists, or dicts collections,
        and if found, validates it. If the field is not found in any observable collection,
        it tries to get the value directly from the proxied object.

        Args:
            attr: The field name to validate.

        Note:
            This method is primarily used internally by the ObservableProxy class.
            Users typically don't need to call this method directly.
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

        This method returns an observable that emits True if all fields are valid
        according to their validators, and False if any field has validation errors.
        The observable updates automatically when field values change.

        Returns:
            An observable that emits True if all fields are valid, False otherwise.

        Examples:
            ```python
            # Create a proxy with validation
            user = User(name="Alice", age=30)
            proxy = ObservableProxy(user)

            # Add a validator
            proxy.add_validator("age", lambda age: "Age must be positive" if age < 0 else None)

            # Get the is_valid observable
            is_valid = proxy.is_valid()

            # Register a callback
            is_valid.on_change(lambda valid: print(f"Form is valid: {valid}"))

            # Initially valid
            print(is_valid.get())  # Prints: True

            # Make an invalid change
            proxy.observable(int, "age").set(-5)  # Prints: "Form is valid: False"
            ```
        """
        return self._is_valid_obs

    @override
    def validation_errors(self) -> IObservableDict[str, list[str]]:
        """
        Get an observable dictionary of validation errors.

        This method returns an observable dictionary that maps field names to lists
        of error messages. The dictionary is updated automatically when field values
        change and validation is performed.

        Returns:
            An observable dictionary mapping field names to lists of error messages.
            Fields with no errors are not included in the dictionary.

        Examples:
            ```python
            # Create a proxy with validation
            user = User(name="", age=-5)
            proxy = ObservableProxy(user)

            # Add validators
            proxy.add_validator("name", lambda name: "Name cannot be empty" if not name else None)
            proxy.add_validator("age", lambda age: "Age must be positive" if age < 0 else None)

            # Get validation errors
            errors = proxy.validation_errors()
            print(dict(errors))  # Prints: {'name': ['Name cannot be empty'], 'age': ['Age must be positive']}

            # Fix one error
            proxy.observable(str, "name").set("Alice")
            print(dict(errors))  # Prints: {'age': ['Age must be positive']}
            ```
        """
        return self._validation_errors_dict

    @override
    def validation_for(self, attr: str) -> IObservable[list[str]]:
        """
        Get an observable list of validation errors for a specific field.

        This method returns an observable that emits a list of error messages for
        the specified field. The observable updates automatically when the field
        value changes and validation is performed.

        Args:
            attr: The field name to get validation errors for.

        Returns:
            An observable that emits a list of error messages for the field.
            An empty list means the field is valid.

        Examples:
            ```python
            # Create a proxy with validation
            user = User(name="", age=30)
            proxy = ObservableProxy(user)

            # Add validators for the name field
            proxy.add_validator("name", lambda name: "Name cannot be empty" if not name else None)
            proxy.add_validator("name", lambda name: "Name too long" if len(name) > 50 else None)

            # Get validation errors for the name field
            name_errors = proxy.validation_for("name")
            print(name_errors.get())  # Prints: ['Name cannot be empty']

            # Fix the error
            proxy.observable(str, "name").set("Alice")
            print(name_errors.get())  # Prints: []
            ```
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

    @override
    def reset_validation(self, attr: str | None = None, *, revalidate: bool = False) -> None:
        """
        Reset validation errors for a specific field or all fields.

        This method clears validation errors for the specified field or all fields.
        It can optionally re-run validators after clearing errors.

        Args:
            attr: The field name to reset validation for. If None, reset all fields.
            revalidate: Whether to re-run validators after clearing errors.
                       If True, validators will be run on the current field values.
                       If False, fields will be marked as valid until the next change.

        Examples:
            ```python
            # Create a proxy with validation
            user = User(name="", age=-5)
            proxy = ObservableProxy(user)

            # Add validators
            proxy.add_validator("name", lambda name: "Name cannot be empty" if not name else None)
            proxy.add_validator("age", lambda age: "Age must be positive" if age < 0 else None)

            # Check validation initially
            print(proxy.is_valid().get())  # Prints: False

            # Reset validation for all fields without revalidating
            proxy.reset_validation()
            print(proxy.is_valid().get())  # Prints: True

            # Reset validation for all fields with revalidation
            proxy.reset_validation(revalidate=True)
            print(proxy.is_valid().get())  # Prints: False

            # Reset validation for just the name field
            proxy.reset_validation("name")
            print(proxy.validation_for("name").get())  # Prints: []
            print(proxy.validation_for("age").get())   # Prints: ['Age must be positive']
            ```
        """
        if attr is None:
            # Reset all validation errors
            self._validation_errors_dict.clear()
            # Update the is_valid observable
            self._is_valid_obs.set(True)

            # Re-run all validators if requested
            if revalidate:
                for field_name in self._validators.keys():
                    self._validate_field_if_exists(field_name)
        else:
            # Reset validation errors for a specific field
            if attr in self._validation_errors_dict:
                del self._validation_errors_dict[attr]
                # Update the is_valid observable
                self._is_valid_obs.set(len(self._validation_errors_dict) == 0)

            # Re-run validator for this field if requested
            if revalidate:
                self._validate_field_if_exists(attr)

    @override
    def set_undo_config(
        self,
        attr: str,
        *,
        enabled: bool | None = None,
        undo_max: int | None = None,
        undo_debounce_ms: int | None = None,
    ) -> None:
        """
        Set the undo configuration for a specific field.

        This method allows configuring undo/redo behavior for individual fields.
        Each field can have its own undo history size and debounce timing.

        Args:
            attr: The field name to configure.
            enabled: Whether undo/redo functionality is enabled for this field.
                    If None, uses the default from the proxy.
            undo_max: Maximum number of undo steps to store. None means use the default.
                     A value of 0 means no limit.
            undo_debounce_ms: Time window in milliseconds to group changes into a single undo step.
                             None means use the default. A value of 0 means no debouncing.

        Examples:
            ```python
            # Create a proxy with undo enabled
            document = Document(title="Draft", content="Hello world")
            proxy = ObservableProxy(document, undo=True)

            # Configure undo for the content field
            proxy.set_undo_config(
                "content",
                undo_max=100,       # Store up to 100 undo steps
                undo_debounce_ms=500  # Group changes within 500ms
            )

            # Disable undo for the title field
            proxy.set_undo_config("title", enabled=False)
            ```
        """
        # Get the current config or create a new one
        config = self._field_undo_configs.get(attr, UndoConfig())

        # Update the config with the provided values
        if enabled is not None:
            config.enabled = enabled
        elif attr not in self._field_undo_configs:
            # If this is a new config and enabled wasn't specified, inherit from default
            config.enabled = self._default_undo_config.enabled

        if undo_max is not None:
            config.undo_max = undo_max
        if undo_debounce_ms is not None:
            config.undo_debounce_ms = undo_debounce_ms

        # Store the updated config
        self._field_undo_configs[attr] = config

        # Enforce the max size if it's been reduced
        if attr in self._undo_stacks and config.undo_max is not None:
            while len(self._undo_stacks[attr]) > config.undo_max:
                self._undo_stacks[attr].pop(0)

    def _get_undo_config(self, attr: str) -> UndoConfig:
        """
        Get the undo configuration for a field.

        Args:
            attr: The field name.

        Returns:
            The undo configuration for the field, or the default if not set.
        """
        config = self._field_undo_configs.get(attr, self._default_undo_config)

        # If undo_max is None, use the default from UndoConfig
        if config.undo_max is None:
            from observant.types.undo_config import UndoConfig as DefaultUndoConfig

            config.undo_max = DefaultUndoConfig.undo_max

        # Make sure the enabled flag is set correctly
        # If this is a field-specific config, check if it has an explicit enabled flag
        if attr in self._field_undo_configs:
            # If the field has a specific config but no explicit enabled flag,
            # inherit from the default config
            if not hasattr(config, "enabled"):
                config.enabled = self._default_undo_config.enabled

        return config

    # _track_scalar_change has been removed - UndoableObservable now handles this

    def _track_list_change(self, attr: str, change: Any) -> None:
        """
        Track a change to a list field for undo/redo.

        This method is called when a list field is modified. It creates undo and redo
        functions based on the type of change (add, remove, clear) and adds them to
        the undo stack.

        Args:
            attr: The field name.
            change: The change object containing details about the modification.

        Note:
            This method is primarily used internally by the ObservableProxy class.
            Users typically don't need to call this method directly.
        """
        # Get the observable for this field
        obs = None
        for key, o in self._lists.items():
            if key.attr == attr:
                obs = o
                break

        if obs is None:
            return  # Field not found

        # Create a flag to prevent recursive tracking
        tracking_enabled = [True]

        # We don't need a tracking function here since it's already registered
        # when the observable_list is created

        # We don't need to add a new tracking callback here
        # The callback is already registered when the observable_list is created

        # Helper function to temporarily disable tracking
        def with_tracking_disabled(action: Callable[[], None]) -> None:
            tracking_enabled[0] = False
            action()
            tracking_enabled[0] = True

        # Create undo/redo functions based on the change type
        if hasattr(change, "type") and change.type == ObservableCollectionChangeType.CLEAR:
            # This is a clear operation
            old_items = change.items

            def undo_func() -> None:
                def action() -> None:
                    obs.extend(old_items)

                with_tracking_disabled(action)

            def redo_func() -> None:
                def action() -> None:
                    obs.clear()

                with_tracking_disabled(action)

        elif hasattr(change, "index") and hasattr(change, "item"):
            # This could be an append/insert or a remove operation
            index = change.index
            item = change.item

            if change.type == ObservableCollectionChangeType.ADD:
                # This is an append or insert
                def undo_func() -> None:
                    def action() -> None:
                        if index is not None and index < len(obs):  # Check if index is valid
                            obs.pop(index)

                    with_tracking_disabled(action)

                def redo_func() -> None:
                    def action() -> None:
                        if index is not None:
                            obs.insert(index, item)
                        else:
                            obs.append(item)

                    with_tracking_disabled(action)
            else:
                # This is a remove operation
                def undo_func() -> None:
                    def action() -> None:
                        if index is not None:
                            obs.insert(index, item)
                        else:
                            obs.append(item)

                    with_tracking_disabled(action)

                def redo_func() -> None:
                    def action() -> None:
                        if index is not None and index < len(obs):  # Check if index is valid
                            obs.pop(index)

                    with_tracking_disabled(action)

        else:
            # Unknown change type
            return

        # Add to the undo stack
        self._add_to_undo_stack(attr, undo_func, redo_func, from_undo=True)

    def _track_dict_change(self, attr: str, change: Any) -> None:
        """
        Track a change to a dict field for undo/redo.

        This method is called when a dictionary field is modified. It creates undo and redo
        functions based on the type of change (add, update, remove, clear) and adds them to
        the undo stack.

        Args:
            attr: The field name.
            change: The change object containing details about the modification.

        Note:
            This method is primarily used internally by the ObservableProxy class.
            Users typically don't need to call this method directly.
        """
        # Get the observable for this field
        obs = None
        for key, o in self._dicts.items():
            if key.attr == attr:
                obs = o
                break

        if obs is None:
            return  # Field not found

        # Create a flag to prevent recursive tracking
        tracking_enabled = [True]

        # We don't need a tracking function here since it's already registered
        # when the observable_dict is created

        # We don't need to add a new tracking callback here
        # The callback is already registered when the observable_dict is created

        # Helper function to temporarily disable tracking
        def with_tracking_disabled(action: Callable[[], None]) -> None:
            tracking_enabled[0] = False
            action()
            tracking_enabled[0] = True

        # Create undo/redo functions based on the change type
        if hasattr(change, "key") and hasattr(change, "value") and hasattr(change, "old_value"):
            # This is a key update
            dict_key = change.key
            value = change.value
            old_value = change.old_value

            def undo_func() -> None:
                def action() -> None:
                    obs[dict_key] = old_value

                with_tracking_disabled(action)

            def redo_func() -> None:
                def action() -> None:
                    obs[dict_key] = value

                with_tracking_disabled(action)

        elif hasattr(change, "key") and hasattr(change, "value") and not hasattr(change, "old_value"):
            # This is a new key
            dict_key = change.key
            value = change.value

            def undo_func() -> None:
                def action() -> None:
                    if dict_key in obs:  # Check if key exists
                        del obs[dict_key]

                with_tracking_disabled(action)

            def redo_func() -> None:
                def action() -> None:
                    obs[dict_key] = value

                with_tracking_disabled(action)

        elif hasattr(change, "key") and hasattr(change, "value") and change.type == ObservableCollectionChangeType.REMOVE:
            # This is a key deletion
            dict_key = change.key
            old_value = change.value

            def undo_func() -> None:
                obs[dict_key] = old_value

            def redo_func() -> None:
                if dict_key in obs:
                    del obs[dict_key]

        elif hasattr(change, "old_items"):
            # This is a clear
            old_items = change.old_items

            def undo_func() -> None:
                def action() -> None:
                    obs.update(old_items)

                with_tracking_disabled(action)

            def redo_func() -> None:
                def action() -> None:
                    obs.clear()

                with_tracking_disabled(action)

        else:
            # Unknown change type
            return

        # Add to the undo stack
        self._add_to_undo_stack(attr, undo_func, redo_func, from_undo=True)

    def _add_to_undo_stack(self, attr: str, undo_func: Callable[[], None], redo_func: Callable[[], None], from_undo: bool = False) -> None:
        """
        Add an undo/redo pair to the undo stack for a field.

        This method manages the undo and redo stacks for a field. It handles debouncing
        (grouping changes within a time window), enforces maximum stack size, and
        manages the pending undo groups.

        Args:
            attr: The field name.
            undo_func: The function to call to undo the change.
            redo_func: The function to call to redo the change.
            from_undo: Whether this is being called from the undo method.

        Note:
            This method is primarily used internally by the ObservableProxy class.
            Users typically don't need to call this method directly.
        """
        # Initialize stacks if they don't exist
        if attr not in self._undo_stacks:
            self._undo_stacks[attr] = []
        if attr not in self._redo_stacks:
            self._redo_stacks[attr] = []

        # Get the undo config for this field
        config = self._get_undo_config(attr)

        # Check if we should debounce this change
        now = time.monotonic() * 1000  # Convert to milliseconds
        last_change_time = self._last_change_times.get(attr, 0)
        debounce_window = config.undo_debounce_ms
        time_since_last_change = now - last_change_time

        if debounce_window is not None and attr in self._pending_undo_groups and self._pending_undo_groups[attr] is not None and time_since_last_change < debounce_window:
            # We're within the debounce window, update the pending group
            self._pending_undo_groups[attr] = redo_func
        else:
            # We're outside the debounce window or there's no pending group

            # Clear the redo stack when a new change is made, but not if we're undoing
            if not from_undo:
                self._redo_stacks[attr].clear()

            # Add the undo function to the stack
            self._undo_stacks[attr].append(undo_func)

            # Enforce the max size
            if config.undo_max is not None:
                while len(self._undo_stacks[attr]) > config.undo_max:
                    self._undo_stacks[attr].pop(0)

            # Set the pending group
            self._pending_undo_groups[attr] = redo_func

        # Update the last change time
        self._last_change_times[attr] = now

    @override
    def undo(self, attr: str) -> None:
        """
        Undo the most recent change to a field.

        This method reverts the most recent change to the specified field by
        popping the top function from the undo stack and executing it. If the
        field has no changes to undo, this method does nothing.

        Args:
            attr: The field name to undo changes for.

        Examples:
            ```python
            # Create a proxy with undo enabled
            document = Document(title="Draft", content="Hello")
            proxy = ObservableProxy(document, undo=True)

            # Make some changes
            proxy.observable(str, "content").set("Hello world")
            proxy.observable(str, "content").set("Hello world!")

            # Undo the last change
            proxy.undo("content")  # Content is now "Hello world"

            # Undo again
            proxy.undo("content")  # Content is now "Hello"
            ```
        """
        if attr not in self._undo_stacks or not self._undo_stacks[attr]:
            return  # Nothing to undo

        # Pop the most recent undo function
        undo_func = self._undo_stacks[attr].pop()

        # Get the pending redo function
        redo_func = self._pending_undo_groups.get(attr)

        # Add to the redo stack if it exists
        if redo_func is not None:
            self._redo_stacks[attr].append(redo_func)
            self._pending_undo_groups[attr] = None

        # Find the observable for this field to set the undoing flag
        obs = None
        for key, o in self._scalars.items():
            if key.attr == attr:
                obs = o
                break

        # Set the undoing flag if we found the observable and it's a UndoableObservable
        from observant.undoable_observable import UndoableObservable

        if obs is not None and isinstance(obs, UndoableObservable):
            obs.set_undoing(True)

        try:
            undo_func()
        finally:
            # Reset the undoing flag
            if obs is not None and isinstance(obs, UndoableObservable):
                obs.set_undoing(False)

        # If sync is enabled for this field, update the model
        for key in self._scalars:
            if key.attr == attr and key.sync:
                value = self._scalars[key].get()
                setattr(self._obj, attr, value)
                break

    @override
    def redo(self, attr: str) -> None:
        """
        Redo the most recently undone change to a field.

        This method reapplies the most recently undone change to the specified field
        by popping the top function from the redo stack and executing it. If the
        field has no changes to redo, this method does nothing.

        Args:
            attr: The field name to redo changes for.

        Examples:
            ```python
            # Create a proxy with undo enabled
            document = Document(title="Draft", content="Hello")
            proxy = ObservableProxy(document, undo=True)

            # Make a change
            proxy.observable(str, "content").set("Hello world")

            # Undo the change
            proxy.undo("content")  # Content is now "Hello"

            # Redo the change
            proxy.redo("content")  # Content is now "Hello world" again
            ```
        """
        if attr not in self._redo_stacks or not self._redo_stacks[attr]:
            return  # Nothing to redo

        # Pop the most recent redo function
        redo_func = self._redo_stacks[attr].pop()

        # Get the undo function that will undo this redo operation
        undo_func = None
        if attr in self._pending_undo_groups:
            undo_func = self._pending_undo_groups[attr]

        # Find the observable for this field to manually track changes
        obs_list = None
        obs_dict = None

        # Check if this is a list field
        for key, o in self._lists.items():
            if key.attr == attr:
                obs_list = o
                break

        # Check if this is a dict field
        if obs_list is None:
            for key, o in self._dicts.items():
                if key.attr == attr:
                    obs_dict = o
                    break

        # Find the scalar observable for this field to set the undoing flag
        obs_scalar = None
        for key, o in self._scalars.items():
            if key.attr == attr:
                obs_scalar = o
                break

        # Set the undoing flag if we found the observable and it's a UndoableObservable
        from observant.undoable_observable import UndoableObservable

        if obs_scalar is not None and isinstance(obs_scalar, UndoableObservable):
            obs_scalar.set_undoing(True)

        try:
            redo_func()
        finally:
            # Reset the undoing flag
            if obs_scalar is not None and isinstance(obs_scalar, UndoableObservable):
                obs_scalar.set_undoing(False)

        # Add the undo function back to the undo stack
        if undo_func is not None:
            self._undo_stacks.setdefault(attr, []).append(undo_func)
            self._pending_undo_groups[attr] = None
        else:
            # If we don't have an undo function from the pending group,
            # we need to create one based on the current state

            # For scalar fields
            for key, o in self._scalars.items():
                if key.attr == attr:
                    current_value = o.get()

                    def new_undo_func() -> None:
                        o.set(current_value, notify=False)

                    self._undo_stacks.setdefault(attr, []).append(new_undo_func)
                    break

            # For list fields
            if obs_list is not None:
                current_list = obs_list.copy()

                def new_list_undo_func() -> None:
                    obs_list.clear()
                    obs_list.extend(current_list)

                self._undo_stacks.setdefault(attr, []).append(new_list_undo_func)

            # For dict fields
            if obs_dict is not None:
                current_dict = obs_dict.copy()

                def new_dict_undo_func() -> None:
                    obs_dict.clear()
                    obs_dict.update(current_dict)

                self._undo_stacks.setdefault(attr, []).append(new_dict_undo_func)

        # If sync is enabled for this field, update the model
        for key in self._scalars:
            if key.attr == attr and key.sync:
                value = self._scalars[key].get()
                setattr(self._obj, attr, value)
                break

    @override
    def can_undo(self, attr: str) -> bool:
        """
        Check if there are changes that can be undone for a field.

        This method returns True if there are changes in the undo stack for the
        specified field, and False otherwise.

        Args:
            attr: The field name to check.

        Returns:
            True if there are changes that can be undone, False otherwise.

        Examples:
            ```python
            # Create a proxy with undo enabled
            document = Document(title="Draft", content="Hello")
            proxy = ObservableProxy(document, undo=True)

            # Check if we can undo initially
            print(proxy.can_undo("content"))  # Prints: False

            # Make a change
            proxy.observable(str, "content").set("Hello world")

            # Check if we can undo after change
            print(proxy.can_undo("content"))  # Prints: True

            # Undo the change
            proxy.undo("content")

            # Check if we can undo after undoing
            print(proxy.can_undo("content"))  # Prints: False
            ```
        """
        return attr in self._undo_stacks and bool(self._undo_stacks[attr])

    @override
    def can_redo(self, attr: str) -> bool:
        """
        Check if there are changes that can be redone for a field.

        This method returns True if there are changes in the redo stack for the
        specified field, and False otherwise.

        Args:
            attr: The field name to check.

        Returns:
            True if there are changes that can be redone, False otherwise.

        Examples:
            ```python
            # Create a proxy with undo enabled
            document = Document(title="Draft", content="Hello")
            proxy = ObservableProxy(document, undo=True)

            # Make a change
            proxy.observable(str, "content").set("Hello world")

            # Check if we can redo initially
            print(proxy.can_redo("content"))  # Prints: False

            # Undo the change
            proxy.undo("content")

            # Check if we can redo after undoing
            print(proxy.can_redo("content"))  # Prints: True

            # Redo the change
            proxy.redo("content")

            # Check if we can redo after redoing
            print(proxy.can_redo("content"))  # Prints: False
            ```
        """
        return attr in self._redo_stacks and bool(self._redo_stacks[attr])

    @override
    def track_scalar_change(self, attr: str, old_value: Any, new_value: Any) -> None:
        """
        Track a scalar change for undo/redo functionality.

        This method is called by UndoableObservable when a scalar field value changes.
        It creates undo and redo functions and adds them to the undo stack.

        Args:
            attr: The field name that changed.
            old_value: The old value before the change.
            new_value: The new value after the change.

        Note:
            This method is primarily used internally by the ObservableProxy class.
            Users typically don't need to call this method directly.
        """
        if old_value == new_value:
            return

        # Check if undo is enabled for this field
        config = self._get_undo_config(attr)
        if not config.enabled:
            return

        # Get the observable for this field
        obs = None
        for key, o in self._scalars.items():
            if key.attr == attr:
                obs = o
                break

        if obs is None:
            return  # Field not found

        # Create undo/redo functions
        def undo_func() -> None:
            obs.set(old_value)

            # If we're undoing to the original value, clear the dirty state
            if old_value == self._initial_values.get(attr):
                self._dirty_fields.discard(attr)

        def redo_func() -> None:
            obs.set(new_value)

            # If we're redoing to a non-original value, mark as dirty
            if new_value != self._initial_values.get(attr):
                self._dirty_fields.add(attr)

        # Add to the undo stack
        self._add_to_undo_stack(attr, undo_func, redo_func)

    def _parse_path_segments(self, path: str) -> list[tuple[str, bool]]:
        """
        Parse a path into segments with optional flags.

        "habitat?.location?.city" -> [("habitat", True), ("location", True), ("city", False)]
        "habitat.location.city" -> [("habitat", False), ("location", False), ("city", False)]

        Args:
            path: The dot-separated path, optionally with ?. for optional segments.

        Returns:
            List of (segment_name, is_optional) tuples.
        """
        segments: list[tuple[str, bool]] = []
        raw_parts = path.replace("?.", "\x00").split(".")
        for part in raw_parts:
            if "\x00" in part:
                sub_parts = part.split("\x00")
                for j, sub in enumerate(sub_parts):
                    if sub:
                        is_optional = j < len(sub_parts) - 1
                        segments.append((sub, is_optional))
            else:
                segments.append((part, False))
        return segments

    def _get_value_at_path(self, segments: list[tuple[str, bool]]) -> Any:
        """
        Get the current value at a path, returning None if any optional segment is None.

        Args:
            segments: List of (segment_name, is_optional) tuples.

        Returns:
            The value at the path, or None if path is broken.
        """
        current_obj: Any = self._obj
        for part, is_optional in segments:
            if current_obj is None:
                return None
            current_obj = getattr(current_obj, part, None)
            if current_obj is None and is_optional:
                return None
        return current_obj

    @override
    def observable_for_path(
        self,
        path: str,
        *,
        sync: bool | None = None,
    ) -> IObservable[Any]:
        """
        Get an observable for a nested path like "habitat.location.city".

        Supports optional chaining with ?. syntax (like JavaScript):
        - "habitat?.location" - if habitat is None, observable holds None
        - "habitat.location?.city" - if location is None, observable holds None

        When parent objects change from None to a value (or vice versa),
        the observable automatically updates.

        Args:
            path: The dot-separated path to the field. Use ?. for optional segments.
            sync: Whether to sync changes back to the model immediately.
                 If None, uses the default sync setting from the proxy.

        Returns:
            An observable for the value at the path.

        Examples:
            ```python
            # Simple nested path
            city_obs = proxy.observable_for_path("address.city")

            # Optional chaining - won't error if address is None
            city_obs = proxy.observable_for_path("address?.city")

            # Deep nesting with optional chaining
            zip_obs = proxy.observable_for_path("user?.address?.zip_code")
            ```
        """
        sync = self._sync_default if sync is None else sync

        # Simple case: no dots means it's a direct attribute
        if "." not in path and "?" not in path:
            return self.observable(object, path, sync=sync)

        segments = self._parse_path_segments(path)
        has_optional = any(is_opt for _, is_opt in segments)

        if not has_optional:
            # No optional segments - use simple nested proxy approach
            return self._observable_for_required_path(segments, sync)

        # Optional segments - create reactive observable
        return self._observable_for_optional_path(segments, sync)

    def _observable_for_required_path(
        self, segments: list[tuple[str, bool]], sync: bool
    ) -> IObservable[Any]:
        """
        Handle paths without optional chaining - all segments must exist.

        Args:
            segments: List of (segment_name, is_optional) tuples.
            sync: Whether to sync changes back to the model.

        Returns:
            An observable for the final value in the path.
        """
        current_obj: Any = self._obj
        current_proxy: ObservableProxy[Any] = self

        for i, (part, _) in enumerate(segments[:-1]):
            cache_key = ".".join(seg[0] for seg in segments[: i + 1])
            current_obj = getattr(current_obj, part)

            if cache_key not in self._nested_proxies:
                self._nested_proxies[cache_key] = ObservableProxy(
                    current_obj, sync=sync
                )
            current_proxy = self._nested_proxies[cache_key]

        final_attr = segments[-1][0]
        return current_proxy.observable(object, final_attr, sync=sync)

    def _observable_for_optional_path(
        self, segments: list[tuple[str, bool]], sync: bool
    ) -> IObservable[Any]:
        """
        Handle paths with optional chaining.
        Creates a derived observable that reacts to changes in parent objects.

        Args:
            segments: List of (segment_name, is_optional) tuples.
            sync: Whether to sync changes back to the model.

        Returns:
            A _PathObservable that wraps the value and reacts to parent changes.
        """
        # Create the result observable with current value
        initial_value = self._get_value_at_path(segments)
        result_obs: Observable[Any] = Observable(initial_value)

        def setup_subscriptions() -> None:
            # Walk the path and subscribe to each level
            current_obj: Any = self._obj
            current_proxy: ObservableProxy[Any] = self

            for i, (part, _) in enumerate(segments[:-1]):
                cache_key = ".".join(seg[0] for seg in segments[: i + 1])

                # Get observable for this segment
                part_obs = current_proxy.observable(object, part, sync=sync)

                # Subscribe to changes at this level
                def make_handler() -> Callable[[Any], None]:
                    def handler(_: Any) -> None:
                        new_value = self._get_value_at_path(segments)
                        if result_obs.get() != new_value:
                            result_obs.set(new_value)

                    return handler

                part_obs.on_change(make_handler())

                # Navigate to next level
                current_obj = getattr(current_obj, part, None)
                if current_obj is None:
                    # Path is broken, stop here but we've subscribed to parents
                    return

                # Create/get proxy for next level
                if cache_key not in self._nested_proxies:
                    self._nested_proxies[cache_key] = ObservableProxy(
                        current_obj, sync=sync
                    )
                current_proxy = self._nested_proxies[cache_key]

            # Subscribe to the final attribute
            final_attr = segments[-1][0]
            final_obs = current_proxy.observable(object, final_attr, sync=sync)

            def final_handler(new_val: Any) -> None:
                if result_obs.get() != new_val:
                    result_obs.set(new_val)

            final_obs.on_change(final_handler)

        # Initial subscription setup
        setup_subscriptions()

        return _PathObservable(result_obs, self, segments)
