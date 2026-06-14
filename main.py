import sqlite3
from getpass import getpass

import bcrypt

import database


def generate_hash(password):
    """Convert a plain password into a bcrypt hash."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    return hashed_password.decode("utf-8")


def is_valid_hash(password, stored_hash):
    """Check if a plain password matches the stored bcrypt hash."""
    password_bytes = password.encode("utf-8")
    stored_hash_bytes = stored_hash.encode("utf-8")

    return bcrypt.checkpw(password_bytes, stored_hash_bytes)


def is_strong_password(password):
    """Check whether a password meets basic strength requirements."""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")

    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one number.")

    if not any(not char.isalnum() for char in password):
        errors.append("Password must contain at least one symbol.")

    if errors:
        print("\nWeak password:")
        for error in errors:
            print(f"- {error}")
        return False

    return True


def register_user(conn):
    """Register a new user and store their hashed password in SQLite."""
    username = input("Enter your username: > ").strip()

    if username == "":
        print("Username cannot be empty.")
        return

    existing_user = database.get_user(conn, username)

    if existing_user is not None:
        print("This username already exists. Please choose another one.")
        return

    while True:
        password = getpass("Enter your password: > ")

        if is_strong_password(password):
            break

        print("Please try again with a stronger password.")

    hashed_password = generate_hash(password)

    try:
        database.add_user(conn, username, hashed_password)
        print("User successfully registered!")

    except sqlite3.IntegrityError:
        print("This username already exists. Please choose another one.")


def login_user(conn):
    """Check whether a username and password are valid using SQLite."""
    username = input("Enter your username: > ").strip()
    password = getpass("Enter your password: > ")

    user = database.get_user(conn, username)

    if user is None:
        return None

    stored_hash = user["password_hash"]

    if is_valid_hash(password, stored_hash):
        return username

    return None


def display_all_users(conn):
    """Display all registered users if the admin password is correct."""
    admin_password = "Aisha!200"
    attempts_left = 3

    print("\n### Admin access required to view all users ###\n")

    while attempts_left > 0:
        entered_password = getpass("Enter the admin password to view all users: > ")

        if entered_password == admin_password:
            users = database.get_all_users(conn)

            if len(users) == 0:
                print("No users have been registered yet.")
                return

            print("\nRegistered Users")
            print("-" * 60)
            print(f"{'ID':<5}{'Username':<20}{'Role':<15}{'Password Hash'}")
            print("-" * 60)

            for user in users:
                short_hash = user["password_hash"][:15] + "..."
                print(f"{user['id']:<5}{user['username']:<20}{user['role']:<15}{short_hash}")

            return

        attempts_left -= 1
        print(f"Incorrect password. Attempts left: {attempts_left}")

    print("Too many incorrect attempts. Access denied.")


def update_username(conn):
    """Update an existing username."""
    old_username = input("Enter the current username: > ").strip()
    new_username = input("Enter the new username: > ").strip()

    if old_username == "" or new_username == "":
        print("Usernames cannot be empty.")
        return

    try:
        updated = database.update_user(conn, old_username, new_username)

        if updated:
            print("Username updated successfully.")
        else:
            print("User not found.")

    except sqlite3.IntegrityError:
        print("The new username already exists. Please choose another one.")


def delete_user(conn):
    """Delete an existing user."""
    username = input("Enter the username to delete: > ").strip()

    if username == "":
        print("Username cannot be empty.")
        return

    confirmation = input(f"Are you sure you want to delete {username}? yes/no: > ").strip().lower()

    if confirmation != "yes":
        print("Delete cancelled.")
        return

    deleted = database.delete_user(conn, username)

    if deleted:
        print("User deleted successfully.")
    else:
        print("User not found.")


def migrate_csv_data(conn):
    """Move the CSV datasets into the SQLite database."""
    try:
        database.migrate_all_datasets(conn)
        print("CSV datasets successfully migrated into SQLite.")

    except FileNotFoundError:
        print("One or more CSV files were not found in the DATA folder.")


def preview_migrated_data(conn):
    """Preview the migrated SQLite data."""
    print("\nChoose a table to preview:")
    print("1. Cyber incidents")
    print("2. Datasets metadata")
    print("3. IT tickets")

    choice = input(": > ").strip()

    try:
        if choice == "1":
            data = database.get_all_cyber_incidents(conn)
            print(data.head().to_string(index=False))

        elif choice == "2":
            data = database.get_all_datasets_metadata(conn)
            print(data.head().to_string(index=False))

        elif choice == "3":
            data = database.get_all_it_tickets(conn)
            print(data.head().to_string(index=False))

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    except Exception:
        print("The data has not been migrated yet. Please choose option 6 first.")


def main():
    """Display the menu and allow the user to use the SQLite-based system."""
    conn = database.get_connection()
    database.create_user_table(conn)

    current_user = None

    while True:
        print("\n==============================")
        print(" Gatekeeper System Menu (GSM)")
        print("==============================")

        if current_user is None:
            print("Currently logged in as: Guest")
        else:
            print(f"Currently logged in as: {current_user}")

        print("1. Register")
        print("2. Log in")
        print("3. View all users")
        print("4. Update username")
        print("5. Delete user")
        print("6. Migrate CSV datasets to SQLite")
        print("7. Preview migrated data")
        print("8. Exit")
        print("9. Log out")

        choice = input(": > ").strip()

        if choice == "1":
            register_user(conn)

        elif choice == "2":
            if current_user is not None:
                print(f"You are already logged in as {current_user}.")
                print("Please log out before logging in as another user.")
            else:
                logged_in_user = login_user(conn)

                if logged_in_user is not None:
                    current_user = logged_in_user
                    print("Login successful!")
                else:
                    print("Incorrect username or password.")

        elif choice == "3":
            display_all_users(conn)

        elif choice == "4":
            update_username(conn)

        elif choice == "5":
            delete_user(conn)

        elif choice == "6":
            migrate_csv_data(conn)

        elif choice == "7":
            preview_migrated_data(conn)

        elif choice == "8":
            print("Goodbye!")
            conn.close()
            break
        elif choice == "9":
            if current_user is None:
                print("No user is currently logged in.")
            else:
                confirmation = input(
                    "Are you sure you want to log out? yes/no: > "
                ).strip().lower()

                if confirmation == "yes":
                    print(f"{current_user} has been logged out.")
                    current_user = None
                else:
                    print("Log out cancelled.")

        else:
            print("Invalid choice. Please enter a number from 1 to 9.")
     

if __name__ == "__main__":
    main()