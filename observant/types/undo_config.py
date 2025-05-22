from dataclasses import dataclass
from typing import Optional


@dataclass
class UndoConfig:
    """
    Configuration for undo/redo behavior of an observable field.

    Attributes:
        undo_max: Maximum number of undo steps to store. None means unlimited.
        undo_debounce_ms: Time window in milliseconds to group changes. None means no debouncing.
    """

    undo_max: Optional[int] = None
    undo_debounce_ms: Optional[int] = None
