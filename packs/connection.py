"""Universal module for managing connections"""
from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
from json import JSONDecodeError, dumps, loads
from logging import Logger
from selectors import EVENT_READ, EVENT_WRITE, DefaultSelector, SelectorKey
from socket import AF_INET, SOCK_STREAM
from socket import socket as SocketClass
from typing import Any, TypeGuard


from .errors import ValidationError
from .typings import Addr, SelectSock, ServerAddr, TMessage
from .utils import map_addr
from .logging import debug

READ_WRITE = EVENT_READ | EVENT_WRITE


class IOMessage:
    """Base class of basic Message. No headers just body."""

    def __init__(self, address: Addr) -> None:
        self._input: bytes = b""
        self._output: bytes = b""
        self._address = address
        self._socket = None
        self._input_upheld = False
        self._output_upheld = False

    @property
    def input_upheld(self):
        """Upheld reset on input buffer if true"""
        return self._input_upheld

    @input_upheld.setter
    def input_upheld(self, value: bool | None = None):
        """Upheld reset on input buffer if true"""
        if value is None:
            value = not self._input_upheld
        self._input_upheld = bool(value)

    @property
    def output_upheld(self):
        """Upheld reset on input buffer if true"""
        return self._input_upheld

    @output_upheld.setter
    def output_upheld(self, value: bool | None = None):
        """Upheld reset on output buffer if true"""
        if value is None:
            value = not self._output_upheld
        self._output_upheld = bool(value)

    @property
    def address(self):
        """Client address"""
        return self._address

    @property
    def input(self):
        """Input buffer"""
        return self._input

    @property
    def output(self):
        """Output buffer"""
        return self._output

    @input.setter
    def input(self, value: str | bytes):
        """Input buffer"""
        if isinstance(value, str):
            value = value.encode('utf-8')
        if self._input_upheld:
            return
        self._input = value

    @output.setter
    def output(self, value: str | bytes):
        """Output Buffer"""
        if isinstance(value, str):
            value = value.encode('utf-8')
        if self._output_upheld:
            return
        self._output = value

    def reset_input(self):
        """Reset input buffer"""
        self._input = b""

    def reset_output(self):
        """Reset output buffer"""
        self._output = b''

    @property
    def socket(self):
        """Return socket"""
        if self._socket is None:
            raise ValueError("Attempted to access undefined data")
        return self._socket

    @socket.setter
    def socket(self, value: SocketClass):
        """Socket"""
        if not isinstance(value, SocketClass):
            raise TypeError("Value must be a socket")
        self._socket = value

    def _map_addr(self):
        return map_addr(self._address)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} upheld-input={self._input_upheld} \
upheld-output={self._output_upheld} length=({len(self._input)}, {len(self._output)}) \
target={self._map_addr()}>"


class BaseMessage:
    """Message, bare part of Request and Response.
    Consists of body"""

    def __init__(self, data: bytes | str) -> None:
        if isinstance(data, str):
            data = data.encode('utf-8')
        self._data = data

    def pack_raw(self):
        """Pack raw data to base64"""
        data = b64encode(self._data)
        return data

    def unpack_raw(self, to_str=False):
        """Unpack b64 blob body to raw data."""
        data = b64decode(self._data)

        if to_str:
            return data.decode('utf-8')
        return data

    def json(self):
        """Return data as JSON if available, return empty string if can't"""
        try:
            return loads(self.unpack_raw(True))
        except JSONDecodeError:
            return ""

    def body(self) -> str:
        """Return unpacked base64 blob"""
        try:
            return self.unpack_raw(True)  # type: ignore
        except BinasciiError:
            return self._data  # type: ignore

    def raw_body(self):
        """Return raw data. Useful if the data isn't base64 blob"""
        return self._data

    def __repr__(self) -> str:
        return f"<{type(self).__name__} length={len(self._data)}>"


class Message(BaseMessage):
    """Message class, this has body and headers."""

    def __init__(self, data: bytes | str) -> None:
        super().__init__(data)
        self._invalid = False

    def json(self) -> TMessage:
        """Return data as valid Message data"""
        data = super().json()
        if self._invalid:
            raise ValidationError("Message data is not valid.")
        if not validate_message(data):  # type: ignore
            self._invalid = True
            raise ValidationError("Message data is not valid.")
        return data

    def body(self) -> Any:
        """Return body data"""
        return self.json()["body"]

    def headers(self) -> dict[str, Any]:
        """Return headers data"""
        return self.json()["headers"]


# def _read_until_parse_able(socket: SocketClass, holder: IOMessage):
#     data = b''
#     while True:
#         try:
#             socket.recv(1024)
#         except BlockingIOError:
#         try:
#             unpack(holder.output)
#             return holder.output
#         except BinasciiError:
#             pass

def event_read(key: SelectorKey, selector: DefaultSelector, __logger: Logger | None = None):
    """Read event function"""
    holder: IOMessage = key.data
    socket: SocketClass = key.fileobj  # type: ignore
    # holder.reset_output()
    ioerror = False
    data = b''

    while True:
        debug(__logger, holder)
        try:
            data += socket.recv(1024)
        except BlockingIOError:
            ioerror = True
            break
        except OSError:
            break

        if not data:
            break
    holder.output = data
    if holder.output:
        return None
    if holder.output_upheld:
        return None
    if ioerror:
        return None
    selector.unregister(socket)
    socket.close()
    return True


def event_write(key: SelectorKey, selector: DefaultSelector):
    """Write Event function"""
    holder: IOMessage = key.data
    socket: SocketClass = key.fileobj  # type: ignore

    try:
        sent = socket.send(holder.input)
        print(sent)
        holder.reset_input()
    except ConnectionAbortedError:
        socket.close()
        selector.unregister(socket)
        return True
    except OSError:
        return True
    return None


def _setup_client(selector: DefaultSelector, addr: ServerAddr, mask: int = READ_WRITE):
    socket = SocketClass(AF_INET, SOCK_STREAM)
    socket.setblocking(False)
    socket.connect_ex(addr)
    request = IOMessage(addr)
    selector.register(socket, mask, request)
    return socket


def process_event(key: SelectorKey, mask: int, selector: DefaultSelector):
    """Process event, this function uses event_* from this module."""
    if mask & EVENT_READ:
        event_read(key, selector)
    if mask & EVENT_WRITE:
        event_write(key, selector)


def setup_client_selectors(addr: ServerAddr, mask: int = READ_WRITE) -> SelectSock:
    """Setup client selectors"""
    selector = DefaultSelector()
    socket = _setup_client(selector, addr, mask)
    return selector, socket


def message_hook(key: SelectorKey):
    """Initiator for Message class."""
    data: None | IOMessage = key.data
    if data is None:
        raise ValueError("Hook on no data available socket.")
    return BaseMessage(data.output)


def pack(buffer: str | bytes) -> bytes:
    """Pack buffer to base64 blob"""
    return BaseMessage(buffer).pack_raw()


def unpack(buffer: bytes) -> str:
    """Unpack buffer to string."""
    return BaseMessage(buffer).unpack_raw(True)  # type: ignore


def validate_message(request: dict) -> TypeGuard[TMessage]:
    """Validate message data"""
    if not "headers" in request:
        return False
    if not "body" in request:
        return False

    if not isinstance(request['headers'], dict):
        return False
    return True


def _make_message(body: Any, headers: dict[str, Any]) -> TMessage:
    request = {
        "body": body,
        "headers": headers
    }
    if not validate_message(request):
        raise ValidationError("Not a valid message data.")
    return request


def make_message(body: Any, headers: dict[str, Any]):
    """Create a message with body and headers."""
    return pack(dumps(_make_message(body, headers)))
