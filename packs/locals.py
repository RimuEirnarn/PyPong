"""Locals"""

from os.path import expanduser
from pathlib import Path

DATA_DIR = Path(expanduser("~/.pypong"))
LOG_DIR = DATA_DIR / "log"
PSEUDOENV = DATA_DIR / "psenv.toml"

if not DATA_DIR.exists():
    DATA_DIR.mkdir()


if not LOG_DIR.exists():
    LOG_DIR.mkdir()

if not PSEUDOENV.exists():
    with open("pseudoenv.toml", encoding='utf-8') as file:
        PSEUDOENV.write_text(file.read())
