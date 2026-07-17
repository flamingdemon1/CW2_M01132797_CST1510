"""Helpers for exporting Gatekeeper results to files or SQLite."""

import csv
from datetime import datetime
from app_model import schema
from app_model.db import DATA_FOLDER


EXPORT_FOLDER = DATA_FOLDER / "exports"

#used underscores before some functions to indicate it is for private use only

def _creation_time():
    """Returns a timestamp for files and database records."""
    return datetime.now().isoformat(timespec="seconds")


def _safe_filename(title):
    """Makes sure a title is safe to use."""
    safe_characters = []

    for char in title.strip().lower():
        if char.isalnum():
            safe_characters.append(char)
        elif char in {" ", "_", "-"}:
            safe_characters.append("_")

    safe_name = "".join(safe_characters).strip("_")
    return safe_name or "gatekeeper_result"


def _validate_content(content):
    """Reject an empty result before attempting to save it."""
    if content is None or str(content).strip() == "":
        raise ValueError("There is no result content to save.")


def save_result_to_text(
    username,
    result_type,
    title,
    content,
    save_source="CLI",
):
    """Save raw results in a UTF-8 text file."""
    _validate_content(content)
    EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    created_at = _creation_time()
    #we use hypens instead of colons because colons aren't allowed in windows filenames
    ts = created_at.replace(":", "-")
    file_path = EXPORT_FOLDER / (
        f"{_safe_filename(title)}_{ts}.txt"
    )
    text = (
        f"Title: {title}\n"
        f"Result type: {result_type}\n"
        f"Saved by: {username}\n"
        f"Saved from: {save_source}\n"
        f"Created at: {created_at}\n\n"
        f"{content}\n"
    )
    file_path.write_text(text, encoding="utf-8")
    return file_path


def save_result_to_csv(
    username,
    result_type,
    title,
    content,
    df=None,
    save_source="CLI",
):
    """Handles both pandas df exports and single-row fallbacks."""
    _validate_content(content)
    EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    created_at = _creation_time()
    ts = created_at.replace(":", "-")
    file_path = EXPORT_FOLDER / (
        f"{_safe_filename(title)}_{ts}.csv"
    )

    if df is not None and not df.empty:
        csv_data = df.copy()
        csv_data.insert(0, "save_username", username)
        csv_data.insert(1, "save_result_type", result_type)
        csv_data.insert(2, "save_title", title)
        csv_data.insert(3, "save_created_at", created_at)
        csv_data.insert(4, "save_source", save_source)
        csv_data.to_csv(file_path, index=False, encoding="utf-8")
    else:
        with file_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "username",
                    "result_type",
                    "title",
                    "content",
                    "created_at",
                    "save_source",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "username": username,
                    "result_type": result_type,
                    "title": title,
                    "content": content,
                    "created_at": created_at,
                    "save_source": save_source,
                }
            )

    return file_path


def save_result_to_database(
    conn,
    username,
    result_type,
    title,
    content,
    save_source="CLI",
):
    """Insert one saved result into the project SQLite database."""
    _validate_content(content)
    schema.create_saved_results_table(conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO saved_results (
            username,
            result_type,
            title,
            content,
            created_at,
            save_source
        )
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            username,
            result_type,
            title,
            str(content),
            _creation_time(),
            save_source,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_saved_results(conn, username=None):
    """Get saved-result summaries, optionally for one user."""
    schema.create_saved_results_table(conn)
    cursor = conn.cursor()

    sql = """
        SELECT id, username, result_type, title, created_at, save_source
        FROM saved_results
    """
    params = []

    if username is not None:
        sql += " WHERE username = ?"
        params.append(username)

    sql += " ORDER BY id DESC;"
    cursor.execute(sql, tuple(params))
    return cursor.fetchall()

def get_saved_result(conn, result_id, username=None):
    """Get one complete saved result, optionally limited to its owner."""
    schema.create_saved_results_table(conn)
    cursor = conn.cursor()

    sql = "SELECT * FROM saved_results WHERE id = ?"
    params = [result_id]

    if username is not None:
        sql += " AND username = ?"
        params.append(username)

    cursor.execute(sql, tuple(params))
    return cursor.fetchone()
