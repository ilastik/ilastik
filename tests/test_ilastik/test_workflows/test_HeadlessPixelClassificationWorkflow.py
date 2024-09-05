import http.server
import json
import socket
import threading
import time
from functools import partial
from pathlib import Path
import shutil
import logging
import tempfile
import os
from typing import Dict, Optional, Union, Tuple

import pytest
import numpy
import vigra
import h5py
import z5py
import zipfile
import psutil
import zarr

from lazyflow.utility.io_util.OMEZarrStore import OME_ZARR_V_0_4_KWARGS

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
    raw_data: Union[Path, str],
    use_raw_data_as_positional_argument: bool = False,
    output_filename_format: str,
    input_axes: str = "",
    output_format: str = "hdf5",
    ignore_training_axistags: bool = False,
):
    assert project.exists()
    if isinstance(raw_data, Path):
        assert raw_data.parent.exists()

    subprocess_args = [
        "python",
        "-m",
        "ilastik",
        "--headless",
        f"--project={project}",
        f"--output_filename_format={output_filename_format}",
        f"--output_format={output_format}",
    ]

    if input_axes:
        subprocess_args.append(f"--input-axes={input_axes}")

    if ignore_training_axistags:
        subprocess_args.append("--ignore_training_axistags")

    if num_distributed_workers:
        os.environ["OMPI_ALLOW_RUN_AS_ROOT"] = "1"
        os.environ["OMPI_ALLOW_RUN_AS_ROOT_CONFIRM"] = "1"
        subprocess_args = ["mpiexec", "-n", str(num_distributed_workers)] + subprocess_args + ["--distributed"]
        if distributed_block_roi:
            subprocess_args += ["--distributed-block-roi", str(distributed_block_roi)]

    raw_data_arg_prefix = "" if use_raw_data_as_positional_argument else "--raw-data="
    subprocess_args.append(f"{raw_data_arg_prefix}{raw_data}")

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


def test_headless_2d3c_with_permuted_raw_data_axis_from_training_data_raises(
    testdir, pixel_classification_ilp_2d3c: Path, tmp_path: Path
):
    """
    default behavior is to try to apply training axistags to the batch data,
    and therefore fail because raw data' axis (cyx) are not in the expected order (yxc)
    """
    raw_3c100x100y: Path = create_h5(numpy.random.rand(3, 100, 100), axiskeys="cyx")
    output_path = tmp_path / "out_3c100x100y.h5"

    with pytest.raises(FailedHeadlessExecutionException):
        run_headless_pixel_classification(
            testdir,
            project=pixel_classification_ilp_2d3c,
            raw_data=raw_3c100x100y,
            output_filename_format=str(output_path),
        )


def test_headless_2d3c_with_permuted_raw_data_axis_explicit_axes(
    testdir, pixel_classification_ilp_2d3c: Path, tmp_path: Path
):
    """forcing correct input axes should pass"""
    raw_3c100x100y: Path = create_h5(numpy.random.rand(3, 100, 100), axiskeys="cyx")
    output_path = tmp_path / "out_3c100x100y.h5"

    run_headless_pixel_classification(
        testdir,
        project=pixel_classification_ilp_2d3c,
        raw_data=raw_3c100x100y,
        output_filename_format=str(output_path),
        input_axes="cyx",
    )


def test_headless_2d3c_with_permuted_raw_data_axis_use_h5_tags(
    testdir, pixel_classification_ilp_2d3c: Path, tmp_path: Path
):
    """
    alternatively, since the generated h5 data has the axistags property, we can ignore training data and use that
    instead, by using the '--ignore_training_axistags' flag
    """
    raw_3c100x100y: Path = create_h5(numpy.random.rand(3, 100, 100), axiskeys="cyx")
    output_path = tmp_path / "out_3c100x100y.h5"

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


@pytest.fixture
def ome_zarr_store_on_disc(tmp_path) -> str:
    """Sets up a zarr store of a random image at raw scale and a downscale.
    Returns the store's subdir under tmp_path"""
    subdir = "some.zarr"
    zarr_dir = tmp_path / subdir
    zarr_dir.mkdir(parents=True, exist_ok=True)

    dataset_shape = [3, 100, 100]  # cyx - to match the 2d3c project
    scaled_shape = [3, 50, 50]
    chunk_size = [3, 64, 64]
    zattrs = {
        "multiscales": [
            {
                "name": "some.zarr",
                "type": "Sample",
                "version": "0.4",
                "axes": [
                    {"type": "space", "name": "c"},
                    {"type": "space", "name": "y", "unit": "pixel"},
                    {"type": "space", "name": "x", "unit": "pixel"},
                ],
                "datasets": [
                    {
                        "path": "s0",
                        "coordinateTransformations": [
                            {"scale": [1.0 for _ in dataset_shape], "type": "scale"},
                            {"translation": [0.0 for _ in dataset_shape], "type": "translation"},
                        ],
                    },
                    {
                        "path": "s1",
                        "coordinateTransformations": [
                            {"scale": [2.0 for _ in scaled_shape], "type": "scale"},
                            {"translation": [0.0 for _ in scaled_shape], "type": "translation"},
                        ],
                    },
                ],
                "coordinateTransformations": [],
            }
        ]
    }
    (zarr_dir / ".zattrs").write_text(json.dumps(zattrs))

    image_original = numpy.random.randint(0, 256, dataset_shape, dtype=numpy.uint16)
    image_scaled = image_original[:, ::2, ::2]
    chunks = tuple(chunk_size)
    zarr.array(image_original, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir / "s0")), **OME_ZARR_V_0_4_KWARGS)
    zarr.array(image_scaled, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir / "s1")), **OME_ZARR_V_0_4_KWARGS)

    return subdir


def test_headless_from_ome_zarr_file_uri(testdir, tmp_path, pixel_classification_ilp_2d3c, ome_zarr_store_on_disc):
    # Request raw scale to test that the full path is used.
    # The loader implementation defaults to loading the lowest resolution (last scale).
    raw_data_path = tmp_path / ome_zarr_store_on_disc / "s0"
    output_path = tmp_path / "out_100x100y3c.h5"
    run_headless_pixel_classification(
        testdir,
        project=pixel_classification_ilp_2d3c,
        raw_data=raw_data_path.as_uri(),
        output_filename_format=str(output_path),
        ignore_training_axistags=True,
    )

    assert output_path.exists()
    with h5py.File(output_path, "r") as f:
        exported = f["exported_data"][()]
        assert exported.shape == (2, 100, 100)
        # Make sure the raw data was actually loaded (zarr fills chunks that fail to load with 0)
        assert numpy.count_nonzero(exported) > 10000


def wait_for_server(host_and_port: Tuple[str, int], timeout=5):
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            with socket.create_connection(host_and_port, timeout=1):
                return True
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Server on {':'.join(host_and_port)} didn't start within {timeout} seconds")


@pytest.fixture
def ome_zarr_store_via_localhost(tmp_path, ome_zarr_store_on_disc) -> str:
    """Serves ome_zarr_store_on_disc on a random open port under localhost.
    Returns the store's base URI."""
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = http.server.HTTPServer(("localhost", 0), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True  # Allows the server to be killed after the test ends
    thread.start()
    wait_for_server(("localhost", server.server_port))

    yield f"http://localhost:{server.server_port}/{ome_zarr_store_on_disc}"

    server.shutdown()
    thread.join()


def test_headless_from_ome_zarr_http_uri(
    testdir, tmp_path, pixel_classification_ilp_2d3c, ome_zarr_store_via_localhost
):
    # Request raw scale to test that the full path is used.
    # The loader implementation defaults to loading the lowest resolution (last scale).
    raw_data_path = f"{ome_zarr_store_via_localhost}/s0"
    output_path = tmp_path / "out_100x100y3c.h5"
    run_headless_pixel_classification(
        testdir,
        project=pixel_classification_ilp_2d3c,
        raw_data=raw_data_path,
        output_filename_format=str(output_path),
        ignore_training_axistags=True,
    )

    assert output_path.exists()
    with h5py.File(output_path, "r") as f:
        exported = f["exported_data"][()]
        assert exported.shape == (2, 100, 100)
        # Make sure the raw data was actually loaded (zarr fills chunks that fail to load with 0)
        assert numpy.count_nonzero(exported) > 10000
