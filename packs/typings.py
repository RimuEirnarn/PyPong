"""Typings utility"""
# pylint: disable=too-few-public-methods
from selectors import DefaultSelector
from socket import socket
from typing import Any, NamedTuple, Protocol, TypedDict


ServerAddr = tuple[str, int]
Addr = tuple[str, int]
SelectSock = tuple[DefaultSelector, socket]


class TMessage(TypedDict):
    """Base prototype of Message"""
    headers: dict[str, Any]
    body: Any


class MessageRequest(NamedTuple):
    """Named tuple version of message"""
    headers: dict[str, Any]
    body: Any


class Status(Protocol):
    """use this to make sure some data is compatible as status"""
    description: str
    value: str
    name: str
