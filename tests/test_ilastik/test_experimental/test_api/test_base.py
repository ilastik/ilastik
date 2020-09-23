import pytest

import numpy as np
from imageio import imread

from ilastik.experimental.api import from_project_file

from ..types import TestData, ApiTestDataLookup


class TestIlastikApi:
    @pytest.mark.parametrize("input, proj, out", [
        (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL_OUT),
        (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL_SKLEARN, TestData.PIXEL_CLASS_1_CHANNEL_SKLEARN_OUT),
        (TestData.DATA_3_CHANNEL, TestData.PIXEL_CLASS_3_CHANNEL, TestData.PIXEL_CLASS_3_CHANNEL_OUT),
    ])
    def test_predict_pretrained(self, test_data_lookup: ApiTestDataLookup, input, proj, out):
        input_data_path = test_data_lookup.find(input)
        project_path = test_data_lookup.find(proj)
        expected_prediction_path = test_data_lookup.find(out)

        data = imread(input_data_path)
        some = from_project_file(project_path)
        expected_prediction = np.load(expected_prediction_path)

        prediction = some.predict(data)
        assert prediction.shape == expected_prediction.shape
        np.testing.assert_almost_equal(prediction, expected_prediction)

    @pytest.mark.parametrize("input, proj", [
        (TestData.DATA_3_CHANNEL, TestData.PIXEL_CLASS_1_CHANNEL),
        (TestData.DATA_1_CHANNEL, TestData.PIXEL_CLASS_3_CHANNEL),
    ])
    def test_project_wrong_num_channels(self, test_data_lookup, input, proj):
        input_data_path = test_data_lookup.find(input)
        project_path = test_data_lookup.find(proj)

        data = imread(input_data_path)
        some = from_project_file(project_path)

        with pytest.raises(ValueError):
            prediction = some.predict(data)
