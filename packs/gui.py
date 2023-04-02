"""Basic GUI Module"""
# pylint: disable=too-many-instance-attributes,too-many-arguments,too-few-public-methods,attribute-defined-outside-init,no-name-in-module
from typing import Literal

import pygame
from pygame.event import Event

from ._gui import BaseApp
from ._gui.typings import Color, CommonConstants, Coordinate, Size
from .game_locals import DOWN, K_DOWN, K_UP, NONE, UP, K_s, K_w
from .logging import setup_logger
from .logging.config import FileConfig, SetupConfig

DEFAULTFONT = pygame.font.get_default_font()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GameLog, FileHandler, ConsoleHandler = setup_logger("GameLog", SetupConfig(
    FileConfig("gamelog.txt", 'w')
))


class BaseSpd:
    """Base Speedable ANY shape."""

    def __init__(self,
                 surface: pygame.Surface,
                 pos: Coordinate,
                 size: Size,
                 speed: int,
                 color: Color,
                 config: CommonConstants) -> None:
        self._surface = surface
        self._config = config
        self._posx = pos[0]
        self._posy = pos[1]
        self._width = size[0]
        self._height = size[1]
        self._speed = speed
        self._color = color


class BaseSpdRect(BaseSpd):
    """Base Speedable Rectangle"""

    def __init__(self,
                 surface: pygame.Surface,
                 pos: Coordinate,
                 size: Size,
                 speed: int,
                 color: Color,
                 config: CommonConstants) -> None:
        super().__init__(surface, pos, size, speed, color, config)
        self._rawbody = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self._body = pygame.draw.rect(surface, color, self._rawbody)

    @property
    def rect(self):
        """Return self rectangle"""
        return self._rawbody

    def display(self):
        """Display current rectangle"""
        self._body = pygame.draw.rect(
            self._surface, self._color, self._rawbody
        )
        return self._body


class BaseSpdCircle(BaseSpd):
    """Base Speedable Circle"""

    def __init__(self,
                 surface: pygame.Surface,
                 pos: Coordinate,
                 radius: int,
                 speed: int,
                 color: Color,
                 config: CommonConstants) -> None:
        super().__init__(surface, pos, (0, 0), speed, color, config)
        self._radius = radius
        self._circle = pygame.draw.circle(surface, color, pos, radius)

    @property
    def circle(self):
        """Return self circle"""
        return self._circle

    def display(self):
        """Display current circle"""
        self._circle = pygame.draw.circle(
            self._surface, self._color, (self._posx, self._posy), self._radius)
        return self._circle


class Player(BaseSpdRect):
    """Player rectangle"""

    def __init__(self,
                 surface: pygame.Surface,
                 pos: Coordinate,
                 size: Size,
                 speed: int,
                 color: Color,
                 config: CommonConstants) -> None:
        super().__init__(surface, pos, size, speed, color, config)
        self._movements = NONE
        self._score = 0

    def update(self):
        """Update player position by y-factor"""
        y_factor = self.movements
        self._posy = self._posy + self._speed*y_factor

        # GameLog.debug("Pos-y -> %s, RES %s, More? %s",
        #   self._posy, self._config.HEIGHT, self._posy + self._height >= self._config.HEIGHT)
        if self._posy <= 0:
            self._posy = 0

        elif self._posy + self._height >= self._config.HEIGHT:
            self._posy = self._config.HEIGHT - self._height

        self._rawbody = (
            self._posx, self._posy, self._width, self._height)

    def display_score(self, text: str, pos: Coordinate, color: Color):
        """Display score"""
        score = self._score
        data = self._config.FONT.render(f"{text}: {score}", True, color)
        rect = data.get_rect()
        rect.center = pos

        self._surface.blit(data, rect)

    @property
    def movements(self):
        """Player movements"""
        # GameLog.debug("Movements getattr %s", self._movements)
        return self._movements

    @movements.setter
    def movements(self, value: Literal[0, -1, 1]):
        """Player movements"""
        # GameLog.debug("Movements setattr -> %s", str(value))
        if not value in (NONE, UP, DOWN):
            raise ValueError("Expected NONE, DOWN, UP constant or 0, -1, 1")
        self._movements = value

    @property
    def score(self) -> int:
        """Player score"""
        return self._score

    @score.setter
    def score(self, value: int):
        """Player score"""
        if not isinstance(value, int):
            raise TypeError("Required integer type")
        self._score = value


class Ball(BaseSpdCircle):
    """Ball"""

    def __init__(self,
                 surface: pygame.Surface,
                 pos: Coordinate,
                 radius: int,
                 speed: int,
                 color: Color,
                 config: CommonConstants) -> None:
        super().__init__(surface, pos, radius, speed, color, config)
        self._x_factor = 1
        self._y_factor = -1
        self._firsttime = 1

    def update(self):
        """Update position"""
        self._posx += self._speed*self._x_factor
        self._posy += self._speed*self._y_factor

        # let's reflect the direction if hit some corner
        if self._posy <= 0 or self._posy >= self._config.HEIGHT:
            self._y_factor *= -1

        # if the ball touch left wall for the first time, set it (firstime) to 0
        # then return 0

        # If player 2 has scored, let's set firsttime to 0.
        if self._posx <= 0 and self._firsttime:
            self._firsttime = 0
            return 1  # Magic number 1
        if self._posx >= self._config.WIDTH and self._firsttime:
            self._firsttime = 0
            return -1  # Magic Number -1
        return 0

    def reset(self):
        """Reset ball position"""
        self._posx = self._config.WIDTH // 2
        self._posy = self._config.HEIGHT // 2
        self._x_factor *= -1
        self._firsttime = 1

    def hit(self):
        """Reflect on x-axis"""
        self._x_factor *= -1


class Application(BaseApp):
    """Application"""

    def init(self):
        GameLog.info("Game initialising")
        super().init()
        self._font = pygame.font.Font(DEFAULTFONT, 20)
        self._gamedata = CommonConstants(*self._config.resolution, self._font)
        self._ball = Ball(self._surface,
                          (self._config.resolution[0]//2,
                           self._config.resolution[1]//2),
                          7,
                          7,
                          WHITE,
                          self._gamedata)
        self._player1 = Player(self._surface, (20, 0),
                               (10, 100), 10, GREEN, self._gamedata)
        self._player2 = Player(
            self._surface, (self._config.resolution[0]-30, 0), (10, 100), 10, RED, self._gamedata)

        self._players = [self._player1, self._player2]
        GameLog.info("Game initialised. Setting running to true")
        self._running = True

    def on_exit(self):
        super().on_exit()
        GameLog.info("Received exit event... closing.")

    def on_keydown(self, event: Event):
        # GameLog.debug("Keydown event -> %s", event)
        """Keydown events"""
        if event.key == K_UP:
            self._player2.movements = UP
        if event.key == K_DOWN:
            self._player2.movements = DOWN
        if event.key == K_w:
            self._player1.movements = UP
        if event.key == K_s:
            self._player1.movements = DOWN

    def on_keyup(self, event: Event):
        # GameLog.debug("Keyup event -> %s", event)
        """Keyup events"""
        if event.key in (K_UP, K_DOWN):
            self._player2.movements = NONE
        if event.key in (K_w, K_s):
            self._player1.movements = NONE

    def on_main(self):
        """Anything besides on_event, update, etc."""
        # self._player1.movements = NONE
        # self._player1.movements = UP
        # self._player1.movements = DOWN

        # self._exit()
        # raise SystemExit
        self._surface.fill(BLACK)
        for player in self._players:
            if pygame.Rect.colliderect(self._ball.circle, player.rect):
                self._ball.hit()

        self._player1.update()
        self._player2.update()

        point = self._ball.update()

        if point == -1:
            self._player1.score += 1
        if point == 1:
            self._player2.score += 1

        if point:
            self._ball.reset()

        self._player1.display()
        self._player2.display()
        self._ball.display()

        self._player1.display_score("Player1", (100, 20), WHITE)
        self._player2.display_score(
            "Player2", (self._config.resolution[0]-100, 20), WHITE)
