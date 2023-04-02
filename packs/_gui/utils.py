"""GUI Utility"""
from tomllib import loads
from .config import AppConfig
from ..locals import DATA_DIR

CONFIG = DATA_DIR / "config"
GCONF = CONFIG / "gconf.toml"

if not CONFIG.exists():
    CONFIG.mkdir()

if not GCONF.exists():
    with open("gconf.toml", encoding='utf-8') as file:
        GCONF.write_text(file.read())


def load_data():
    """Load Graphical Configuration"""
    with open(GCONF, encoding='utf-8') as gconffile:
        return AppConfig(**loads(gconffile.read()))
