"""A passing pytest subset or opt-out must not satisfy consumer acceptance."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_consumer_results.py"
spec = importlib.util.spec_from_file_location("check_consumer_results", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def reports(tmp_path, names=("prepare", "read"), status=None):
    expected = tmp_path / "expected.json"
    expected.write_text(json.dumps(["contracts::prepare", "contracts::read"]))
    root = ET.Element("testsuites")
    suite = ET.SubElement(root, "testsuite")
    for name in names:
        case = ET.SubElement(suite, "testcase", classname="contracts", name=name)
        if status:
            ET.SubElement(case, status)
    report = tmp_path / "result.xml"
    ET.ElementTree(root).write(report)
    return report, expected


def test_complete_successful_cases_are_accepted(tmp_path):
    report, expected = reports(tmp_path)
    assert checker.verify_results(report, expected) == ["contracts::prepare", "contracts::read"]


@pytest.mark.parametrize("names", [(), ("prepare",), ("prepare", "read", "read"),
                                     ("prepare", "read", "unreviewed")])
def test_empty_partial_duplicate_or_unreviewed_cases_fail(tmp_path, names):
    report, expected = reports(tmp_path, names)
    with pytest.raises(ValueError, match="case mismatch"):
        checker.verify_results(report, expected)


@pytest.mark.parametrize("status", ["skipped", "failure", "error"])
def test_required_cases_must_execute_and_pass(tmp_path, status):
    report, expected = reports(tmp_path, status=status)
    with pytest.raises(ValueError, match="did not pass"):
        checker.verify_results(report, expected)


@pytest.mark.parametrize("expected_cases", [[], ["same", "same"], [1], {}])
def test_invalid_expected_case_manifest_fails(tmp_path, expected_cases):
    report, expected = reports(tmp_path)
    expected.write_text(json.dumps(expected_cases))
    with pytest.raises(ValueError, match="nonempty unique"):
        checker.verify_results(report, expected)


def test_cli_rejects_a_successful_but_reduced_pytest_report(tmp_path):
    report, expected = reports(tmp_path, names=("prepare",))
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--junit", str(report), "--expected", str(expected)],
        text=True, capture_output=True,
    )
    assert result.returncode == 1
    assert "contracts::read" in result.stderr


def test_suite_error_outside_cases_is_not_hidden(tmp_path):
    report, expected = reports(tmp_path)
    tree = ET.parse(report)
    ET.SubElement(tree.getroot(), "error", message="collection failed")
    tree.write(report)
    with pytest.raises(ValueError, match="contains an error"):
        checker.verify_results(report, expected)
