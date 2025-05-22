from dataclasses import dataclass
from typing import Generic, TypeVar

from .collection_change_type import ObservableCollectionChangeType

T = TypeVar("T")


@dataclass(frozen=True)
class ObservableListChange(Generic[T]):
    """Information about a change to an ObservableList."""

    type: ObservableCollectionChangeType
    index: int | None = None  # Index where the change occurred, if applicable
    item: T | None = None  # Item that was added or removed, if applicable
    items: list[T] | None = None  # Multiple items that were added or removed, if applicable
