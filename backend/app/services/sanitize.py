"""
    Protect against CSV Injection:
"""


def sanitize_value(value: str) -> str:
    """
    Protect against CSV Injection:
    If a field starts with '=', '+', '-', '@' → prefix with a single quote
    """
    if value and value[0] in ("=", "+", "-", "@"):
        return "'" + value
    return value
