import pathlib

import pytest

import lazyflow
from lazyflow.graph import Graph
from lazyflow.operator import format_operator_stack


@pytest.fixture(scope="module")
def disabled_cache_manager():
    """
    Some tests rely on cache being persistent. On smaller machines it can
    happen that cache is cleaned up during a test. By disabling the automatic
    cleanup we ensure reproducible cache hits.
    """
    cache_manager = lazyflow.operators.cacheMemoryManager._cache_memory_manager
    cache_manager.disable()
    yield cache_manager
    cache_manager.enable()


@pytest.fixture(scope="function", autouse=True)
def ensure_clean_cache(disabled_cache_manager):
    """Clean cache before after test"""
    yield
    disabled_cache_manager._cleanup()


@pytest.hookimpl()
def pytest_exception_interact(node, call, report):
    if call.excinfo:
        stack = format_operator_stack(call.excinfo.value)
        if stack:
            formatted_stack = "".join(stack)
            report.sections.append(("Operator Stack", formatted_stack))


@pytest.hookimpl()
def pytest_runtest_setup(item):
    # pytest-qt changes exception handling so to avoid test failures in exception handling tests
    # we need to mark all tests with qt_no_exception_capture mark
    # See: https://pytest-qt.readthedocs.io/en/latest/virtual_methods.html#disabling-the-automatic-exception-hook
    item.add_marker("qt_no_exception_capture")


@pytest.fixture
def graph():
    return Graph()


@pytest.fixture
def inputdata_dir():
    basepath = pathlib.Path(__file__).parent
    return str(basepath / "data" / "inputdata")
