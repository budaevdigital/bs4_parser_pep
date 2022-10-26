# constans.py
from pathlib import Path

# Path(__file__) — абсолютный путь до текущего файла;
# parent — директория, в которой он лежит.
BASE_DIR = Path(__file__).parent

MAIN_DOC_URL = "https://docs.python.org/3/"
MAIN_PEP_URL = "https://peps.python.org/"
DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
EXPECTED_STATUS = {
    "A": ["Active", "Accepted"],
    "D": ["Deferred"],
    "F": ["Final"],
    "P": ["Provisional"],
    "R": ["Rejected"],
    "S": ["Superseded"],
    "W": ["Withdrawn"],
    "": ["Draft", "Active"],
}
