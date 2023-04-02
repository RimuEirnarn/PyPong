"""GUI Config"""
from typing import NamedTuple


class AppConfig(NamedTuple):
    """Application Config"""

    resolution: tuple[int, int]
    full: bool
    MAXFPS: int
