import pathlib
import sys
from unittest import mock

import h5py
import numpy
import pytest

from ilastik import app
from ilastik.workflows.neuralNetwork import LocalWorkflow


@pytest.fixture
def project_path() -> pathlib.Path:
    """local NN workflow created at 6b836bd112618c8ec6244c7330a711a383ef7a20"""
    tests_root = pathlib.Path(__file__).parents[2]
    project_path = tests_root / "data" / "inputdata" / "NNLocaBatch2d1c.ilp"
    return project_path


def load_h5_ds(fname, dataset):
    with h5py.File(fname, "r") as f:
        return f[dataset][()]


def test_nn_local_headless_prediction(project_path: pathlib.Path, data_path, tmp_path, tiktorch_executable_path):
    """use an ilastik project file with a simple model to test headless op

    Note: tiktorch_executable_path fixture used to ensure tiktorch can be started
    locally. Either it's in the env or provided to pytest via
    --tiktorch_executable

    """
    input_file = data_path / "inputdata" / "2d.h5"
    output_file = tmp_path / "output.h5"
    args = [
        "--headless",
        f"--project={project_path}",
        "--raw_data",
        f"{input_file}",
        "--input_axes",
        "yx",
        "--output_filename_format",
        f"{output_file}",
    ]
    # Clear the existing commandline args so it looks like we're starting fresh.
    sys.argv = ["ilastik.py"]
    sys.argv.extend(args)

    with mock.patch("ilastik.config.runtime_cfg.tiktorch_executable", new=tiktorch_executable_path):
        with mock.patch("ilastik.workflows.WORKFLOW_CLASSES", new=[LocalWorkflow]):
            parsed_args, workflow_cmdline_args = app.parse_known_args()

            shell = app.main(parsed_args=parsed_args, workflow_cmdline_args=workflow_cmdline_args, init_logging=False)

            shell.closeCurrentProject()

            # NN model does input * -1 + 1
            output_ref = load_h5_ds(input_file, "data")[..., numpy.newaxis] * -1 + 1
            output = load_h5_ds(output_file, "exported_data")
            numpy.testing.assert_array_almost_equal(output, output_ref)
