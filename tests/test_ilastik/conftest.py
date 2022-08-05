import pathlib

import pytest

import importlib
import sys


@pytest.fixture(scope="session")
def data_path():
    conf_path = pathlib.Path(__file__).parent
    return conf_path / "data"


def pytest_addoption(parser):
    parser.addoption("--tiktorch_executable", help="tiktorch executable to use for integration tests")


@pytest.fixture
def tiktorch_exe_from_env():
    TIKTORCH_MODULES = ("tiktorch", "tiktorch.server", "torch")
    if all(importlib.util.find_spec(mod) for mod in TIKTORCH_MODULES):
        tiktorch_executable = [sys.executable, "-m", "tiktorch.server"]
    else:
        tiktorch_executable = None

    return tiktorch_executable


@pytest.fixture
def tiktorch_executable_path(request, tiktorch_exe_from_env):
    tiktorch_exe_path = request.config.getoption("--tiktorch_executable", None) or tiktorch_exe_from_env
    if not tiktorch_exe_path:
        pytest.skip("need --tiktorch_executable option to run")

    return tiktorch_exe_path
