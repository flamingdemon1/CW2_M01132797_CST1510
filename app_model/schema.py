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