"""Client library"""
from selectors import DefaultSelector, SelectorKey
from socket import AF_INET, SOCK_STREAM
from socket import socket as SocketClass
from threading import Event, Thread
from time import sleep
from typing import Any

from .connection import (EVENT_READ, IOMessage, Message, event_read,
                         make_message)
from .logging import FileConfig, SetupConfig, setup_logger
from .typings import ServerAddr
from .utils import TruthEvent, map_addr

ClientLog, FileHandler, Console = setup_logger("client", SetupConfig(
    FileConfig("client-log.txt", 'w')
))


class Client:  # pylint: disable=too-many-instance-attributes
    """Base client class"""

    def __init__(self, addr: ServerAddr) -> None:
        self._addr = addr
        self._host = addr[0]
        self._port = addr[1]
        self._selector = DefaultSelector()
        self._socket = SocketClass(AF_INET, SOCK_STREAM)
        # self._socket = LoggedSocket(AF_INET, SOCK_STREAM)
        # self._socket.put_logger(ClientLog)
        self._socket.connect(addr)
        self._socket.setblocking(False)
        self._response = IOMessage(addr)
        self._data = Message("")
        self._running = Event()
        self._thread = Thread(target=self._process_request)
        self._reading = TruthEvent()
        self._selector.register(self._socket, EVENT_READ, self._response)

    def push(self, data: Any):
        """Push data to server"""
        ClientLog.debug("Sending data")
        x = self._socket.send(make_message(data, {}))
        # ClientLog.debug(x)
        return x

    def read(self) -> bytes:
        """Read data from server"""
        ClientLog.debug("Reading data")
        while self._response.output == b'':
            sleep(0.1)
        self._data._data = self._response.output  # pylint: disable=protected-access
        # ClientLog.debug(f"Done reading. {self._data.unpack_raw()}")
        self._response.reset_output()
        return self._data.unpack_raw(False)  # type: ignore

    def json(self):
        """Read data from server and return JSON object"""
        while self._reading:
            sleep(0.1)
        self.read()
        return self._data.json()

    def _do_read(self, key: SelectorKey):
        with self._reading:
            event_read(key, self._selector)

    def _process_request(self):
        self._running.set()
        try:
            while self._running.is_set():
                events = self._selector.select()
                for key, mask in events:
                    if mask & EVENT_READ:
                        self._do_read(key)
        except KeyboardInterrupt:
            return
        finally:
            self._selector.close()
            self._socket.close()

    def start(self):
        """Start client thread"""
        ClientLog.info("Starting connect to server")
        self._thread.start()

    def stop(self):
        """Stop client thread"""
        ClientLog.info("Closing...")
        self._running.clear()
        self._socket.close()
        self._thread.join()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} -> {map_addr(self._addr)}\
[{map_addr(self._socket.getsockname())}]>"
