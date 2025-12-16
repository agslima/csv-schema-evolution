"""
Protect against CSV Injection:
"""


def sanitize_cell_value(value: str) -> str:
    """
    Prevents CSV Injection (Formula Injection).

    If a field starts with strictly forbidden characters (=, +, -, @),
    it prefixes the value with a single quote to force it as text.

    Args:
        value (str): The raw string from the CSV cell.

    Returns:
        str: The sanitized string.
    """
    if not value:
        return ""

    # 1. Trim Whitespace (The "Cleaning" part)
    clean_value = value.strip()

    # 2. Security Check (The "Protection" part)
    # If a field starts with strictly forbidden characters, prefix with single quote
    if clean_value.startswith(("=", "+", "-", "@")):
        return f"'{clean_value}"

    return clean_value
