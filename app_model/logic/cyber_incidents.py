import pandas as pd
from app_model.db import DATA_FOLDER


CYBER_INCIDENTS_FILE = DATA_FOLDER / "cyber_incidents.csv"


def migrate_cyber_incidents(conn):
    """Move cyber_incidents.csv into a SQLite table."""
    data = pd.read_csv(CYBER_INCIDENTS_FILE)
    data.to_sql("cyber_incidents", conn, if_exists="replace", index=False)


def get_all_cyber_incidents(conn):
    """Return all cyber incidents as a pandas DataFrame."""
    sql = "SELECT * FROM cyber_incidents;"
    return pd.read_sql(sql, conn)