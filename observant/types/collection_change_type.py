from enum import Enum, auto


class ObservableCollectionChangeType(Enum):
    """Type of change that occurred in a collection."""

    ADD = auto()
    REMOVE = auto()
    CLEAR = auto()
    UPDATE = auto()  # For dictionaries, when a value is updated
