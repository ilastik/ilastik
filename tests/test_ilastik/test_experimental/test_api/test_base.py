import pytest

import numpy as np
from imageio import imread

from ilastik.experimental.api import from_project_file

from ..types import TestData, ApiTestDataLookup

class TestIlastikApi:
    @pytest.fixture
    def input(self, request, test_data_lookup):
        print(request, test_data_lookup)
        input_data_path = test_data_lookup.find(request.param)

        loader = imread
        if input_data_path.endswith(".npy"):
            loader = np.load
        return loader(input_data_path)

    @pytest.mark.parametrize("input, proj, out", [
        (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL_OUT),
        (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL_SKLEARN, TestData.PIXEL_CLASS_1_CHANNEL_SKLEARN_OUT),
        (TestData.DATA_3_CHANNEL, TestData.PIXEL_CLASS_3_CHANNEL, TestData.PIXEL_CLASS_3_CHANNEL_OUT),
        (TestData.DATA_1_CHANNEL_3D, TestData.PIXEL_CLASS_3D, TestData.PIXEL_CLASS_3D_OUT),
    ], indirect=["input"])
    def test_predict_pretrained(self, test_data_lookup: ApiTestDataLookup, input, proj, out):
        project_path = test_data_lookup.find(proj)
        expected_prediction_path = test_data_lookup.find(out)

        pipeline = from_project_file(project_path)
        expected_prediction = np.load(expected_prediction_path)

        prediction = pipeline.predict(input)
        assert prediction.shape == expected_prediction.shape
        np.testing.assert_almost_equal(prediction, expected_prediction)

    @pytest.mark.parametrize("input, proj", [
        (TestData.DATA_3_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL),
        (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_3_CHANNEL),
    ], indirect=["input"])
    def test_project_wrong_num_channels(self, test_data_lookup, input, proj):
        project_path = test_data_lookup.find(proj)

        pipeline = from_project_file(project_path)

        with pytest.raises(ValueError):
            prediction = pipeline.predict(input)

    @pytest.mark.parametrize("input, proj", [
        (TestData.DATA_1_CHANNEL_3D, TestData.PIXEL_CLASS_1_CHANNEL),
        (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_3D),
    ], indirect=["input"])
    def test_project_wrong_dimensionality(self, test_data_lookup, input, proj):
        project_path = test_data_lookup.find(proj)

        pipeline = from_project_file(project_path)

        with pytest.raises(ValueError):
            prediction = pipeline.predict(input)

    @pytest.mark.parametrize("proj", [
        TestData.PIXEL_CLASS_NO_CLASSIFIER,
        TestData.PIXEL_CLASS_NO_DATA,
    ])
    def test_project_insufficient_data(self, test_data_lookup, proj):
        project_path = test_data_lookup.find(proj)
        with pytest.raises(ValueError):
            pipeline = from_project_file(project_path)
