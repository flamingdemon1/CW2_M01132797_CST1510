"""Shared password validation and strength display helpers."""

import streamlit as st


def is_valid_email(email):
    """Return True when an email has a simple valid address structure."""
    email = email.strip()

    if email.count("@") != 1 or " " in email:
        return False

    local_part, domain = email.split("@")

    if not local_part or not domain or "." not in domain:
        return False

    if domain.startswith(".") or domain.endswith("."):
        return False

    return True


def get_password_errors(password):
    """Return a list of password requirements that are not satisfied."""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")

    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one number.")

    if not any(not char.isalnum() for char in password):
        errors.append("Password must contain at least one symbol.")

    return errors


def get_password_strength(password):
    """Return a display label, score, colour, and feedback for a password."""
    score = 0
    missing_requirements = []

    if len(password) >= 8:
        score += 20
    else:
        missing_requirements.append("at least 8 characters")

    if any(char.isupper() for char in password):
        score += 15
    else:
        missing_requirements.append("uppercase letter")

    if any(char.islower() for char in password):
        score += 15

    if any(char.isdigit() for char in password):
        score += 15
    else:
        missing_requirements.append("number")

    if any(not char.isalnum() for char in password):
        score += 20
    else:
        missing_requirements.append("symbol")

    if len(password) >= 12:
        score += 15

    if score <= 20:
        label, colour = "Very weak", "#8B0000"
    elif score <= 40:
        label, colour = "Weak", "#E57373"
    elif score <= 60:
        label, colour = "Medium", "#F9A825"
    elif score <= 80:
        label, colour = "Strong", "#81C784"
    else:
        label, colour = "Very strong", "#1B5E20"

    if missing_requirements:
        feedback = "Missing: " + ", ".join(missing_requirements) + "."
    elif len(password) < 12:
        feedback = (
            "Good password. Use 12 or more characters for an even stronger "
            "password."
        )
    elif not any(char.islower() for char in password):
        feedback = "Good password. Add a lowercase letter for extra strength."
    else:
        feedback = "Excellent password. All recommended checks are passed."

    return label, score, colour, feedback


def display_password_strength(password):
    """Display the shared coloured strength bar and password feedback."""
    if password == "":
        st.caption("Start typing a password to see its strength.")
        return

    label, score, _colour, feedback = get_password_strength(password)

    # A native Streamlit progress bar reruns naturally when the input changes.
    st.progress(score, text=f"Password strength: {label} ({score}%)")
    st.caption(feedback)
