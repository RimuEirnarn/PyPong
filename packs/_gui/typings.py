"""GUI Typings"""
from typing import NamedTuple

import pygame


Resolution = tuple[int, int]
Coordinate = tuple[int, int]
Size = tuple[int, int]
Color = tuple[int, int, int] | pygame.Color


class CommonConstants(NamedTuple):
    """Common constants"""
    WIDTH: int
    HEIGHT: int
    FONT: pygame.font.Font
