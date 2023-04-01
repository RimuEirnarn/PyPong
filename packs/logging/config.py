"""Config logging"""
from logging import DEBUG
from typing import Literal, NamedTuple

DEFAULT_FORMAT = "[%(levelname)-8s] [%(asctime)s] [%(module)s@%(funcName)s[%(lineno)d]] %(message)s"


class FileConfig(NamedTuple):
    """File Config"""
    filename: str
    mode: Literal['a'] | Literal['w'] | Literal['ab'] | Literal['wb'] | str


class SetupConfig(NamedTuple):
    """Setup Config"""
    file: FileConfig
    format: str = DEFAULT_FORMAT
    level: int = DEBUG
    console: Literal['stderr'] | Literal['stdout'] | None = "stderr"
