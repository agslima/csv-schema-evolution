#!/usr/bin/env python3
"""
Simple test runner for csv_schema_evolution project.
Runs basic tests without pytest to avoid async/DB connectivity issues.
"""

import sys
import os

# Add parent directory (backend/) to path so 'app' module can be imported
# pylint: disable=no-member
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# pylint: disable=wrong-import-position
# FIX E0611: Use the correct function name 'sanitize_cell_value'
from app.utils.sanitize import sanitize_cell_value  # noqa: E402
from app.utils.validators import MAX_FILE_SIZE  # noqa: E402


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
        # Update function call
        result = sanitize_cell_value(input_val)
        if result != expected:
            failed.append(
                f"  FAIL: sanitize_cell_value({repr(input_val)}) = {repr(result)}, "
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
        # Update function call
        result = sanitize_cell_value(input_val)
        if result != expected:
            failed.append(
                f"  FAIL: sanitize_cell_value({repr(input_val)}) = {repr(result)}, "
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
    print("=" * 60)
    print()

    tests = [
        test_sanitize_injection_prevention,
        test_sanitize_edge_cases,
        test_validators,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        # pylint: disable=broad-except
        except Exception as error:
            print(f"❌ {test_func.__name__} ERROR: {error}")
            results.append(False)
        print()

    # Summary
    passed = sum(results)
    total = len(results)
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
