"""Beginner-friendly helpers for exporting Gatekeeper results."""

import csv
from datetime import datetime

from app_model import schema
from app_model.db import DATA_FOLDER


EXPORT_FOLDER = DATA_FOLDER / "exports"


def _created_at():
    """Return one readable timestamp for files and database records."""
    return datetime.now().isoformat(timespec="seconds")


def _safe_filename(title):
    """Convert a result title into a safe, simple filename."""
    safe_characters = []

    for character in title.strip().lower():
        if character.isalnum():
            safe_characters.append(character)
        elif character in {" ", "_", "-"}:
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
    """Save a result and its basic details in a UTF-8 text file."""
    _validate_content(content)
    EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    created_at = _created_at()
    timestamp_for_file = created_at.replace(":", "-")
    file_path = EXPORT_FOLDER / (
        f"{_safe_filename(title)}_{timestamp_for_file}.txt"
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
    tabular_data=None,
    save_source="CLI",
):
    """Save tabular results, or one text result row, in CSV format."""
    _validate_content(content)
    EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    created_at = _created_at()
    timestamp_for_file = created_at.replace(":", "-")
    file_path = EXPORT_FOLDER / (
        f"{_safe_filename(title)}_{timestamp_for_file}.csv"
    )

    if tabular_data is not None and not tabular_data.empty:
        csv_data = tabular_data.copy()
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
            _created_at(),
            save_source,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_saved_results(conn, username=None):
    """Return saved-result summaries, optionally for one username only."""
    schema.create_saved_results_table(conn)
    cursor = conn.cursor()

    if username is None:
        cursor.execute(
            """
            SELECT id, username, result_type, title, created_at, save_source
            FROM saved_results
            ORDER BY id DESC;
            """
        )
    else:
        cursor.execute(
            """
            SELECT id, username, result_type, title, created_at, save_source
            FROM saved_results
            WHERE username = ?
            ORDER BY id DESC;
            """,
            (username,),
        )

    return cursor.fetchall()


def get_saved_result(conn, result_id, username=None):
    """Return one complete saved result, with optional owner filtering."""
    schema.create_saved_results_table(conn)
    cursor = conn.cursor()

    if username is None:
        cursor.execute("SELECT * FROM saved_results WHERE id = ?;", (result_id,))
    else:
        cursor.execute(
            """
            SELECT *
            FROM saved_results
            WHERE id = ? AND username = ?;
            """,
            (result_id, username),
        )

    return cursor.fetchone()
