from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ProxyFieldKey:
    attr: str
    sync: bool
