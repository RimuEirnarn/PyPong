"""Universal utility"""
# pylint: disable=method-hidden,redefined-builtin,no-name-in-module,protected-access
from logging import Logger
from shlex import shlex
from socket import AddressFamily, SocketKind, socket
from threading import Condition, Event
from typing import Callable, Literal

from _socket import dup

from .typings import Addr
from .locals import PSEUDOENV
from .envtoml import load_from_file


class TruthEvent(Condition):
    """A truthful event for those who need. Basically likes and event except that,
    you can use if statement. You can also use typical usage of Condition."""

    def __init__(self, lock=None) -> None:
        super().__init__(lock)
        self._event = Event()

    def __bool__(self):
        return self._event.is_set()

    def acquire(self, blocking: bool = ..., timeout: float = ...) -> bool:
        """Please refer to Threading `Condition`."""
        acquired = super().acquire(blocking, timeout)  # pylint: disable=no-member
        if acquired:
            self._event.set()
        return acquired

    def release(self) -> None:
        """Please refer to Threading `Condition`."""
        self._event.clear()
        return super().release()  # pylint: disable=no-member


def map_addr(addr: Addr | str):
    """Map address to string."""
    if isinstance(addr, tuple):
        return f"{addr[0]}:{addr[1]}"
    return addr


class LoggedSocket(socket):
    """Log your socket to a logger"""

    def __init__(self,
                 family: AddressFamily | int = -1,
                 type: SocketKind | int = -1,
                 proto: int = -1,
                 fileno: int | None = None) -> None:
        super().__init__(family, type, proto, fileno)
        self._logger = None

    def put_logger(self, logger: Logger):
        """Put logger to log send and recv data."""
        self._logger = logger

    def send(self, __data: bytes, __flags: int = 0) -> int:
        """Send data to peer.

        Args:
            __data (bytes): Data need to be send
            __flags (int, optional): Flags. Defaults to 0.

        Returns:
            int: Bytes sent
        """
        sent = super().send(__data, __flags)
        if self._logger:
            self._logger.debug((sent, __data))
        return sent

    def recv(self, __bufsize: int, __flags: int = 0) -> bytes:
        """Read data from peer

        Args:
            __bufsize (int): Number of buffer need to grab
            __flags (int, optional): Flags. Defaults to 0.

        Returns:
            bytes: Bytes received.
        """
        buff = super().recv(__bufsize, __flags)
        if self._logger:
            self._logger.debug(buff)
        return buff

    @classmethod
    def copy(cls, sock: socket):
        """Copy socket to this class implementation."""
        fd = dup(sock.fileno())
        copy = cls(sock.family, sock.type, sock.proto, fileno=fd)
        copy.settimeout(sock.gettimeout())
        copy.setblocking(sock.getblocking())
        return copy

    def accept(self) -> tuple[socket, Addr]:
        """Accept incoming connection"""
        sock, addr = super().accept()  # pylint: disable=no-member
        new = self.copy(sock)
        sock.close()
        if self._logger:
            new.put_logger(self._logger)
        return new, addr


def guess_type(string: str):
    """Guess a int, float base from string. Return strign if not any match."""
    if string.isdigit():
        return int(string)
    if string.isdecimal():
        return float(string)
    return string


def map_args(arg: str, guess: bool = False):
    """Map an argument to something else"""
    return (a for a in shlex(arg)) if not guess else (guess_type(a) for a in shlex(arg))


def mapped(func: Callable[..., None | Literal[True]]):
    """Map basic Cmd function/command to as compatible as ever."""

    def wrapper(self, arg):
        return func(self, map_args(arg, True))
    wrapper._raw = func
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    wrapper.__doc__ = func.__doc__
    return wrapper


def no_arg(func: Callable[..., None | Literal[True]]):
    """Map basic Cmd that require no argument."""

    def wrapper(self, arg):  # pylint: disable=unused-argument
        return func(self)

    wrapper._raw = func
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    wrapper.__doc__ = func.__doc__
    return wrapper


def load_environ():
    """Load environ from Pseudo Environ"""
    return load_from_file(str(PSEUDOENV))
