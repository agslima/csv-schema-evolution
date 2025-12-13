"""
Unit tests for the sanitize service.
"""

import sys
import os

# pylint: disable=no-member
# Add project root to path so 'app' module can be imported
# Path: tests/unit/ -> tests/ -> root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# pylint: enable=no-member


# pylint: disable=wrong-import-position
# FIX E0611: Use correct function name
from app.utils.sanitize import sanitize_cell_value  # noqa: E402


def test_sanitize_value():
    """Test CSV injection prevention for dangerous prefixes."""
    assert sanitize_cell_value("=CMD") == "'=CMD"
    assert sanitize_cell_value("+SUM") == "'+SUM"
    assert sanitize_cell_value("-SYSTEM") == "'-SYSTEM"
    assert sanitize_cell_value("@IMPORT") == "'@IMPORT"
    assert sanitize_cell_value("normal") == "normal"
    assert sanitize_cell_value("") == ""
    assert sanitize_cell_value("123") == "123"


def test_sanitize_value_edge_cases():
    """Test sanitize with edge cases."""
    # Single character dangerous prefix
    assert sanitize_cell_value("=") == "'="
    # Dangerous prefix in middle (should not be sanitized)
    assert sanitize_cell_value("text=value") == "text=value"
    # Multiple characters of same dangerous prefix
    assert sanitize_cell_value("===DANGER") == "'===DANGER"


def test_sanitize_does_not_affect_whitespace():
    """Test that sanitize doesn't affect leading whitespace."""
    # Note: spaces don't trigger sanitization
    assert sanitize_cell_value(" =FORMULA") == " =FORMULA"
    assert sanitize_cell_value("a=FORMULA") == "a=FORMULA"
