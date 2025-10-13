"""Password complexity validation helpers."""

import string
from typing import Optional

# Define the standard error message once so controllers can reuse it consistently.
WEAK_PASSWORD_MESSAGE = (
    "Password must be at least 10 characters long and include uppercase, lowercase, numbers, and symbols."
)


def validate_password_strength(password: str) -> Optional[str]:
    """Return an error message when a password fails basic complexity checks."""
    if password is None:
        return WEAK_PASSWORD_MESSAGE

    if len(password) < 10:
        return WEAK_PASSWORD_MESSAGE

    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_digit = any(char.isdigit() for char in password)
    symbols = set(string.punctuation)
    has_symbol = any(char in symbols for char in password)

    if not (has_upper and has_lower and has_digit and has_symbol):
        return WEAK_PASSWORD_MESSAGE

    return None