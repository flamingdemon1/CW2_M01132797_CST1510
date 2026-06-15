import pandas as pd
from app_model.db import DATA_FOLDER


DATASETS_METADATA_FILE = DATA_FOLDER / "datasets_metadata.csv"


def migrate_datasets_metadata(conn):
    """Move datasets_metadata.csv into a SQLite table."""
    data = pd.read_csv(DATASETS_METADATA_FILE)
    data.to_sql("datasets_metadata", conn, if_exists="replace", index=False)


def get_all_datasets_metadata(conn):
    """Return all dataset metadata as a pandas DataFrame."""
    sql = "SELECT * FROM datasets_metadata;"
    return pd.read_sql(sql, conn)