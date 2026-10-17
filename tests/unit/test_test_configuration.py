"""Exercise opt-in boundaries through real pytest collection and execution."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def probe_suite(tmp_path, monkeypatch):
    monkeypatch.delenv("ABACUS_PP_ORB", raising=False)

    def run(source, *args, location="unit", parent="checkout"):
        root = tmp_path / parent
        root.mkdir(exist_ok=True)
        test_dir = root / "tests"
        test_dir.mkdir(exist_ok=True)
        shutil.copyfile(Path(__file__).parents[1] / "conftest.py", test_dir / "conftest.py")
        shutil.copyfile(Path(__file__).parents[2] / "pyproject.toml", root / "pyproject.toml")
        target = test_dir / location
        target.mkdir(exist_ok=True)
        (target / "test_probe.py").write_text(source)
        env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
        env.pop("PYTEST_ADDOPTS", None)
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *args], cwd=root,
            env=env, capture_output=True, text=True, timeout=30,
        )

    return run


@pytest.mark.parametrize("marker", ["engine", "consumer"])
def test_explicit_markers_require_opt_in(probe_suite, marker):
    result = probe_suite(
        f"import pytest\n@pytest.mark.{marker}\ndef test_probe():\n"
        "    raise AssertionError('external work executed without opt-in')\n"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 skipped" in result.stdout


@pytest.mark.parametrize("parent", ["integration", "consumers"])
def test_checkout_directory_name_does_not_skip_offline_tests(probe_suite, parent):
    result = probe_suite("def test_probe():\n    pass\n", parent=parent)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


def test_test_name_does_not_make_offline_test_require_engine(probe_suite):
    result = probe_suite("def test_restart():\n    pass\n")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


@pytest.mark.parametrize("location", ["integration", "consumers"])
def test_external_directories_still_require_opt_in(probe_suite, location):
    result = probe_suite("def test_probe():\n    assert False\n", location=location)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 skipped" in result.stdout


def test_engine_opt_in_requires_supplied_assets(probe_suite):
    result = probe_suite(
        "import pytest\n@pytest.mark.engine\ndef test_probe():\n    pass\n",
        "--run-engine",
    )
    assert result.returncode != 0
    assert "ABACUS_PP_ORB" in result.stdout + result.stderr


def test_deselected_engine_tests_do_not_require_assets(probe_suite):
    result = probe_suite(
        "import pytest\n@pytest.mark.engine\ndef test_engine():\n    assert False\n"
        "def test_offline():\n    pass\n", "--run-engine", "-m", "not engine",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed, 1 deselected" in result.stdout


@pytest.mark.parametrize("marker, option", [("engine", "--run-engine"), ("consumer", "--run-consumers")])
def test_opt_in_executes_selected_tests(probe_suite, tmp_path, monkeypatch, marker, option):
    assets = tmp_path / "assets with spaces"
    assets.mkdir()
    monkeypatch.setenv("ABACUS_PP_ORB", str(assets))
    result = probe_suite(
        f"import pytest\n@pytest.mark.{marker}\ndef test_probe():\n    pass\n", option,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
