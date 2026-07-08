import sqlite3
from pathlib import Path

# Find the project's main folder from db.py so the database path still works
# even when the program is started from a different directory.
BASE_FOLDER = Path(__file__).resolve().parent.parent
DATA_FOLDER = BASE_FOLDER / "DATA"
DATABASE_FILE = DATA_FOLDER / "project_data.db"


def get_connection():
    """Create and return a connection to the SQLite database."""
    # if the data folder doesn't exist , it gets created.
    DATA_FOLDER.mkdir(exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    # allows query results to be accessed using coloumn names
    conn.row_factory = sqlite3.Row

    return conn