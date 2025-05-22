from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from observant.interfaces.dict import IObservableDict
from observant.interfaces.list import IObservableList
from observant.interfaces.observable import IObservable

T = TypeVar("T")


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
        attr: str,
        *,
        sync: bool | None = None,
    ) -> IObservableDict[Any, Any]:
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
    def update(self, **kwargs: T) -> None:
        """
        Set one or more scalar observable values.
        """
        ...

    @abstractmethod
    def load_dict(self, values: dict[str, T]) -> None:
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
