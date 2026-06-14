import sqlite3
from pathlib import Path
import pandas as pd


BASE_FOLDER = Path(__file__).resolve().parent
DATA_FOLDER = BASE_FOLDER / "DATA"
DATABASE_FILE = DATA_FOLDER / "project_data.db"

CYBER_INCIDENTS_FILE = DATA_FOLDER / "cyber_incidents.csv"
DATASETS_METADATA_FILE = DATA_FOLDER / "datasets_metadata.csv"
IT_TICKETS_FILE = DATA_FOLDER / "it_tickets.csv"


def get_connection():
    """Create and return a connection to the SQLite database."""
    DATA_FOLDER.mkdir(exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE)

    # This allows us to access database columns by name, such as user["username"]
    conn.row_factory = sqlite3.Row

    return conn


def create_user_table(conn):
    """Create the users table if it does not already exist."""
    cursor = conn.cursor()

    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    );
    """

    cursor.execute(sql)
    conn.commit()


def add_user(conn, username, password_hash):
    """Add a new user to the users table."""
    cursor = conn.cursor()

    sql = """
    INSERT INTO users (username, password_hash)
    VALUES (?, ?);
    """

    cursor.execute(sql, (username, password_hash))
    conn.commit()


def get_user(conn, username):
    """Return one user by username."""
    cursor = conn.cursor()

    sql = """
    SELECT *
    FROM users
    WHERE username = ?;
    """

    cursor.execute(sql, (username,))
    return cursor.fetchone()


def get_all_users(conn):
    """Return all users from the users table."""
    cursor = conn.cursor()

    sql = """
    SELECT *
    FROM users;
    """

    cursor.execute(sql)
    return cursor.fetchall()


def update_user(conn, old_username, new_username):
    """Update a user's username."""
    cursor = conn.cursor()

    sql = """
    UPDATE users
    SET username = ?
    WHERE username = ?;
    """

    cursor.execute(sql, (new_username, old_username))
    conn.commit()

    return cursor.rowcount > 0


def delete_user(conn, username):
    """Delete a user from the users table."""
    cursor = conn.cursor()

    sql = """
    DELETE FROM users
    WHERE username = ?;
    """

    cursor.execute(sql, (username,))
    conn.commit()

    return cursor.rowcount > 0


def migrate_cyber_incidents(conn):
    """Move cyber_incidents.csv into a SQLite table."""
    data = pd.read_csv(CYBER_INCIDENTS_FILE)
    data.to_sql("cyber_incidents", conn, if_exists="replace", index=False)


def migrate_datasets_metadata(conn):
    """Move datasets_metadata.csv into a SQLite table."""
    data = pd.read_csv(DATASETS_METADATA_FILE)
    data.to_sql("datasets_metadata", conn, if_exists="replace", index=False)


def migrate_it_tickets(conn):
    """Move it_tickets.csv into a SQLite table."""
    data = pd.read_csv(IT_TICKETS_FILE)
    data.to_sql("it_tickets", conn, if_exists="replace", index=False)


def migrate_all_datasets(conn):
    """Move all CSV datasets into SQLite tables."""
    migrate_cyber_incidents(conn)
    migrate_datasets_metadata(conn)
    migrate_it_tickets(conn)


def get_all_cyber_incidents(conn):
    """Return all cyber incidents as a pandas DataFrame."""
    sql = "SELECT * FROM cyber_incidents;"
    return pd.read_sql(sql, conn)


def get_all_datasets_metadata(conn):
    """Return all dataset metadata as a pandas DataFrame."""
    sql = "SELECT * FROM datasets_metadata;"
    return pd.read_sql(sql, conn)


def get_all_it_tickets(conn):
    """Return all IT tickets as a pandas DataFrame."""
    sql = "SELECT * FROM it_tickets;"
    return pd.read_sql(sql, conn)