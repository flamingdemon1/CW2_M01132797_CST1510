import bcrypt
from pathlib import Path
from getpass import getpass


# Store the users file inside the DATA folder
DATA_FOLDER = Path("DATA")
USERS_FILE = DATA_FOLDER / "users.txt"


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


def load_users():
    """Read all users from the users.txt file."""
    users = {}

    # If the file does not exist yet, return an empty dictionary
    if not USERS_FILE.exists():
        return users

    with open(USERS_FILE, "r") as file:
        for line in file:
            # Skip empty lines
            if line.strip() == "":
                continue

            username, password_hash = line.strip().split(",", 1)
            users[username] = password_hash

    return users


def register_user():
    """Register a new user and store their hashed password."""
    username = input("Enter your username: > ").strip()
   
    users = load_users()

    if username == "":
        print("Username cannot be empty!")
        return

    if username in users:
        print("This username already exists. Please choose another one.")
        return
    
    password = getpass("Enter your password: > ")
    hashed_password = generate_hash(password)

    # Make sure the DATA folder exists
    DATA_FOLDER.mkdir(exist_ok=True)

    with open(USERS_FILE, "a") as file:
        file.write(f"{username},{hashed_password}\n")

    print("User successfully registered!")


def login_user():
    """Check whether a username and password are correct."""
    username = input("Enter your username: > ").strip()
    password = getpass("Enter your password: > ")

    users = load_users()

    if username not in users:
        return False

    stored_hash = users[username]

    return is_valid_hash(password, stored_hash)


def main():
    """Display the menu and allow the user to register, log in, or exit."""
    while True:
        print("\n1. Register")
        print("2. Log in")
        print("3. Exit")

        choice = input(": > ").strip()

        if choice == "1":
            register_user()

        elif choice == "2":
            if login_user():
                print("Login successful!")
            else:
                print("Incorrect username or password.")

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()