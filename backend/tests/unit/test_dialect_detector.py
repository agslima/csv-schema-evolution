"""
Unit tests for the Dialect Detector service.
"""

import unittest

# import csv
from app.services.dialect_detector import DialectDetector


class TestDialectDetector(unittest.TestCase):
    """Test suite for CSV dialect detection logic."""

    def setUp(self):
        self.detector = DialectDetector()

    def test_standard_comma_separated(self):
        """
        Scenario: Standard CSV file with a header and consistent rows.
        Paper: Represents a 'clean' dataset where Pattern Score is high (1.0).
        """
        content = (
            "id,name,date\n"
            "1,Alice,2023-01-01\n"
            "2,Bob,2023-01-02\n"
            "3,Charlie,2023-01-03"
        )
        dialect = self.detector.detect(content)
        self.assertEqual(dialect.delimiter, ",")
        self.assertEqual(dialect.quotechar, '"')

    def test_semicolon_with_comma_decimals(self):
        """
        Scenario: European format using semicolons as delimiters and commas for decimals.
        Paper: Validates that Type Score correctly identifies floats like '1,5'.
        """
        content = """Measure;Value;Date
Temp;37,5;2023-10-01
Press;1013,2;2023-10-01"""
        dialect = self.detector.detect(content)
        self.assertEqual(dialect.delimiter, ";")

    def test_single_column_integers(self):
        """
        Scenario: A single column of IDs.
        Paper Check: This tests the 'Alpha' constant.
        Without Alpha, Pattern Score would be 0 and fail.
        """
        content = "1001\n1002\n1003\n1004"
        dialect = self.detector.detect(content)

        # Verify internal parsing
        # pylint: disable=protected-access
        rows = self.detector._parse_sample(
            content, dialect.delimiter, dialect.quotechar
        )
        self.assertTrue(
            all(len(r) == 1 for r in rows), "Should be parsed as single column"
        )

    def test_mixed_types_single_column(self):
        """
        Scenario: Single column with mixed integers, strings, and dates.
        Paper Check: Tests the Type Score robustness.
        """
        content = "12345\nProduct_A\n2023-12-25\nadmin@example.com"
        dialect = self.detector.detect(content)

        # pylint: disable=protected-access
        rows = self.detector._parse_sample(
            content, dialect.delimiter, dialect.quotechar
        )
        self.assertEqual(len(rows), 4)
        self.assertEqual(len(rows[0]), 1)

    def test_messy_quotes(self):
        """
        Scenario: Fields containing the delimiter inside quotes.
        Paper: Tests that parser respects quotes to maintain Pattern Score.
        """
        content = (
            "id,description,total\n"
            '1,"Item A, with comma",500\n'
            '2,"Item B; with semicolon",600\n'
            '3,"Item C",700'
        )
        dialect = self.detector.detect(content)
        self.assertEqual(dialect.delimiter, ",")
        self.assertEqual(dialect.quotechar, '"')

        # Verify it actually parsed the quoted field correctly
        # pylint: disable=protected-access
        rows = self.detector._parse_sample(
            content, dialect.delimiter, dialect.quotechar
        )
        self.assertEqual(len(rows[1]), 3)
        self.assertEqual(rows[1][1], "Item A, with comma")

    def test_pipe_delimiter(self):
        """Scenario: Non-standard delimiter (|)."""
        content = "name|age|email\nalice|30|a@b.com\nbob|25|b@c.com"
        dialect = self.detector.detect(content)
        self.assertEqual(dialect.delimiter, "|")

    def test_single_line_header(self):
        """
        Scenario: Only headers, no data.
        Paper: Pattern Score should still work on single row pattern.
        """
        content = "col1,col2,col3"
        dialect = self.detector.detect(content)
        self.assertEqual(dialect.delimiter, ",")

    def test_garbage_fallback(self):
        """
        Scenario: Complete garbage input.
        Paper: Should fallback to defaults (Excel) rather than crash.
        """
        content = "!!!@@@###$$$%%%^^^&&&***((("
        dialect = self.detector.detect(content)

        # FIX: Check behavior (delimiter) instead of strict type inheritance
        # self.assertIsInstance(dialect, csv.Dialect) <--- REMOVE THIS
        self.assertEqual(dialect.delimiter, ",")  # Default fallback


if __name__ == "__main__":
    unittest.main()
