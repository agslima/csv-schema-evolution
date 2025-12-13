"""
Unit tests for the sanitize service.
Ensures CSV Injection protection works correctly.
"""

import sys
import os

# pylint: disable=no-member
# Add project root to path to ensure 'app' module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# pylint: enable=no-member

# pylint: disable=wrong-import-position
from app.utils.sanitize import sanitize_cell_value


def test_sanitize_standard_prefixes():
    """
    Test CSV injection prevention for standard dangerous prefixes.
    Any field starting with =, +, -, @ must be escaped.
    """
    assert sanitize_cell_value("=CMD") == "'=CMD"
    assert sanitize_cell_value("+SUM") == "'+SUM"
    assert sanitize_cell_value("-SYSTEM") == "'-SYSTEM"
    assert sanitize_cell_value("@IMPORT") == "'@IMPORT"


def test_sanitize_safe_values():
    """Test that safe values remain unchanged."""
    assert sanitize_cell_value("normal") == "normal"
    assert sanitize_cell_value("123") == "123"
    assert sanitize_cell_value("") == ""
    assert sanitize_cell_value("alice@example.com") == "alice@example.com"


def test_sanitize_edge_cases():
    """Test sanitization with specific edge cases."""
    # Single character dangerous prefix
    assert sanitize_cell_value("=") == "'="
    assert sanitize_cell_value("+") == "'+"

    # Dangerous character in the middle (safe, should not be sanitized)
    assert sanitize_cell_value("text=value") == "text=value"
    assert sanitize_cell_value("1+1") == "1+1"

    # Multiple characters of the same dangerous prefix
    assert sanitize_cell_value("===DANGER") == "'===DANGER"


def test_sanitize_handles_whitespace():
    """
    Test that leading whitespace DOES trigger sanitization.

    Explanation: Many spreadsheet tools ignore leading whitespace
    and still execute the formula. Therefore, "  =CMD" is dangerous
    and must be sanitized to "'  =CMD".
    """
    # The previous test expected this to be ignored,
    # but our robust implementation uses .strip() check.
    assert sanitize_cell_value(" =CMD") == "' =CMD"
    assert sanitize_cell_value("\t+SUM") == "'\t+SUM"

    # Trailing whitespace does not matter for the trigger,
    # but the value should be preserved.
    assert sanitize_cell_value("=CMD   ") == "'=CMD   "
