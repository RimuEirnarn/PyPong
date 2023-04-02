"""Like python-env but only toml"""
from tomllib import loads
from os import environ


def load_from_file(filepath: str):
    """Load and store toml data from file"""
    with open(filepath, encoding='utf-8') as file:
        loaded = loads(file.read())
        environ.update(loaded)
