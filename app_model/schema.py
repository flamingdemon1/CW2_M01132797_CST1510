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

    conn.commit()
