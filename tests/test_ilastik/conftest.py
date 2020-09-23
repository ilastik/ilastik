import pathlib

import pytest

@pytest.fixture(scope="session")
def data_path():
    conf_path = pathlib.Path(__file__).parent
    return conf_path / "data"

