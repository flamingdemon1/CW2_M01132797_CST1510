import sqlite3
from getpass import getpass
import bcrypt
from app_model import db, export_service, schema, users as user_model
from app_model.logic import cyber_incidents, metadatas, it_tickets, cisa_kev


# AI assistance was used for SQLite and CSV migration improvements,
# Rich CLI presentation, refactoring suggestions, and debugging.



# Use exception handling to make sure rich is insalled , if not the program will not immediately crash
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table

    RICH_AVAILABLE = True
    console = Console()
    # if the exception is raised, rich is not installed and RICH_AVAILABLE is set to false.
except ImportError:
    RICH_AVAILABLE = False
    console = None
    Panel = Rule = Table = None


 # functions to help avoid repetition later in the program.
def print_successmsg(message):
    """Function to display a green success message."""
    console.print(message, style="bold green")


def print_errormsg(message):
    """Function to display a red  error message."""
    console.print(message, style="bold red")


def print_warningmsg(message):
    """Function to display a yellow  warning message."""
    console.print(message, style="yellow")


def print_infomsg(message):
    """Function to display a cyan  info message."""
    console.print(message, style="cyan")


def display_dataframe(data, title):
    """Display the first five dataframe rows as a Rich table."""
    preview = data.head()
    table = Table(title=title, header_style="bold cyan", border_style="blue")

    # rich expects strings, so str(coloumn) ensures every heading is text.
    for coloumn in preview.columns:
        table.add_column(str(coloumn))

    for row in preview.itertuples(index=False, name=None):
        table.add_row(*(str(value) for value in row))

    console.print(table)


def display_main_menu(current_user, current_role):
    """Display the Gatekeeper's CLI  menu """
    session_text = "Guest"

    if current_user is not None:
        session_text = f"{current_user} ({current_role})"

    menu = Table.grid(padding=(0, 2))
    menu.add_column(style="bold cyan", justify="right")
    menu.add_column(style="white")
   
    options = [
        ("1", "Register"),
        ("2", "Log in"),
        ("3", "View all users"),
        ("4", "Change username"),
        ("5", "Delete user"),
        ("6", "Migrate CSV datasets to SQLite"),
        ("7", "Preview migrated data"),
        ("8", "Exit"),
        ("9", "Log out"),
        ("10", "Create admin account"),
        ("11", "Change password"),
        ("12", "Export or save last preview"),
    ]

    for number, label in options:
        menu.add_row(number, label)

    console.print(
        Panel(
            menu,
            title="[bold cyan]Gatekeeper System Menu (GSM)[/bold cyan]",
            subtitle=f"[magenta]Session: {session_text}[/magenta]",
            border_style="blue",
            padding=(1, 3),
        )
    )


def generate_hash(password):
    """Convert  plain text into a bcrypt hash."""
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
    """Check whether passwords meet the pre-determined requirements."""
    errors = []
    # this operates on a point based system, where more points are awarded for stronger passwords and-
    # the opposite for weaker ones.
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")

    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one number.")

    if not any(not char.isalnum() for char in password):
        errors.append("Password must contain at least one symbol.")

    if errors:
        print_errormsg("Weak password:")
        for error in errors:
            print_errormsg(f"- {error}")
        return False

    return True


def get_username_errors(username):
    """Return a list of username format problems."""
    errors = []

 # These if statements check for typical username issues and output appropriate error messages.
    if len(username) < 3 or len(username) > 20:
        errors.append("Username must be 3 to 20 characters long.")

    if username != "" and not username[0].isalpha():
        errors.append("Username must start with a letter.")

    if not username.replace("_", "").isalnum():
        errors.append("Username can only contain letters, numbers, and underscores.")

    if " " in username:
        errors.append("Username cannot contain spaces.")

    return errors


def valid_username(username):
    """Check whether a username follows the project rules."""
    errors = get_username_errors(username)

    if errors:
        print_errormsg("Invalid username:")
        for error in errors:
            print_errormsg(f"- {error}")
        return False

    return True


def ensure_role_column(conn):
    """Make sure older users tables also have the role column."""
    cursor = conn.cursor()
   # Used pragma so that we do not have to recreate the users table and lose all existing users.
    cursor.execute("PRAGMA table_info(users);")
    columns = [column["name"] for column in cursor.fetchall()]

    if "role" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';")
        conn.commit()


def get_user_role(conn, username):
    """Return the role for a username."""
    user = user_model.get_user(conn, username)

    if user is None:
        return None

    if "role" in user.keys() and user["role"] is not None:
        return user["role"]

    return "user"


def require_admin(current_role, action_name):
    """Allow an action only when the logged-in user is an admin."""
    if current_role == "admin":
        return True

    print_errormsg(f"Admin access required to {action_name}.")
    print_warningmsg("Please log in with an admin account.")
    return False


def count_admin_users(conn):
    """Count how many admin users exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin';")
    return cursor.fetchone()[0]


def update_role(conn, username, role):
    """Update a user's role."""
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users
        SET role = ?
        WHERE username = ?;
        """,
        (role, username),
    )
    conn.commit()
    return cursor.rowcount > 0


def setup_admin_account(conn, current_role):
    """Create an admin account."""
    admin_count = count_admin_users(conn)

    if admin_count > 0 and not require_admin(
        current_role, "create another admin account"
    ):
        return

    console.print(Rule("[bold cyan]Create Admin Account[/bold cyan]"))

    if admin_count == 0:
        print_infomsg("No admin account exists yet, so you can create the first one now.")

    username = input("Enter the admin username: > ").strip()

    if not valid_username(username):
        return

    existing_user = user_model.get_user(conn, username)

    if existing_user is not None:
        existing_role = (
            existing_user["role"] if "role" in existing_user.keys() else "user"
        )

        if existing_role == "admin":
            print_warningmsg("This account is already an admin.")
            return

        if admin_count == 0:
            password = getpass(
                "This user already exists. Enter their password to make them admin: > "
            )

            if not is_valid_hash(password, existing_user["password_hash"]):
                print_errormsg("Incorrect password. Admin setup cancelled.")
                return
        else:
            confirmation = input(
                f"{username} already exists. Type yes to make this user admin: > "
            ).strip().lower()

            if confirmation != "yes":
                print_warningmsg("Admin setup cancelled.")
                return

        update_role(conn, username, "admin")
        print_successmsg("Admin access added to this account.")
        return

    while True:
        password = getpass("Enter the admin password: > ")

        if is_strong_password(password):
            break

        print_warningmsg("Please try again with a stronger password.")

    hashed_password = generate_hash(password)

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, 'admin');
        """,
        (username, hashed_password),
    )
    conn.commit()

    print_successmsg("Admin account created successfully.")
    print_infomsg("You can now log in with this admin account.")


def register_user(conn):
    """Register a new user and store their hashed password in SQLite."""
    username = input("Enter your username: > ").strip()

    if not valid_username(username):
        return

    existing_user = user_model.get_user(conn, username)

    if existing_user is not None:
        print_errormsg("This username already exists. Please choose another one.")
        return

    while True:
        password = getpass("Enter your password: > ")

        if is_strong_password(password):
            break

        print_warningmsg("Please try again with a stronger password.")

    hashed_password = generate_hash(password)

    try:
        user_model.add_user(conn, username, hashed_password)
        print_successmsg("User successfully registered!")
     
    # Error handling to prevent conflicts with data integrity.
    except sqlite3.IntegrityError:
        print_errormsg("This username already exists. Please choose another one.")


def login_user(conn):
    """Check whether a username and password are valid using SQLite."""
    username = input("Enter your username: > ").strip()
    password = getpass("Enter your password: > ")

    user = user_model.get_user(conn, username)

    if user is None:
        return None

    stored_hash = user["password_hash"]

    if is_valid_hash(password, stored_hash):
        return username

    return None


def display_all_users(conn, current_role):
    """Display all registered users if the logged-in user is an admin."""
    if not require_admin(current_role, "view all users"):
        return

    registered_users = user_model.get_all_users(conn)

    if len(registered_users) == 0:
        print_warningmsg("No users have been registered yet.")
        return

    table = Table(
        title="Registered Users",
        header_style="bold cyan",
        border_style="blue",
    )
    table.add_column("ID", justify="right")
    table.add_column("Username", style="white")
    table.add_column("Role", style="magenta")

    for user in registered_users:
        role = user["role"] if "role" in user.keys() else "user"
        table.add_row(str(user["id"]), str(user["username"]), str(role))

    console.print(table)


def update_username(conn, current_user, current_role):
    """Update a username using either user-level or admin-level access."""
    if current_user is None:
        print_warningmsg("Please log in before updating a username.")
        return current_user

    if current_role == "admin":
        old_username = input("Enter the username to update: > ").strip()

        if old_username == "":
            print_errormsg("Username cannot be empty.")
            return current_user

        if user_model.get_user(conn, old_username) is None:
            print_errormsg("User not found.")
            return current_user

    else:
        old_username = current_user
        user = user_model.get_user(conn, current_user)

        if user is None:
            print_errormsg("Your account could not be found. Please log in again.")
            return current_user

        password = getpass("Enter your current password to confirm this change: > ")

        if not is_valid_hash(password, user["password_hash"]):
            print_errormsg("Incorrect password. Username update denied.")
            return current_user

        print_infomsg(f"You are updating your own username: {current_user}")

    new_username = input("Enter the new username: > ").strip()
    confirm_username = input("Enter the new username again: > ").strip()

    if new_username != confirm_username:
        print_errormsg("Usernames do not match. Username update cancelled.")
        return current_user

    if not valid_username(new_username):
        return current_user

    if new_username == old_username:
        print_warningmsg("The new username is the same as your current username.")
        return current_user

    try:
        updated = user_model.update_user(conn, old_username, new_username)

        if updated:
            print_successmsg("Username updated successfully.")
            if old_username == current_user:
                return new_username
            return current_user
        else:
            print_errormsg("User not found.")
            return current_user

    except sqlite3.IntegrityError:
        print_errormsg("The new username already exists. Please choose another one.")
        return current_user


def change_password(conn, current_user):
    """Allow  logged-in users to change their passwords."""
    if current_user is None:
        print_warningmsg("Please log in before changing your password.")
        return

    user = user_model.get_user(conn, current_user)

    if user is None:
        print_errormsg("Your account could not be found. Please log in again.")
        return

    current_password = getpass("Enter your current password: > ")

    if not is_valid_hash(current_password, user["password_hash"]):
        print_errormsg("Incorrect password. Password change denied.")
        return

    show_password = input(
        "Show the new password while typing? yes/no: > "
    ).strip().lower()

    if show_password == "yes":
        new_password = input("Enter your new password: > ")
        confirm_password = input("Enter your new password again: > ")
    else:
        new_password = getpass("Enter your new password: > ")
        confirm_password = getpass("Enter your new password again: > ")

    if new_password != confirm_password:
        print_errormsg("New passwords do not match. Password change cancelled.")
        return

    if not is_strong_password(new_password):
        print_warningmsg("Password change cancelled.")
        return

    new_password_hash = generate_hash(new_password)
    updated = user_model.update_password(conn, current_user, new_password_hash)

    if updated:
        print_successmsg("Password updated successfully.")
    else:
        print_errormsg("Password could not be updated.")


def delete_user(conn, current_role):
    """Allows an admin to delete an existing user."""
    if not require_admin(current_role, "delete a user"):
        return None

    username = input("Enter the username to delete: > ").strip()

    if username == "":
        print_errormsg("Username cannot be empty.")
        return None

    user = user_model.get_user(conn, username)

    if user is None:
        print_errormsg("User not found.")
        return None

    user_role = user["role"] if "role" in user.keys() else "user"
     
    if user_role == "admin" and count_admin_users(conn) <= 1:
        print_errormsg("You cannot delete the only admin account.")
        print_warningmsg("Create another admin account first, then try again.")
        return None

    confirmation = input(
        f"Deleting {username} cannot be undone. Type yes to confirm: > "
    ).strip().lower()

    if confirmation != "yes":
        print_warningmsg("Delete cancelled.")
        return None

    deleted = user_model.delete_user(conn, username)

    if deleted:
        print_successmsg("User deleted successfully.")
        return username

    print_errormsg("User could not be deleted.")
    return None


def migrate_csv_data(conn, current_role):
    """Move the CSV datasets into SQLite if the logged-in user is an admin."""
    if not require_admin(current_role, "migrate CSV datasets to SQLite"):
        return

    confirmation = input(
        "This will replace the migrated dataset tables in SQLite. Continue? yes/no: > "
    ).strip().lower()

    if confirmation != "yes":
        print_warningmsg("CSV migration cancelled.")
        return

    try:
        cyber_incidents.migrate_cyber_incidents(conn)
        metadatas.migrate_datasets_metadata(conn)
        it_tickets.migrate_it_tickets(conn)
        cisa_kev.migrate_cisa_kev(conn)

        print_successmsg("CSV datasets successfully migrated into SQLite.")

    except FileNotFoundError:
        print_errormsg("One or more CSV files were not found in the DATA folder.")
    except ValueError as error:
        print_errormsg(f"CSV migration failed: {error}")


def preview_migrated_data(conn):
    """Preview the migrated SQLite data."""
    console.print(Rule("[bold cyan]Preview Migrated Data[/bold cyan]"))
    console.print("[cyan]1.[/cyan] Cyber incidents")
    console.print("[cyan]2.[/cyan] Datasets metadata")
    console.print("[cyan]3.[/cyan] IT tickets")
    console.print("[cyan]4.[/cyan] CISA known exploited vulnerabilities")

    choice = input(": > ").strip()

    try:
        if choice == "1":
            data = cyber_incidents.get_all_cyber_incidents(conn)
            title = "Cyber Incidents Preview"

        elif choice == "2":
            data = metadatas.get_all_datasets_metadata(conn)
            title = "Dataset Metadata Preview"

        elif choice == "3":
            data = it_tickets.get_all_it_tickets(conn)
            title = "IT Tickets Preview"

        elif choice == "4":
            data = cisa_kev.get_all_cisa_kev(conn)
            title = "CISA KEV Preview"

        else:
            print_errormsg("Invalid choice. Please enter 1, 2, 3, or 4.")
            return None

        if data.empty:
            print_warningmsg("This dataset is empty, so there is nothing to export.")
            return None

        preview = data.head()
        display_dataframe(data, title)
        print_infomsg("This preview is now available for option 12 export.")

        return {
            "title": title,
            "result_type": "Dataset Preview",
            "content": preview.to_string(index=False),
            "df": preview,
        }

    except Exception:
        print_warningmsg(
            "The data has not been migrated yet. Please choose option 6 first."
        )
        return None


def export_last_preview(conn, current_user, current_result):
    """Export the most recent safe dataset preview."""
    if current_user is None:
        print_warningmsg("Please log in before exporting a result.")
        return

    if current_result is None:
        print_warningmsg("No preview is available yet. Use option 7 first.")
        return

    console.print(Rule("[bold cyan]Export or Save Last Preview[/bold cyan]"))
    print_infomsg(f"Current preview: {current_result['title']}")
    console.print("[cyan]1.[/cyan] Save as text file")
    console.print("[cyan]2.[/cyan] Save as CSV file")
    console.print("[cyan]3.[/cyan] Save to SQLite saved_results")
    console.print("[cyan]4.[/cyan] Cancel")

    choice = input(": > ").strip()

    try:
        if choice == "1":
            file_path = export_service.save_result_to_text(
                current_user,
                current_result["result_type"],
                current_result["title"],
                current_result["content"],
                save_source="CLI Preview",
            )
            print_successmsg(f"Text export saved to {file_path}.")

        elif choice == "2":
            file_path = export_service.save_result_to_csv(
                current_user,
                current_result["result_type"],
                current_result["title"],
                current_result["content"],
                df=current_result["df"],
                save_source="CLI Preview",
            )
            print_successmsg(f"CSV export saved to {file_path}.")

        elif choice == "3":
            saved_id = export_service.save_result_to_database(
                conn,
                current_user,
                current_result["result_type"],
                current_result["title"],
                current_result["content"],
                save_source="CLI Preview",
            )
            print_successmsg(f"Preview saved to SQLite with ID {saved_id}.")

        elif choice == "4":
            print_warningmsg("Export cancelled.")

        else:
            print_errormsg("Invalid choice. Please enter 1, 2, 3, or 4.")

    except sqlite3.Error:
        print_errormsg("The preview could not be saved to SQLite.")
    except OSError:
        print_errormsg("The preview could not be saved to a file.")
    except ValueError as error:
        print_errormsg(str(error))


def main():
    """Check if Rich is installed and display the Menu if it is."""
    if not RICH_AVAILABLE:
        print("Please install Rich using: pip install rich")
        return

    console.print(
        Panel(
            "[white]Secure multi-domain intelligence and account management CLI[/white]",
            title="[bold cyan]Welcome to Gatekeeper[/bold cyan]",
            border_style="cyan",
        )
    )

    conn = db.get_connection()
    schema.create_user_table(conn)
    ensure_role_column(conn)

    current_user = None
    current_role = None
    current_result = None

    while True:
        display_main_menu(current_user, current_role)
        choice = console.input("[bold cyan]Select an option: [/bold cyan]").strip()

        if choice == "1":
            register_user(conn)

        elif choice == "2":
            if current_user is not None:
                print_warningmsg(f"You are already logged in as {current_user}.")
                print_infomsg("Please log out before logging in as another user.")
            else:
                logged_in_user = login_user(conn)

                if logged_in_user is not None:
                    current_user = logged_in_user
                    current_role = get_user_role(conn, current_user)
                    current_result = None
                    print_successmsg(f"Login successful! Role: {current_role}")
                else:
                    print_errormsg("Incorrect username or password.")

        elif choice == "3":
            display_all_users(conn, current_role)

        elif choice == "4":
            current_user = update_username(conn, current_user, current_role)

        elif choice == "5":
            deleted_username = delete_user(conn, current_role)

            if deleted_username is not None and deleted_username == current_user:
                current_user = None
                current_role = None
                current_result = None
                print_warningmsg("Your account was deleted, so you have been logged out.")

        elif choice == "6":
            migrate_csv_data(conn, current_role)

        elif choice == "7":
            if current_user is None:
                print_warningmsg("Please log in before previewing migrated data.")
            else:
                preview_result = preview_migrated_data(conn)
                if preview_result is not None:
                    current_result = preview_result

        elif choice == "8":
            print_successmsg("Goodbye!")
            conn.close()
            break

        elif choice == "9":
            if current_user is None:
                print_warningmsg("No user is currently logged in.")
            else:
                confirmation = input(
                    "Are you sure you want to log out? yes/no: > "
                ).strip().lower()

                if confirmation == "yes":
                    print_successmsg(f"{current_user} has been logged out.")
                    current_user = None
                    current_role = None
                    current_result = None
                else:
                    print_warningmsg("Log out cancelled.")

        elif choice == "10":
            setup_admin_account(conn, current_role)

        elif choice == "11":
            change_password(conn, current_user)

        elif choice == "12":
            export_last_preview(conn, current_user, current_result)

        else:
            print_errormsg("Invalid choice. Please enter a number from 1 to 12.")


if __name__ == "__main__":
    main()
