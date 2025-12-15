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
    if value and value.strip().startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value
