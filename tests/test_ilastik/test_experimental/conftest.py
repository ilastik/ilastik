from zipfile import ZipFile

import pytest

from . import types


@pytest.fixture(scope="session")
def test_data_lookup(data_path, tmpdir_factory) -> types.ApiTestDataLookup:
    unpacking_dir = tmpdir_factory.mktemp("api_projects")

    projects_zip = data_path / "api_projects.zip"
    with ZipFile(projects_zip) as zip:
        zip.extractall(unpacking_dir)

        known_filenames = set(e.value for e in types.TestData)

        path_by_name = {}
        for name in zip.namelist():
            if name not in known_filenames:
                raise ValueError(
                    f"Unknown file {name} in api_projects.zip. Add entry to ApiTestData or remove it from zip"
                )

            path_by_name[name] = str(unpacking_dir / name)

        return types.ApiTestDataLookup(path_by_name)
