ALLOWED_ROLES = {"user", "admin"}


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


def get_all_users_safe(conn):
    """Return account details that are safe to display to administrators."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users);")
    columns = {column["name"] for column in cursor.fetchall()}
    safe_columns = [
        "username",
        "COALESCE(role, 'user') AS role",
        """
            CASE
                WHEN email IS NOT NULL AND TRIM(email) <> '' THEN 'Configured'
                ELSE 'Not configured'
            END AS recovery_email_status
        """,
    ]

    if {"phone_number", "two_factor_enabled"}.issubset(columns):
        safe_columns.extend(
            [
                """
                    CASE
                        WHEN phone_number IS NOT NULL AND TRIM(phone_number) <> '' THEN 'Configured'
                        ELSE 'Not configured'
                    END AS phone_status
                """,
                """
                    CASE
                        WHEN COALESCE(two_factor_enabled, 0) = 1 THEN 'Enabled'
                        ELSE 'Disabled'
                    END AS two_factor_status
                """,
            ]
        )
    else:
        safe_columns.extend(
            [
                "'Not configured' AS phone_status",
                "'Disabled' AS two_factor_status",
            ]
        )

    if "created_at" in columns:
        safe_columns.append("created_at")

    select_columns = ",\n            ".join(safe_columns)
    cursor.execute(
        f"""
        SELECT
            {select_columns}
        FROM users
        ORDER BY username COLLATE NOCASE;
        """
    )
    return cursor.fetchall()


def count_admin_users(conn):
    """Return the number of accounts that currently have the admin role."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS total FROM users WHERE LOWER(role) = 'admin';"
    )
    return cursor.fetchone()["total"]


def update_user_role(conn, username, role):
    """Safely update one role while preserving at least one administrator."""
    normalised_role = role.strip().lower()

    if normalised_role not in ALLOWED_ROLES:
        raise ValueError("Role must be either user or admin.")

    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(role, 'user') AS role FROM users WHERE username = ?;",
        (username,),
    )
    account = cursor.fetchone()

    if account is None:
        raise ValueError("The selected account could not be found.")

    current_role = str(account["role"]).strip().lower()

    if (
        current_role == "admin"
        and normalised_role != "admin"
        and count_admin_users(conn) <= 1
    ):
        raise ValueError("The final administrator account cannot be demoted.")

    cursor.execute(
        "UPDATE users SET role = ? WHERE username = ?;",
        (normalised_role, username),
    )
    conn.commit()
    return cursor.rowcount > 0


def update_recovery_email(conn, username, email):
    """Add or replace one user's recovery email address."""
    normalised_email = email.strip().lower()

    if not normalised_email:
        raise ValueError("Recovery email cannot be empty.")

    return update_email(conn, username, normalised_email)


def update_phone_number(conn, username, phone_number):
    """Add or replace one user's verified SMS phone number."""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET phone_number = ? WHERE username = ?;",
        (phone_number.strip(), username),
    )
    conn.commit()
    return cursor.rowcount > 0


def set_two_factor_enabled(conn, username, enabled):
    """Turn SMS two-factor authentication on or off for one user."""
    enabled_value = 1 if enabled else 0
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET two_factor_enabled = ? WHERE username = ?;",
        (enabled_value, username),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_two_factor_status(conn, username):
    """Return the stored phone number and 2FA setting for one user."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            phone_number,
            COALESCE(two_factor_enabled, 0) AS two_factor_enabled
        FROM users
        WHERE username = ?;
        """,
        (username,),
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        "phone_number": row["phone_number"],
        "two_factor_enabled": bool(row["two_factor_enabled"]),
    }


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
