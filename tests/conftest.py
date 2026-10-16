"""Keep engine execution explicitly opt-in."""

import os
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-engine", action="store_true", default=False)
    parser.addoption("--run-consumers", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "consumers" in Path(str(item.path)).parts:
            item.add_marker(pytest.mark.consumer)
            if not config.getoption("--run-consumers"):
                item.add_marker(pytest.mark.skip(reason="requires --run-consumers"))
        needs_engine = "integration" in Path(str(item.path)).parts or item.name in {
            "test_calculator_results", "test_restart",
        }
        if not needs_engine:
            continue
        item.add_marker(pytest.mark.engine)
        if not config.getoption("--run-engine"):
            item.add_marker(pytest.mark.skip(reason="requires --run-engine"))
        elif not Path(os.environ.get("ABACUS_PP_ORB", "missing-PP_ORB")).is_dir():
            raise pytest.UsageError("--run-engine requires ABACUS_PP_ORB asset directory")
