def create_user_table(conn):
    """Create the users table if it does not already exist."""
    cursor = conn.cursor()

    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        email TEXT,
        role TEXT DEFAULT 'user'
    );
    """

    cursor.execute(sql)

    # Older coursework databases do not have an email column. This small
    # migration keeps their existing user records and adds email as optional.
    cursor.execute("PRAGMA table_info(users);")
    existing_columns = [column[1] for column in cursor.fetchall()]

    if "email" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT;")

    if "phone_number" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT;")

    if "two_factor_enabled" not in existing_columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN two_factor_enabled INTEGER DEFAULT 0;"
        )

    conn.commit()


def create_saved_results_table(conn):
    """Create the table shared by CLI and Streamlit saved results."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            result_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            save_source TEXT NOT NULL
        );
        """
    )
    conn.commit()
