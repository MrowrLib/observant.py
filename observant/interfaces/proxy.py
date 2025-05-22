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
