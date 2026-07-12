"""CISA Known Exploited Vulnerabilities data helpers."""

import pandas as pd

from app_model.db import DATA_FOLDER


# AI assistance was used for integration planning, visualisation refinement,
# and debugging. The source dataset itself is official CISA data and was not
# generated or modified by AI.

CISA_KEV_FILE = DATA_FOLDER / "external" / "known_exploited_vulnerabilities.csv"
CISA_KEV_TABLE = "cisa_known_exploited_vulnerabilities"

EXPECTED_COLUMNS = [
    "cveID",
    "vendorProject",
    "product",
    "vulnerabilityName",
    "dateAdded",
    "shortDescription",
    "requiredAction",
    "dueDate",
    "knownRansomwareCampaignUse",
    "notes",
    "cwes",
]


def _validate_columns(data):
    """Check that the CISA CSV has the expected catalogue columns."""
    missing_columns = [column for column in EXPECTED_COLUMNS if column not in data.columns]

    if missing_columns:
        missing_names = ", ".join(missing_columns)
        raise ValueError(f"CISA KEV CSV is missing columns: {missing_names}")


def migrate_cisa_kev(conn):
    """Move the CISA KEV CSV into its own SQLite table."""
    if not CISA_KEV_FILE.is_file():
        raise FileNotFoundError(
            "DATA/external/known_exploited_vulnerabilities.csv was not found."
        )

    data = pd.read_csv(CISA_KEV_FILE, dtype=str).fillna("")
    _validate_columns(data)
    data = data[EXPECTED_COLUMNS]
    data.to_sql(CISA_KEV_TABLE, conn, if_exists="replace", index=False)


def get_all_cisa_kev(conn):
    """Return all migrated CISA KEV records as a DataFrame."""
    sql = f"SELECT * FROM {CISA_KEV_TABLE};"
    data = pd.read_sql(sql, conn)
    _validate_columns(data)
    return data


def get_cisa_kev_summary(conn):
    """Return safe dashboard-style CISA KEV summary counts."""
    data = get_all_cisa_kev(conn).copy()
    date_added = pd.to_datetime(data["dateAdded"], errors="coerce")
    latest_date = date_added.max()

    if pd.isna(latest_date):
        latest_30_days = 0
    else:
        latest_30_days = int((date_added >= latest_date - pd.Timedelta(days=30)).sum())

    return {
        "total_vulnerabilities": len(data),
        "vendor_count": data["vendorProject"].replace("", pd.NA).nunique(),
        "ransomware_count": int(
            data["knownRansomwareCampaignUse"]
            .fillna("")
            .str.lower()
            .eq("known")
            .sum()
        ),
        "latest_30_days": latest_30_days,
        "top_vendors": data["vendorProject"].fillna("Unknown").value_counts().head(10),
        "ransomware_distribution": data["knownRansomwareCampaignUse"]
        .replace("", "Unknown")
        .fillna("Unknown")
        .value_counts(),
    }
