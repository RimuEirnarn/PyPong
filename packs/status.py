"""Status utility."""
from enum import StrEnum, unique, _simple_enum  # type: ignore


@unique  # type: ignore
@_simple_enum(StrEnum)
class StatusEnum:  # pylint: disable=too-few-public-methods
    """Status codes, phrase and description."""
    def __new__(cls, value, description=''):
        obj = str.__new__(cls, value)
        obj._value_ = value

        obj.description = description
        return obj
    # Ok.
    YES = ("Success", "Request successful")

    # Client Error
    EBADREQ = ("Bad Request", "User/client sends Not Great™ form of message.")

    # ENOACC probably unneeded. Since sockets are sockets.
    ENOACC = ("Access Denied",
              "User doesn't have enough permission to access resource")

    # Server Error
    EOVERLOAD = ("Server Overloaded",
                 "Hold tight, the server is overloaded. it'll back soon (hopefully)")
    EFAILURE = ("Server Failure",
                "Server was crashed! Let's hope it will be back soon.")

    # Misclenaous Error
    ENOROOM = ("No Room Available", "Please wait while the room is full.")
