import os

import pytest

from lazyflow.graph import Graph


@pytest.fixture(scope="session")
def inputdata_dir():
    conftest_dir = os.path.dirname(__file__)
    return os.path.join(conftest_dir, "data", "inputdata")


@pytest.fixture
def graph():
    return Graph()
