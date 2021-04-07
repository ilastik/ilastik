import pathlib

import pytest


@pytest.fixture(scope="session")
def data_path():
    conf_path = pathlib.Path(__file__).parent
    return conf_path / "data"


def pytest_addoption(parser):
    parser.addoption("--tiktorch_executable", help="tiktorch executable to use for integration tests")


@pytest.fixture
def tiktorch_executable_path(request):
    tiktorch_exe_path = request.config.getoption("--tiktorch_executable", None)
    if not tiktorch_exe_path:
        pytest.skip("need --tiktorch_executable option to run")

    return tiktorch_exe_path
