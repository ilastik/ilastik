import shutil
import zipfile
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def sample_projects_dir(tmp_path_factory) -> Path:
    tmp_path = tmp_path_factory.mktemp("test_projects")
    test_data_path = Path(__file__).parent.parent / "data"
    sample_projects_zip_path = test_data_path / "test_projects.zip"
    sample_data_dir_path = test_data_path / "inputdata"

    projects_archive = zipfile.ZipFile(sample_projects_zip_path, mode="r")
    projects_archive.extractall(path=tmp_path)

    shutil.copytree(sample_data_dir_path, tmp_path / "inputdata")

    return tmp_path


@pytest.fixture
def pixel_classification_ilp_2d3c(sample_projects_dir: Path) -> Path:
    return sample_projects_dir / "PixelClassification2d3c.ilp"


@pytest.fixture
def object_classification_from_predictions_ilp_2d3c(sample_projects_dir: Path) -> Path:
    return sample_projects_dir / "ObjectClassification2d3c_wPred.ilp"


@pytest.fixture
def object_classification_from_labels_ilp_2d3c(sample_projects_dir: Path) -> Path:
    return sample_projects_dir / "ObjectClassification2d3c_wLabels.ilp"


@pytest.fixture
def multicut_ilp_3d1c(sample_projects_dir: Path) -> Path:
    return sample_projects_dir / "Boundary-basedSegmentationwMulticut3d1c.ilp"
