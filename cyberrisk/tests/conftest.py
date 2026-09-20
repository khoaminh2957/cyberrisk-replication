import os, sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def pytest_addoption(parser):
    parser.addoption("--run-network", action="store_true", help="run tests that hit SEC EDGAR / Google Trends")


def pytest_configure(config):
    config.addinivalue_line("markers", "network: needs the internet")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-network"):
        return
    skip = pytest.mark.skip(reason="needs --run-network")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)
