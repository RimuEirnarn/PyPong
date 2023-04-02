"""Basic GUI package"""
# pylint: disable=no-member,too-many-instance-attributes,unused-argument,no-name-in-module
import pygame
from pygame.locals import QUIT, KEYDOWN, KEYUP
from pygame.event import Event
from pygame.time import Clock

from .typings import Resolution
from .config import AppConfig


class BaseApp:
    """Base App. The configuration is atleast available like the `example.gconf.toml` file."""
    _INIT = False

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._running = False
        self._surface_ = None
        self._is_fullscreen = False
        self._clock_ = None
        self._title = ""

    @property
    def title(self):
        """Game/Window title"""
        return self._title

    @title.setter
    def title(self, value: str):
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        if not isinstance(value, str):
            value = str(value) if hasattr(value, "__str__") else repr(value)
        self._title = value
        if BaseApp._INIT:
            pygame.display.set_caption(self._title)

    def toggle_fullscreen(self):
        """Toggle fullscreen. Requires initialisation."""
        if not BaseApp._INIT:
            raise RuntimeError("Pygame is not loaded.")
        if not self._is_fullscreen:
            self._init_display((0, 0), pygame.FULLSCREEN)
            self._is_fullscreen = True
            return
        self._init_display(self._config.resolution)
        self._is_fullscreen = False

    def _init_display(self,
                      resolution: Resolution,
                      flags: int = 0,
                      depth: int = 0,
                      display: int = 0,
                      vsync: int = 0):
        if self._surface_:
            pygame.display.quit()
            pygame.display.init()
        self._surface = pygame.display.set_mode(
            resolution, flags, depth, display, vsync)

    def init(self):
        """Do initializing"""
        if BaseApp._INIT:
            return
        BaseApp._INIT = True
        pygame.init()
        pygame.display.set_caption("Application")
        self._clock = Clock()
        self._is_fullscreen = self._config.full
        if not self._config.full:
            self._init_display(self._config.resolution)
        else:
            self._init_display((0, 0), pygame.FULLSCREEN)

    @property
    def _surface(self):
        """Surface data"""
        if self._surface_ is None:
            raise RuntimeError("No screen surface available")
        return self._surface_

    @_surface.setter
    def _surface(self, surface: pygame.Surface):
        """Surface data"""
        if not isinstance(surface, pygame.Surface):
            raise TypeError("Surface type is required")
        self._surface_ = surface

    @property
    def _clock(self):
        """Clock data"""
        if self._clock_ is None:
            raise RuntimeError("No screen surface available")
        return self._clock_

    @_clock.setter
    def _clock(self, clock: Clock):
        """Clock data"""
        if not isinstance(clock, Clock):
            raise TypeError("Clock type is required")
        self._clock_ = clock

    def on_event(self, event: Event):
        """Events"""
        if event.type == QUIT:
            self.on_exit()
            self._exit()
            return True
        if event.type == KEYDOWN:
            self.on_keydown(event)
        if event.type == KEYUP:
            self.on_keyup(event)
        return None

    def on_exit(self):
        """On exit event"""
        self._running = False

    def on_keydown(self, event: Event):
        """Keydown Events"""
        return NotImplemented

    def on_keyup(self, event: Event):
        """Keyup events"""
        return NotImplemented

    def on_main(self):
        """Main something. Anything besides events, and updates."""
        return NotImplemented

    def on_update(self):
        """Update function. You can override or using super() method.
        It just updates the screen and ticks it at MAXFPS (defined in your gconf.toml)"""
        pygame.display.update()
        self._clock.tick(self._config.MAXFPS)

    def main_loop(self):
        """Run the program"""
        if BaseApp._INIT is False:
            self.init()
        exit_request = None
        while self._running:
            for event in pygame.event.get():
                exit_request = self.on_event(event)

            if exit_request:
                break
            self.on_main()

            self.on_update()

    @staticmethod
    def _exit():
        if BaseApp._INIT:
            pygame.quit()
            BaseApp._INIT = False
            return

    @staticmethod
    def exit(event: Event):
        """Exit from application. This does not entirely close the application."""
        if BaseApp._INIT is False:
            return
        if event.type == pygame.QUIT:
            pygame.quit()
            BaseApp._INIT = False
            return
