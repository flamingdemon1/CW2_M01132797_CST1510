def add_user(conn, username, password_hash, email=None):
    """Add a new user to the users table."""
    cursor = conn.cursor()

    sql = """
    INSERT INTO users (username, password_hash, email)
    VALUES (?, ?, ?);
    """

    cursor.execute(sql, (username, password_hash, email))
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


def get_user_by_username_or_email(conn, identifier):
    """Return one user matching a username or recovery email."""
    cursor = conn.cursor()

    username_sql = """
    SELECT *
    FROM users
    WHERE username = ?;
    """
    cursor.execute(username_sql, (identifier,))
    username_match = cursor.fetchone()

    if username_match is not None:
        return username_match

    email_sql = """
    SELECT *
    FROM users
    WHERE LOWER(email) = LOWER(?);
    """
    cursor.execute(email_sql, (identifier,))
    email_matches = cursor.fetchall()

    # A shared email is ambiguous, so recovery must use the username instead.
    return email_matches[0] if len(email_matches) == 1 else None


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


def update_password(conn, username, new_password_hash):
    """Update a user's password hash."""
    cursor = conn.cursor()

    sql = """
    UPDATE users
    SET password_hash = ?
    WHERE username = ?;
    """

    cursor.execute(sql, (new_password_hash, username))
    conn.commit()

    return cursor.rowcount > 0


def update_email(conn, username, new_email):
    """Update a user's recovery email address."""
    cursor = conn.cursor()

    sql = """
    UPDATE users
    SET email = ?
    WHERE username = ?;
    """

    cursor.execute(sql, (new_email, username))
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
