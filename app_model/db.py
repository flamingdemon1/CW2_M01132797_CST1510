import sqlite3
from pathlib import Path


BASE_FOLDER = Path(__file__).resolve().parent.parent
DATA_FOLDER = BASE_FOLDER / "DATA"
DATABASE_FILE = DATA_FOLDER / "project_data.db"


def get_connection():
    """Create and return a connection to the SQLite database."""
    DATA_FOLDER.mkdir(exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    return conn