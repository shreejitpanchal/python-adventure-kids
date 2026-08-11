"""Exercise validation: checks behavior/output, not exact code formatting."""
from __future__ import annotations

import re
from typing import Optional

INPUT_PLACEHOLDER = "{input}"


def validate_output(
    actual_stdout: str,
    expected_output: str = "",
    input_value: Optional[str] = None,
    expected_output_pattern: Optional[str] = None,
) -> bool:
    """Compares output, optionally substituting what the child typed into a template.

    - expected_output_pattern (a regex) takes priority when set -- used for
      lessons involving randomness (games), where any of several outcomes is
      a valid, correctly-working program.
    - Otherwise expected_output can contain "{input}" as a placeholder for
      whatever the child entered, so any name/answer they try is accepted as
      long as their program echoes it back correctly.
    """
    actual = actual_stdout.strip()

    if expected_output_pattern:
        return re.fullmatch(expected_output_pattern, actual) is not None

    expected = expected_output
    if input_value is not None and INPUT_PLACEHOLDER in expected:
        expected = expected.replace(INPUT_PLACEHOLDER, input_value)
    return actual == expected.strip()
