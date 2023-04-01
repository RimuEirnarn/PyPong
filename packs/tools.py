"""Basic tools to use"""
from .typings import Status
from .connection import make_message


def transform_error(body: str, error: Status) -> bytes:
    # """Create a basic error response."""
    """Create a basic error response

    Args:
        body (str): Body message.
        error (Status): Error passed from `StatusEnum`

    Returns:
        bytes: Packed message, ready to send
    """
    return make_message(body, {
        "EMessage": error.description,
        "EName": error.value,
        "ECode": error.name
    })
