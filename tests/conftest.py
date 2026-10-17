"""Keep engine execution explicitly opt-in."""

import os
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-engine", action="store_true", default=False)
    parser.addoption("--run-consumers", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):
    tests_root = Path(__file__).resolve().parent
    for item in items:
        path = Path(item.path).resolve()
        parts = path.relative_to(tests_root).parts if path.is_relative_to(tests_root) else ()
        if parts and parts[0] == "consumers":
            item.add_marker(pytest.mark.consumer)
        if parts and parts[0] == "integration":
            item.add_marker(pytest.mark.engine)
        if item.get_closest_marker("consumer") is not None:
            if not config.getoption("--run-consumers"):
                item.add_marker(pytest.mark.skip(reason="requires --run-consumers"))
        if item.get_closest_marker("engine") is not None:
            if not config.getoption("--run-engine"):
                item.add_marker(pytest.mark.skip(reason="requires --run-engine"))


def pytest_runtest_setup(item):
    if item.get_closest_marker("engine") is not None and item.config.getoption("--run-engine"):
        assets = os.environ.get("ABACUS_PP_ORB")
        if not assets or not Path(assets).expanduser().is_dir():
            pytest.fail("--run-engine requires ABACUS_PP_ORB asset directory", pytrace=False)
