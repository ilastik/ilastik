import sys
import subprocess

import pytest
import numpy as np
import xarray
from imageio import imread

from ilastik.experimental.api import from_project_file

from ..types import TestData, TestProjects, ApiTestDataLookup


def _load_as_xarray(dataset: TestData):
    loader = imread
    if dataset.path.endswith(".npy"):
        loader = np.load
    data = loader(dataset.path)
    return xarray.DataArray(data, dims=tuple(dataset.axes))


class TestIlastikApi:
    @pytest.fixture
    def run_headless(self, tmpdir):
        def _run_headless(proj, input):
            out_path = str(tmpdir / "out.npy")
            args = [
                sys.executable,
                "-m",
                "ilastik",
                "--headless",
                "--project",
                proj,
                input.path,
                "--input_axes",
                input.data_axes,
                "--output_format",
                "numpy",
                "--output_filename_format",
                out_path,
            ]
            subprocess.check_call(args)
            return np.load(out_path)

        return _run_headless

    @pytest.mark.parametrize(
        "input, proj",
        [
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XY),
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XYC),
            (TestData.DATA_3_CHANNEL, TestProjects.PIXEL_CLASS_3_CHANNEL),
            (TestData.DATA_1_CHANNEL_3D, TestProjects.PIXEL_CLASS_3D),
            (TestData.DATA_1_CHANNEL_3D, TestProjects.PIXEL_CLASS_3D_2D_3D_FEATURE_MIX),
        ],
    )
    def test_predict_pretrained(self, test_data_lookup: ApiTestDataLookup, input, proj, run_headless):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input)

        expected_prediction = run_headless(project_path, input_dataset)
        pipeline = from_project_file(project_path)

        prediction = pipeline.predict(_load_as_xarray(input_dataset))
        assert prediction.shape == expected_prediction.shape
        np.testing.assert_array_almost_equal(prediction, expected_prediction)

    @pytest.mark.parametrize(
        "input, proj",
        [
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XYC),
        ],
    )
    def test_predict_pretrained_with_axes_reordering(
        self,
        test_data_lookup: ApiTestDataLookup,
        input,
        proj,
        run_headless,
    ):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input)

        pipeline = from_project_file(project_path)
        expected_prediction = run_headless(project_path, input_dataset)

        input_data = _load_as_xarray(input_dataset)
        input_numpy = input_data.data

        reshaped_numpy = input_numpy.reshape(1, *input_numpy.shape)
        prediction = pipeline.predict(xarray.DataArray(reshaped_numpy, dims=(("c",) + input_data.dims)))
        assert prediction.shape == expected_prediction.shape
        np.testing.assert_array_almost_equal(prediction, expected_prediction, decimal=1)

    @pytest.mark.parametrize(
        "input, proj",
        [
            (TestData.DATA_3_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XYC),
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_3_CHANNEL),
        ],
    )
    def test_project_wrong_num_channels(self, test_data_lookup, input, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input)

        pipeline = from_project_file(project_path)

        with pytest.raises(ValueError):
            pipeline.predict(_load_as_xarray(input_dataset))

    @pytest.mark.parametrize(
        "input, proj",
        [
            (TestData.DATA_1_CHANNEL_3D, TestProjects.PIXEL_CLASS_1_CHANNEL_XYC),
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_3D),
        ],
    )
    def test_project_wrong_dimensionality(self, test_data_lookup, input, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input)

        pipeline = from_project_file(project_path)

        with pytest.raises(ValueError):
            pipeline.predict(_load_as_xarray(input_dataset))

    @pytest.mark.parametrize(
        "proj",
        [
            TestProjects.PIXEL_CLASS_NO_CLASSIFIER,
            TestProjects.PIXEL_CLASS_NO_DATA,
        ],
    )
    def test_project_insufficient_data(self, test_data_lookup, proj):
        project_path = test_data_lookup.find_project(proj)
        with pytest.raises(ValueError):
            from_project_file(project_path)
