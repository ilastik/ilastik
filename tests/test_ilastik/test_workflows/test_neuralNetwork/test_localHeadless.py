import pathlib
import sys
from unittest import mock

import h5py
import numpy
import pytest

from ilastik import app
from ilastik.workflows.neuralNetwork import LocalWorkflow


@pytest.fixture
def project_path_140b30v4() -> pathlib.Path:
    """local NN workflow created at 6b836bd112618c8ec6244c7330a711a383ef7a20

    on top of ilastik 1.4.0b30 with bioimage model spec version 0.4
    """
    tests_root = pathlib.Path(__file__).parents[2]
    project_path = tests_root / "data" / "inputdata" / "NNLocaBatch-140b30-biov04-2d1c.ilp"
    return project_path


@pytest.fixture
def project_path_141b22v5() -> pathlib.Path:
    """local NN workflow created at f64915831ab2747c3c32194eba36712121456234

    on top of ilastik 1.4.1b22 with bioimage model spec version 0.5
    """
    tests_root = pathlib.Path(__file__).parents[2]
    project_path = tests_root / "data" / "inputdata" / "NNLocaBatch-141b22-biov05-2d1c.ilp"
    return project_path


def load_h5_ds(fname, dataset):
    with h5py.File(fname, "r") as f:
        return f[dataset][()]


def test_nn_local_fails_with_old_project_file(project_path_140b30v4: pathlib.Path, tiktorch_executable_path):
    """use an ilastik project file with a simple model to test headless op

    Note: tiktorch_executable_path fixture used to ensure tiktorch can be started
    locally. Either it's in the env or provided to pytest via
    --tiktorch_executable

    """
    args = [
        "--headless",
        f"--project={project_path_140b30v4}",
    ]
    # Clear the existing commandline args so it looks like we're starting fresh.
    sys.argv = ["ilastik.py"]
    sys.argv.extend(args)

    with mock.patch("ilastik.config.runtime_cfg.tiktorch_executable", new=tiktorch_executable_path):
        with mock.patch("ilastik.workflows.WORKFLOW_CLASSES", new=[LocalWorkflow]):
            parsed_args, workflow_cmdline_args = app.parse_known_args()

            with pytest.raises(ValueError):
                _ = app.main(parsed_args=parsed_args, workflow_cmdline_args=workflow_cmdline_args, init_logging=False)


def test_nn_local(project_path_141b22v5: pathlib.Path, data_path, tmp_path, tiktorch_executable_path):
    """use an ilastik project file with a simple model to test headless op

    Note: tiktorch_executable_path fixture used to ensure tiktorch can be started
    locally. Either it's in the env or provided to pytest via
    --tiktorch_executable

    """
    input_file = data_path / "inputdata" / "2d.h5"
    output_file = tmp_path / "output.h5"
    args = [
        "--headless",
        f"--project={project_path_141b22v5}",
        "--raw_data",
        f"{input_file}",
        "--input_axes",
        "yx",
        "--output_filename_format",
        f"{output_file}",
        "--nn_device",
        "cpu",
    ]
    # Clear the existing commandline args so it looks like we're starting fresh.
    sys.argv = ["ilastik.py"]
    sys.argv.extend(args)

    with mock.patch("ilastik.config.runtime_cfg.tiktorch_executable", new=tiktorch_executable_path):
        with mock.patch("ilastik.workflows.WORKFLOW_CLASSES", new=[LocalWorkflow]):
            parsed_args, workflow_cmdline_args = app.parse_known_args()
            shell = app.main(parsed_args=parsed_args, workflow_cmdline_args=workflow_cmdline_args, init_logging=False)

            shell.closeCurrentProject()

            # NN model does (normalized input (scale linear gain 1/256) * -1 + 1
            output_ref = load_h5_ds(input_file, "data")[..., numpy.newaxis] * (1 / 256) * -1 + 1
            output = load_h5_ds(output_file, "exported_data")
            numpy.testing.assert_array_almost_equal(output, output_ref)
