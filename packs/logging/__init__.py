"""Logging utility"""
from atexit import register as atexit_register
from logging import FileHandler, Formatter, Logger, StreamHandler, getLogger
from sys import stderr, stdout

from .config import FileConfig, SetupConfig


def setup_logger(name: str, config: SetupConfig):
    """Setup a basic logger"""
    logger = getLogger(name)
    logger.setLevel(config.level)
    formatter = Formatter(config.format)
    handler_file = FileHandler(*config.file, encoding="utf-8")
    output = None
    if config.console == 'stderr':
        output = stderr
    if config.console == 'stdout':
        output = stdout

    def shutdown_log():
        logger.info("Reaching end of interpreter, closing...")

    atexit_register(shutdown_log)
    if output is None:
        handler_file.setFormatter(formatter)
        logger.addHandler(handler_file)
        return logger, handler_file, None
    handler_console = StreamHandler(output)
    handler_file.setFormatter(formatter)
    handler_console.setFormatter(formatter)
    logger.addHandler(handler_file)
    logger.addHandler(handler_console)
    return logger, handler_file, handler_console


__all__ = ['SetupConfig', 'FileConfig', "setup_logger"]


def debug(logger: Logger | None, data):
    """debug"""
    if not logger:
        return
    logger.debug(data)


def info(logger: Logger | None, data):
    """info"""
    if not logger:
        return
    logger.info(data)
