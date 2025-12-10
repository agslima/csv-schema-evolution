#!/usr/bin/env python3
"""
Simple test runner for csv_schema_evolution project.
Runs basic tests without pytest to avoid async/DB connectivity issues.
"""

import sys
import os

# Add backend directory to path
# pylint: disable=no-member
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# pylint: disable=wrong-import-position
from app.services.sanitize import sanitize_value
from app.utils.validators import MAX_FILE_SIZE


def test_sanitize_injection_prevention():
    """Test CSV injection prevention."""
    tests = [
        ("=CMD", "'=CMD"),
        ("+SUM", "'+SUM"),
        ("-SYSTEM", "'-SYSTEM"),
        ("@IMPORT", "'@IMPORT"),
        ("normal", "normal"),
        ("", ""),
        ("123", "123"),
        ("=", "'="),
        ("text=value", "text=value"),
        ("===DANGER", "'===DANGER"),
    ]

    failed = []
    for input_val, expected in tests:
        result = sanitize_value(input_val)
        if result != expected:
            failed.append(
                f"  FAIL: sanitize_value({repr(input_val)}) = {repr(result)}, "
                f"expected {repr(expected)}"
            )

    if failed:
        print("❌ test_sanitize_injection_prevention FAILED:")
        for msg in failed:
            print(msg)
        return False

    print("✅ test_sanitize_injection_prevention PASSED")
    return True


def test_sanitize_edge_cases():
    """Test sanitize with edge cases."""
    tests = [
        (" =FORMULA", " =FORMULA"),  # Space before doesn't trigger
        ("a=FORMULA", "a=FORMULA"),  # Letter before doesn't trigger
        ("  text", "  text"),  # Leading spaces
        ("123=456", "123=456"),  # Digit before
    ]

    failed = []
    for input_val, expected in tests:
        result = sanitize_value(input_val)
        if result != expected:
            failed.append(
                f"  FAIL: sanitize_value({repr(input_val)}) = {repr(result)}, "
                f"expected {repr(expected)}"
            )

    if failed:
        print("❌ test_sanitize_edge_cases FAILED:")
        for msg in failed:
            print(msg)
        return False

    print("✅ test_sanitize_edge_cases PASSED")
    return True


def test_validators():
    """Test validators module."""
    # Test MAX_FILE_SIZE constant
    expected_size = 50 * 1024 * 1024
    if MAX_FILE_SIZE != expected_size:
        print(
            f"❌ test_validators FAILED: MAX_FILE_SIZE = {MAX_FILE_SIZE}, "
            f"expected {expected_size}"
        )
        return False

    print("✅ test_validators PASSED (MAX_FILE_SIZE = 50 MB)")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("CSV Schema Evolution - Test Suite")
