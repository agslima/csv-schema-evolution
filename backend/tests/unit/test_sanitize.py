import pytest
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# Direct test of sanitize module (no app imports needed)
def test_sanitize_value():
    """Test CSV injection prevention for dangerous prefixes."""
    from app.services.sanitize import sanitize_value

    assert sanitize_value("=CMD") == "'=CMD"
    assert sanitize_value("+SUM") == "'+SUM"
    assert sanitize_value("-SYSTEM") == "'-SYSTEM"
    assert sanitize_value("@IMPORT") == "'@IMPORT"
    assert sanitize_value("normal") == "normal"
    assert sanitize_value("") == ""
    assert sanitize_value("123") == "123"


def test_sanitize_value_edge_cases():
    """Test sanitize with edge cases."""
    from app.services.sanitize import sanitize_value

    # Single character dangerous prefix
    assert sanitize_value("=") == "'="
    # Dangerous prefix in middle (should not be sanitized)
    assert sanitize_value("text=value") == "text=value"
    # Multiple characters of same dangerous prefix
    assert sanitize_value("===DANGER") == "'===DANGER"


def test_sanitize_does_not_affect_whitespace():
    """Test that sanitize doesn't affect leading whitespace."""
    from app.services.sanitize import sanitize_value

    # Note: spaces don't trigger sanitization
    assert sanitize_value(" =FORMULA") == " =FORMULA"
    assert sanitize_value("a=FORMULA") == "a=FORMULA"
