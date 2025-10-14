"""Password complexity validation helpers."""

import string
from typing import Optional

# Define the standard error message once so controllers can reuse it consistently.
WEAK_PASSWORD_MESSAGE = (
    "Password too weak — must be at least 8 characters, include a number and symbol."
)


def validate_password_strength(password: str) -> Optional[str]:
    """Return an error message when a password fails basic complexity checks."""
    if not password:
        return WEAK_PASSWORD_MESSAGE

    if len(password) < 8:
        return WEAK_PASSWORD_MESSAGE


    has_digit = any(char.isdigit() for char in password)
    symbols = set(string.punctuation)
    has_symbol = any(char in symbols for char in password)

    if not (has_digit and has_symbol):
        return WEAK_PASSWORD_MESSAGE


    return None
