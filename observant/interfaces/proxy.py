from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

from observant.interfaces.dict import IObservableDict
from observant.interfaces.list import IObservableList
from observant.interfaces.observable import IObservable

T = TypeVar("T")
TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


class IObservableProxy(Generic[T], ABC):
    """
    Proxy for a data object that exposes its fields as Observable, ObservableList, or ObservableDict.
    Provides optional sync behavior to automatically write back to the source model.
    """

    @abstractmethod
    def observable(
        self,
        typ: type[T],
        attr: str,
        *,
        sync: bool | None = None,
    ) -> IObservable[T]:
        """
        Get or create an Observable[T] for a scalar field.
        """
        ...

    @abstractmethod
    def observable_list(
        self,
        typ: type[T],
        attr: str,
        *,
        sync: bool | None = None,
    ) -> IObservableList[T]:
        """
        Get or create an ObservableList[T] for a list field.
        """
        ...

    @abstractmethod
    def observable_dict(
        self,
        typ: tuple[type[TKey], type[TValue]],
        attr: str,
        *,
        sync: bool | None = None,
    ) -> IObservableDict[TKey, TValue]:
        """
        Get or create an ObservableDict for a dict field.
        """
        ...

    @abstractmethod
    def get(self) -> T:
        """
        Get the original object being proxied.
        """
        ...

    @abstractmethod
    def update(self, **kwargs: Any) -> None:
        """
        Set one or more scalar observable values.
        """
        ...

    @abstractmethod
    def load_dict(self, values: dict[str, Any]) -> None:
        """
        Set multiple scalar observable values from a dict.
        """
        ...

    @abstractmethod
    def save_to(self, obj: T) -> None:
        """
        Write all observable values back into the given object.
        """
        ...

    @abstractmethod
    def is_dirty(self) -> bool:
        """
        Check if any fields have been modified since initialization or last reset.

        Returns:
            True if any fields have been modified, False otherwise.
        """
        ...

    @abstractmethod
    def dirty_fields(self) -> set[str]:
        """
        Get the set of field names that have been modified.

        Returns:
            A set of field names that have been modified.
        """
        ...

    @abstractmethod
    def reset_dirty(self) -> None:
        """
        Reset the dirty state of all fields.
        """
        ...

    @abstractmethod
    def register_computed(
        self,
        name: str,
        compute: Callable[[], T],
        dependencies: list[str],
    ) -> None:
        """
        Register a computed property that depends on other observables.

        Args:
            name: The name of the computed property.
            compute: A function that returns the computed value.
            dependencies: List of field names that this computed property depends on.
        """
        ...

    @abstractmethod
    def computed(
        self,
        typ: type[T],
        name: str,
    ) -> IObservable[T]:
        """
        Get a computed property by name.

        Args:
            typ: The type of the computed property.
            name: The name of the computed property.

        Returns:
            An observable containing the computed value.
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def is_valid(self) -> IObservable[bool]:
        """
        Get an observable that indicates whether all fields are valid.

        Returns:
            An observable that emits True if all fields are valid, False otherwise.
        """
        ...

    @abstractmethod
    def validation_errors(self) -> IObservableDict[str, list[str]]:
        """
        Get an observable dictionary of validation errors.

        Returns:
            An observable dictionary mapping field names to lists of error messages.
        """
        ...

    @abstractmethod
    def validation_for(self, attr: str) -> IObservable[list[str]]:
        """
        Get an observable list of validation errors for a specific field.

        Args:
            attr: The field name to get validation errors for.

        Returns:
            An observable that emits a list of error messages for the field.
            An empty list means the field is valid.
        """
        ...

    @abstractmethod
    def reset_validation(self, attr: str | None = None, *, revalidate: bool = False) -> None:
        """
        Reset validation errors for a specific field or all fields.

        Args:
            attr: The field name to reset validation for. If None, reset all fields.
            revalidate: Whether to re-run validators after clearing errors.
        """
        ...

    @abstractmethod
    def set_undo_config(
        self,
        attr: str,
        *,
        undo_max: int | None = None,
        undo_debounce_ms: int | None = None,
    ) -> None:
        """
        Set the undo configuration for a specific field.

        Args:
            attr: The field name to configure.
            undo_max: Maximum number of undo steps to store. None means unlimited.
            undo_debounce_ms: Time window in milliseconds to group changes. None means no debouncing.
        """
        ...

    @abstractmethod
    def undo(self, attr: str) -> None:
        """
        Undo the most recent change to a field.

        Args:
            attr: The field name to undo changes for.
        """
        ...

    @abstractmethod
    def redo(self, attr: str) -> None:
        """
        Redo the most recently undone change to a field.

        Args:
            attr: The field name to redo changes for.
        """
        ...

    @abstractmethod
    def can_undo(self, attr: str) -> bool:
        """
        Check if there are changes that can be undone for a field.

        Args:
            attr: The field name to check.

        Returns:
            True if there are changes that can be undone, False otherwise.
        """
        ...

    @abstractmethod
    def can_redo(self, attr: str) -> bool:
        """
        Check if there are changes that can be redone for a field.

        Args:
            attr: The field name to check.

        Returns:
            True if there are changes that can be redone, False otherwise.
        """
        ...

    @abstractmethod
    def track_scalar_change(self, attr: str, old_value: Any, new_value: Any) -> None:
        """
        Track a scalar change for undo/redo functionality.

        Args:
            attr: The field name that changed.
            old_value: The old value before the change.
            new_value: The new value after the change.
        """
        ...

    @abstractmethod
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
        ...
