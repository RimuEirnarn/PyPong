"""Collections of Errors"""


class StateError(ValueError):
    """A state has been reached and now is raised."""


class ValidationError(ValueError):
    """validation did not pass"""
