import sys
import subprocess

import pytest
import numpy as np
import vigra
from imageio import imread

from ilastik.experimental.api import from_project_file

from ..types import TestData, ApiTestDataLookup


def _load_as_numpy(path):
    loader = imread
    if path.endswith(".npy"):
        loader = np.load
    return loader(path)


class TestIlastikApi:
    @pytest.fixture
    def run_headless(self, tmpdir, ilastik_py):
        def _run_headless(proj, input):
            out_path = str(tmpdir / "out.npy")
            args = [
                sys.executable,
                ilastik_py,
                "--headless",
                "--project",
                proj,
                input,
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
            (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL),
            (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL_SKLEARN),
            (TestData.DATA_3_CHANNEL, TestData.PIXEL_CLASS_3_CHANNEL),
            (TestData.DATA_1_CHANNEL_3D, TestData.PIXEL_CLASS_3D),
            (TestData.DATA_1_CHANNEL_3D, TestData.PIXEL_CLASS_3D_2D_3D_FEATURE_MIX),
        ],
    )
    def test_predict_pretrained(self, test_data_lookup: ApiTestDataLookup, input, proj, run_headless):
        project_path = test_data_lookup.find(proj)
        input_path = test_data_lookup.find(input)

        expected_prediction = run_headless(project_path, input_path)
        pipeline = from_project_file(project_path)

        prediction = pipeline.predict(_load_as_numpy(input_path))
        assert prediction.shape == expected_prediction.shape
        np.testing.assert_array_almost_equal(prediction, expected_prediction)

    @pytest.mark.parametrize(
        "input, proj, axes",
        [
            (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL, "yx"),
        ],
    )
    def test_predict_pretrained_with_axes_reordering(
        self,
        test_data_lookup: ApiTestDataLookup,
        input,
        proj,
        run_headless,
        axes,
    ):
        project_path = test_data_lookup.find(proj)
        input_path = test_data_lookup.find(input)

        pipeline = from_project_file(project_path)
        expected_prediction = run_headless(project_path, input_path)

        input_data = _load_as_numpy(input_path)
        reshaped_input = input_data.reshape(1, *input_data.shape)
        prediction = pipeline.predict(vigra.taggedView(reshaped_input, "c" + axes))
        assert prediction.shape == expected_prediction.shape
        np.testing.assert_array_almost_equal(prediction, expected_prediction, decimal=1)

    @pytest.mark.parametrize(
        "input, proj",
        [
            (TestData.DATA_3_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL),
            (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_3_CHANNEL),
        ],
    )
    def test_project_wrong_num_channels(self, test_data_lookup, input, proj):
        project_path = test_data_lookup.find(proj)
        input_path = test_data_lookup.find(input)

        pipeline = from_project_file(project_path)

        with pytest.raises(ValueError):
            pipeline.predict(_load_as_numpy(input_path))

    @pytest.mark.parametrize(
        "input, proj",
        [
            (TestData.DATA_1_CHANNEL_3D, TestData.PIXEL_CLASS_1_CHANNEL),
            (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_3D),
        ],
    )
    def test_project_wrong_dimensionality(self, test_data_lookup, input, proj):
        project_path = test_data_lookup.find(proj)
        input_path = test_data_lookup.find(input)

        pipeline = from_project_file(project_path)

        with pytest.raises(ValueError):
            pipeline.predict(_load_as_numpy(input_path))

    @pytest.mark.parametrize(
        "proj",
        [
            TestData.PIXEL_CLASS_NO_CLASSIFIER,
            TestData.PIXEL_CLASS_NO_DATA,
        ],
    )
    def test_project_insufficient_data(self, test_data_lookup, proj):
        project_path = test_data_lookup.find(proj)
        with pytest.raises(ValueError):
            from_project_file(project_path)
