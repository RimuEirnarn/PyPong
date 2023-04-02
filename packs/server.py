"""Server library"""
from binascii import Error as BinasciiError
from selectors import DefaultSelector, SelectorKey
from socket import AF_INET, SOCK_STREAM
from socket import socket as SocketClass
from threading import Event, Thread
from time import sleep
from traceback import format_exception


from .connection import (EVENT_READ, BaseMessage, IOMessage, Message,
                         event_read, make_message,
                         validate_message)
from .errors import StateError
from .locals import LOG_DIR
from .logging import FileConfig, SetupConfig, setup_logger
from .status import StatusEnum
from .typings import Addr, ServerAddr
from .tools import transform_error
from .utils import map_addr

CONFIG = SetupConfig(
    FileConfig(
        str(LOG_DIR / "log.txt"),
        "w"
    )
)
Logger, FileHandler, Console = setup_logger("server", CONFIG)

# DEVNOTE: I hate this.


class Server:  # pylint: disable=too-many-instance-attributes
    """Base Server class"""

    def __init__(self, addr: ServerAddr, listen_for: int = 0) -> None:
        self._addr = addr
        self._host, self._port = addr
        self._socket = SocketClass(AF_INET, SOCK_STREAM)
        # self._socket = LoggedSocket(AF_INET, SOCK_STREAM)
        # self._socket.put_logger(Logger)
        self._has_binded = False
        self._selector = DefaultSelector()
        self._closed = False
        self._running = Event()
        self._thread = None
        self._connections = listen_for
        self._clients: list[SocketClass] = []
        self._placeholder = addr == ("", 0)

    def _reject_accept(self, client: SocketClass, addr: Addr):
        client.send(transform_error(
            "Server is full", StatusEnum.ENOROOM))  # type: ignore
        Logger.info(
            "Connection at client: %s aborted, only allows %s connected clients",
            map_addr(addr),
            self._connections)
        sleep(0.2)
        client.close()

    def _accept(self):
        client, address = self._socket.accept()
        client.setblocking(False)
        if len(self._clients) == self._connections and self._connections > 0:
            self._reject_accept(client, address)
            return
        Logger.info("Connected at client: %s", map_addr(address))
        request = IOMessage(address)
        request.socket = client
        self._selector.register(client, EVENT_READ, request)
        self._clients.append(client)

    def _serve_client(self, key: SelectorKey, mask: int):
        Logger.debug(
            "Client %s attempt to %s", map_addr(key.data), "READ" if mask & EVENT_READ else 'NULL')
        if mask & EVENT_READ:
            closed = event_read(key, self._selector)
            data: IOMessage = key.data
            if closed:
                Logger.info(
                    "Connection to client %s has been closed", map_addr(data.address))
                self._clients.remove(key.fileobj)  # type: ignore
                return
            # Logger.debug(data.output)
            self._do_read(key.fileobj, Message(data.output))  # type: ignore
        # if mask & EVENT_WRITE:
        #     closed = event_write(key, self._selector)
        #     data: IORequest = key.data
        #     if closed:
        #         Logger.info(
        #             F"Connection to client {data.address[0]}:{data.address[1]} has been closed"
        #         )
        #         self._client_sock = None
        #         return

    def _close_client(self, client: SocketClass):
        try:
            client.send(make_message("You there?", {}))
        except ConnectionResetError:
            pass
        else:
            return
        client.close()
        self._clients.remove(client)
        self._selector.unregister(client)

    def _do_read(self, socket: SocketClass, request: BaseMessage):
        data = request.json()
        Logger.debug(
            "Current socket is main socket? %s", socket == self._socket)
        if not validate_message(data):  # type: ignore
            # Logger.debug("what?")
            socket.send(transform_error(
                "Invalid message data", StatusEnum.EBADREQ))  # type: ignore
            return
        events = self._selector.get_map()
        for _, key in events.items():
            if key.data is None:
                continue
            sock: SocketClass = key.data.socket
            self._do_send(sock, request=request, echo=data != "")

    def _do_send(self, socket: SocketClass, request: BaseMessage, echo: bool = True):
        if echo:
            try:
                # Logger.debug(
                # f"{ip} -> Decoded {request.unpack_raw()} RAW -> {request.raw_body()}")
                request.unpack_raw()
                socket.send(request.raw_body())
            except BinasciiError:
                socket.send(transform_error(
                    "Invalid message data", StatusEnum.EBADREQ))  # type: ignore
            except ConnectionResetError:
                self._close_client(socket)

    @property
    def closed(self):
        """Is server closed?"""
        return self._closed

    @property
    def running(self):
        """Is server running?"""
        return self._running.is_set()

    def setup(self):
        """Setup server"""
        if self._placeholder:
            raise RuntimeError("Cannot setup on placeholder server")
        if self._has_binded:
            raise StateError("The server has already been binded")
        self._socket.bind((self._host, self._port))
        self._socket.setblocking(False)
        self._socket.listen()
        Logger.info("Listening at %s", map_addr(self._addr))
        self._selector.register(self._socket, EVENT_READ)

    def _main_loop(self):
        if self._placeholder:
            raise RuntimeError("Cannot run on placeholder server")
        self._running.set()
        if self.closed:
            raise StateError(
                "Cannot re-run server, it has run the task before.")
        try:
            if not self._has_binded:
                self.setup()
            while self._running.is_set():
                events = self._selector.select(1)
                for key, mask in events:
                    # print(key.fileobj, mask, f"{mask | EVENT_READ = }",
                    #   f"{mask | EVENT_WRITE = }")
                    if key.data is None:
                        self._accept()
                    else:
                        self._serve_client(key, mask)
        except (EOFError, KeyboardInterrupt):
            Logger.info("Closing on EOF/Keyboard Interrupt.")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            Logger.error("Error occurred while trying to execute!")
            (LOG_DIR / "traceback.txt").write_text(''.join(format_exception(exc)))
            Logger.info("Traceback is saved. Loop will be closed.")
        finally:
            self._selector.close()
            self._closed = True

        Logger.info("Finished server instance.")

    def main_loop(self):
        """Start application main loop"""
        self._main_loop()

    def start_as_thread(self):
        """Start server thread"""
        thread = Thread(target=self._main_loop)
        thread.start()
        self._thread = thread
        return thread

    def stop_thread(self):
        """Stop server thread"""
        if not self._thread:
            return

        Logger.info("Stop thread is called. Attempting to close server thread")
        # if not self._peer:
        #     client = SocketClass(AF_INET, SOCK_STREAM)
        #     client.connect((self._host, self._port))
        #     client.send(BaseMessage(dumps({
        #         "message": "Stop!"
        #     })).pack_raw())
        #     client.recv(1024)
        #     sleep(1)
        #     client.close()
        # self._running.clear()
        for sock in self._clients:
            try:
                sock.close()
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        self._thread.join()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {len(self._clients)}/{self._connections}\
run={map_addr(self._addr)}>"
