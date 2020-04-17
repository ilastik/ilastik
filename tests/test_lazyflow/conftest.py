import os

import pytest
import pathlib

from lazyflow.operator import format_operator_stack
from lazyflow.graph import Graph


@pytest.hookimpl()
def pytest_exception_interact(node, call, report):
    if call.excinfo:
        stack = format_operator_stack(call.excinfo.tb)
        if stack:
            formatted_stack = "".join(stack)
            report.sections.append(("Operator Stack", formatted_stack))


@pytest.hookimpl()
def pytest_runtest_setup(item):
    # pytest-qt changes exception handling so to avoid test failures in exception handling tests
    # we need to mark all tests with qt_no_exception_capture mark
    # See: https://pytest-qt.readthedocs.io/en/latest/virtual_methods.html#disabling-the-automatic-exception-hook
    item.add_marker("qt_no_exception_capture")


@pytest.fixture(scope="session")
def inputdata_dir():
    conftest_dir = os.path.dirname(__file__)
    return os.path.join(conftest_dir, "data", "inputdata")


@pytest.fixture
def graph():
    return Graph()


@pytest.fixture
def inputdata_dir():
    basepath = pathlib.Path(__file__).parent
    return str(basepath / "data" / "inputdata")
