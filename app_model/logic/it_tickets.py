import pandas as pd
from app_model.db import DATA_FOLDER


IT_TICKETS_FILE = DATA_FOLDER / "it_tickets.csv"


def migrate_it_tickets(conn):
    """Move it_tickets.csv into a SQLite table."""
    data = pd.read_csv(IT_TICKETS_FILE)
    data.to_sql("it_tickets", conn, if_exists="replace", index=False)


def get_all_it_tickets(conn):
    """Return all IT tickets as a pandas DataFrame."""
    sql = "SELECT * FROM it_tickets;"
    return pd.read_sql(sql, conn)