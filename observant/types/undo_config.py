from dataclasses import dataclass
from typing import Optional


@dataclass
class UndoConfig:
    """
    Configuration for undo/redo behavior of an observable field.

    Attributes:
        enabled: Whether undo/redo functionality is enabled for this field.
        undo_max: Maximum number of undo steps to store. None means unlimited.
        undo_debounce_ms: Time window in milliseconds to group changes. None means no debouncing.
    """

    enabled: bool = False
    undo_max: Optional[int] = 50
    undo_debounce_ms: Optional[int] = None
