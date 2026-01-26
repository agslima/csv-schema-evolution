"""
Dialect Detector Service.
"""

import csv
import re
from collections import Counter
from io import StringIO
from typing import List, Tuple, Pattern


class DialectDetector:
    """
    Implements the Data Consistency Measure for CSV Dialect Detection.
    Source: 'Wrangling Messy CSV Files by Detecting Row and Type Patterns' (2018)
    """

    # pylint: disable=too-few-public-methods

    # Constants from the paper
    ALPHA = 1e-3  # Constant to handle single-column files
    BETA = 1e-10  # Minimum Type Score to avoid zeroing out valid patterns

    # Type Inference Regex Patterns (Simplified from Appendix A)
    # Note: Order matters (check specific formats before general ones)
    TYPE_PATTERNS: List[Pattern] = [
        re.compile(r"^\s*$"),  # Empty
        re.compile(r"^-?\d+$"),  # Integer
        re.compile(r"^-?\d+[.,]\d+(e[+-]?\d+)?$"),  # Float/Scientific
        re.compile(r"^(http|https)://[^\s/$.?#].[^\s]*$"),  # URL
        re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"),  # Email
        re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?$"),  # ISO Date/Time
        re.compile(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$"),  # Common Date
        re.compile(r"^[Nn]/?[Aa]$"),  # N/A
        re.compile(r"^[A-Za-z0-9\s\-_]+$"),  # Alphanumeric
    ]

    def __init__(self, sample_size: int = 8192):
        self.sample_size = sample_size

    def detect(self, content: str) -> csv.Dialect:
        """
        Search the space of dialects for the one maximizing Consistency Q(x, theta).
        Q = Pattern_Score * Type_Score
        """
        sample = content[: self.sample_size]
        candidates = self._get_potential_dialects()

        best_dialect = None
        best_score = -1.0

        for delimiter, quotechar in candidates:
            # pylint: disable=broad-except
            try:
                rows = self._parse_sample(sample, delimiter, quotechar)
                if not rows:
                    continue

                # Calculate components
                p_score = self._calculate_pattern_score(rows)
                t_score = self._calculate_type_score(rows)

                # Q(x, theta) = P(x, theta) * T(x, theta)
                consistency_score = p_score * t_score

                if consistency_score > best_score:
                    best_score = consistency_score
                    best_dialect = (delimiter, quotechar)
            except Exception:
                continue

        # Fallback to standard Excel dialect if nothing works
        if not best_dialect:
            return csv.get_dialect("excel")

        # Register and return the detected dialect
        dialect_name = f"auto_{ord(best_dialect[0])}_{ord(best_dialect[1])}"
        try:
            csv.register_dialect(
                dialect_name, delimiter=best_dialect[0], quotechar=best_dialect[1]
            )
        except csv.Error:
            pass  # Already registered

        return csv.get_dialect(dialect_name)

    def _get_potential_dialects(self) -> List[Tuple[str, str]]:
        """
        Construct potential dialects (Theta_x).
        The paper suggests filtering this list, but use a fixed common set for efficiency.
        """
        delimiters = [",", ";", "\t", "|"]
        quotechars = ['"', "'"]
        candidates = []
        for delimiter in delimiters:
            for quotechar in quotechars:
                candidates.append((delimiter, quotechar))
        return candidates

    def _parse_sample(
        self, sample: str, delimiter: str, quotechar: str
    ) -> List[List[str]]:
        sample_io = StringIO(sample)
        try:
            # Use strict=True to fail fast on bad parsing (e.g. unclosed quotes)
            reader = csv.reader(
                sample_io, delimiter=delimiter, quotechar=quotechar, strict=True
            )
            return list(reader)
        except csv.Error:
            return []

    def _calculate_pattern_score(self, rows: List[List[str]]) -> float:
        """
        Calculates P(x, theta).
        P = (1/K) * Sum( N_k * (L_k - 1) / L_k )
        """
        if not rows:
            return 0.0

        lengths = [len(r) for r in rows]
        pattern_counts = Counter(lengths)

        # K: Number of distinct row patterns
        num_patterns = len(pattern_counts)
        total_score = 0.0

        for length, count in pattern_counts.items():
            # Handle single-column files using Alpha constant
            # Numerator is max(alpha, L_k - 1)
            numerator = max(self.ALPHA, length - 1)

            # Term is (L_k - 1) / L_k
            score_k = numerator / length
            total_score += count * score_k

        return (1 / num_patterns) * total_score

    def _calculate_type_score(self, rows: List[List[str]]) -> float:
        """
        Calculates T(x, theta).
        T = (1/M) * Sum( I[type(cell) in KnownTypes] )
        """
        total_cells = sum(len(r) for r in rows)
        if total_cells == 0:
            return self.BETA

        matched_cells = 0
        for row in rows:
            for cell in row:
                cell_val = cell.strip()
                # Check against known types
                if any(regex.match(cell_val) for regex in self.TYPE_PATTERNS):
                    matched_cells += 1

        score = matched_cells / total_cells
        # Use Beta to avoid zeroing out valid pattern scores
        return max(self.BETA, score)
