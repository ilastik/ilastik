from pathlib import Path
import shutil
import subprocess
import logging
import tempfile
import json
import os
from typing import Dict, Optional

import pytest
import numpy
import vigra
import h5py
import z5py
import zipfile
from ndstructs import Array5D, Shape5D
import psutil

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pytest_plugins = ["pytester"]

try:
    from lazyflow.distributed.TaskOrchestrator import TaskOrchestrator

    MPI_DEPENDENCIES_MET = bool(shutil.which("mpiexec"))
except ImportError:
    MPI_DEPENDENCIES_MET = False


@pytest.fixture
def sample_projects_dir(tmp_path: Path) -> Path:
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


def create_h5(data: numpy.ndarray, axiskeys: str) -> Path:
    assert len(axiskeys) == len(data.shape)
    path = tempfile.mkstemp()[1] + ".h5"
    with h5py.File(path, "w") as f:
        ds = f.create_dataset("data", data=data)
        ds.attrs["axistags"] = vigra.defaultAxistags(axiskeys).toJSON()

    return Path(path) / "data"


class FailedHeadlessExecutionException(Exception):
    pass


def run_headless_pixel_classification(
    testdir,
    *,
    num_distributed_workers: int = 0,
    distributed_block_roi: Optional[Dict[str, slice]] = None,
    project: Path,
    raw_data: Path,
    use_raw_data_as_positional_argument: bool = False,
    output_filename_format: str,
    input_axes: str = "",
    output_format: str = "hdf5",
    ignore_training_axistags: bool = False,
):
    assert project.exists()
    assert raw_data.parent.exists()

    subprocess_args = [
        "python",
        "-m",
        "ilastik",
        "--headless",
        "--project=" + str(project),
        "--output_filename_format=" + str(output_filename_format),
        "--output_format=" + output_format,
    ]

    if input_axes:
        subprocess_args.append("--input-axes=" + input_axes)

    if ignore_training_axistags:
        subprocess_args.append("--ignore_training_axistags")

    if num_distributed_workers:
        os.environ["OMPI_ALLOW_RUN_AS_ROOT"] = "1"
        os.environ["OMPI_ALLOW_RUN_AS_ROOT_CONFIRM"] = "1"
        subprocess_args = ["mpiexec", "-n", str(num_distributed_workers)] + subprocess_args + ["--distributed"]
        if distributed_block_roi:
            subprocess_args += ["--distributed-block-roi", str(distributed_block_roi)]

    raw_data_arg_prefix = "" if use_raw_data_as_positional_argument else "--raw-data="
    subprocess_args.append(raw_data_arg_prefix + str(raw_data))

    result = testdir.run(*subprocess_args)
    if result.ret != 0:
        raise FailedHeadlessExecutionException(
            "===STDOUT===\n\n" + result.stdout.str() + "\n\n===STDERR===\n\n" + result.stderr.str()
        )


def test_headless_2d3c_with_same_raw_data_axis(testdir, pixel_classification_ilp_2d3c: Path, tmp_path: Path):
    raw_100x100y3c: Path = create_h5(numpy.random.rand(100, 100, 3), axiskeys="yxc")
    output_path = tmp_path / "out_100x100y3c.h5"
    run_headless_pixel_classification(
        testdir, project=pixel_classification_ilp_2d3c, raw_data=raw_100x100y3c, output_filename_format=str(output_path)
    )


def test_headless_2d3c_with_permuted_raw_data_axis(testdir, pixel_classification_ilp_2d3c: Path, tmp_path: Path):
    raw_3c100x100y: Path = create_h5(numpy.random.rand(3, 100, 100), axiskeys="cyx")
    output_path = tmp_path / "out_3c100x100y.h5"

    # default behavior is to try to apply training axistags to the batch data, and therefore fail because raw data's
    # axis (cyx) are not in the expected order (yxc)
    with pytest.raises(FailedHeadlessExecutionException):
        run_headless_pixel_classification(
            testdir,
            project=pixel_classification_ilp_2d3c,
            raw_data=raw_3c100x100y,
            output_filename_format=str(output_path),
        )

    # forcing correct input axes should pass
    run_headless_pixel_classification(
        testdir,
        project=pixel_classification_ilp_2d3c,
        raw_data=raw_3c100x100y,
        output_filename_format=str(output_path),
        input_axes="cyx",
    )

    # alternatively, since the generated h5 data has the axistags property, we can ignore training data and use that
    # instead, by using the '--ignore_training_axistags' flag
    run_headless_pixel_classification(
        testdir,
        project=pixel_classification_ilp_2d3c,
        raw_data=raw_3c100x100y,
        output_filename_format=str(output_path),
        ignore_training_axistags=True,
    )


@pytest.mark.skipif(not MPI_DEPENDENCIES_MET, reason="Must have mpi4py and mpiexec installed fot this test")
def test_distributed_results_are_identical_to_single_process_results(
    testdir, pixel_classification_ilp_2d3c: Path, tmp_path: Path
):
    raw_100x100y3c: Path = create_h5(numpy.random.rand(100, 100, 3), axiskeys="yxc")

    single_process_output_path = tmp_path / "single_process_out_100x100y3c.h5"
    run_headless_pixel_classification(
        testdir,
        project=pixel_classification_ilp_2d3c,
        raw_data=raw_100x100y3c,
        output_filename_format=str(single_process_output_path),
    )

    with h5py.File(single_process_output_path, "r") as f:
        single_process_out_data = f["exported_data"][()]

    distributed_output_path = tmp_path / "distributed_out_100x100y3c.n5"
    run_headless_pixel_classification(
        testdir,
        num_distributed_workers=min(4, psutil.cpu_count(logical=False)),
        output_format="n5",
        project=pixel_classification_ilp_2d3c,
        raw_data=raw_100x100y3c,
        output_filename_format=str(distributed_output_path),
    )

    with z5py.File(distributed_output_path, "r") as f:
        distributed_out_data = f["exported_data"][()]

    assert (single_process_out_data == distributed_out_data).all()

    distributed_50x50block_output_path = tmp_path / "distributed_50x50block_out_100x100y3c.n5"
    run_headless_pixel_classification(
        testdir,
        num_distributed_workers=min(4, psutil.cpu_count(logical=False)),
        distributed_block_roi={"x": 50, "y": 50},
        output_format="n5",
        project=pixel_classification_ilp_2d3c,
        raw_data=raw_100x100y3c,
        use_raw_data_as_positional_argument=True,
        output_filename_format=str(distributed_50x50block_output_path),
    )

    with z5py.File(distributed_50x50block_output_path, "r") as f:
        dataset = f["exported_data"]
        axiskeys = "".join(dataset.attrs["axes"]).lower()[::-1]
        assert {k: v for k, v in zip(axiskeys, dataset.chunks)} == {"x": 50, "y": 50, "c": 2}
        distributed_50x50block_data = dataset[()]

    assert (single_process_out_data == distributed_50x50block_data).all()
