"""Reject incomplete or unsuccessful plugin-owned consumer test reports."""

import argparse
from collections import Counter
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def verify_results(report: Path, expected_file: Path) -> list[str]:
    expected = json.loads(expected_file.read_text())
    if not isinstance(expected, list) or not expected or not all(
        isinstance(name, str) and name for name in expected
    ) or len(expected) != len(set(expected)):
        raise ValueError("Expected consumer cases must be a nonempty unique string list")
    root = ET.parse(report).getroot()
    cases = list(root.iter("testcase"))
    actual = [f"{case.get('classname')}::{case.get('name')}" for case in cases]
    if Counter(actual) != Counter(expected):
        missing = sorted((Counter(expected) - Counter(actual)).elements())
        unexpected = sorted((Counter(actual) - Counter(expected)).elements())
        raise ValueError(f"Consumer case mismatch: missing={missing}, unexpected={unexpected}")
    unsuccessful = [
        name for name, case in zip(actual, cases)
        if any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))
    ]
    if unsuccessful:
        raise ValueError(f"Required consumer cases did not pass: {unsuccessful}")
    # Collection errors can be represented outside ordinary testcase nodes.
    if next(root.iter("error"), None) is not None or next(root.iter("failure"), None) is not None:
        raise ValueError("Consumer report contains an error or failure")
    return actual


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    args = parser.parse_args()
    try:
        cases = verify_results(args.junit, args.expected)
    except (ValueError, OSError, ET.ParseError) as exc:
        parser.exit(1, f"Consumer acceptance failed: {exc}\n")
    print(f"All {len(cases)} required consumer cases passed")


if __name__ == "__main__":
    main()
