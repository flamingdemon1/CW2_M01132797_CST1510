"""Shared password validation and strength display helpers."""

import streamlit as st


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

    label, score, colour, feedback = get_password_strength(password)

    st.markdown(
        f"""
        <div style="max-width: 520px; margin-top: 0.25rem;
                    margin-bottom: 0.25rem;">
            <div style="display: flex; align-items: baseline; gap: 0.6rem;">
                <strong>Password strength: {label}</strong>
                <span style="color: {colour}; font-size: 0.9rem;">{score}%</span>
            </div>
            <div style="background-color: #1E293B; height: 10px;
                        border-radius: 5px; overflow: hidden; margin-top: 6px;">
                <div style="background-color: {colour}; width: {score}%;
                            height: 10px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(feedback)
