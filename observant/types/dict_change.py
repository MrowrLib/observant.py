from dataclasses import dataclass
from typing import Generic, TypeVar

from .collection_change_type import ObservableCollectionChangeType

TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


@dataclass(frozen=True)
class ObservableDictChange(Generic[TKey, TValue]):
    """Information about a change to an ObservableDict."""

    type: ObservableCollectionChangeType
    key: TKey | None = None  # Key where the change occurred, if applicable
    value: TValue | None = (
        None  # Value that was added, removed, or updated, if applicable
    )
    items: dict[TKey, TValue] | None = (
        None  # Multiple items that were added, removed, or updated, if applicable
    )
