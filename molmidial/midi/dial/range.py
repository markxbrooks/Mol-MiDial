"""
Dial Range
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DialRange:
    min: int | float
    init: int | float
    max: int | float

    def as_tuple(self) -> tuple[int, int, int]:
        return self.min, self.init, self.max