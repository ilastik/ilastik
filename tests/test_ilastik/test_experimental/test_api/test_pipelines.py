import imageio.v3 as iio
import numpy as np
import pytest
import xarray
from pydantic import ValidationError

from ilastik.experimental.api import AutocontextPipeline, PixelClassificationPipeline, from_project_file

from ..types import ApiTestDataLookup, Dataset, TestData, TestProjects


def assert_predictions_equal_ilastik_cross(a, b):
    """Compares ilastik prediction results

    Accuracies are tuned to allow passing tests across architectures.
    Applicable for pixel classification and autocontext results.

    This function requires that 99.9 % of pixels have a deviation lower
    than 0.015 and all pixels deviate less than 0.15.

    Checks:
      * less than 0.1 % deviate more than 0.015 (equal to what
        `numpy.testing.assert_array_almost_equal` assumes for 2 decimals)
      * no pixels have deviation more than 0.15 (equal to what
        `numpy.testing.assert_array_almost_equal` assumes for 1 decimals)

    """
    # Hide traceback in pytest for this function
    __tracebackhide__ = True
    diff = np.abs(a - b)

    n_2dec = np.count_nonzero(diff >= 1.5 * 10 ** (-2))

    if n_2dec / diff.size > 10 ** (-3):
        np.testing.assert_array_almost_equal(a, b, decimal=2)

    n_1dec = np.count_nonzero(diff >= 1.5 * 10 ** (-1))
    if n_1dec != 0:
        np.testing.assert_array_almost_equal(a, b, decimal=1)


def _load_as_xarray(dataset: Dataset):
    loader = iio.imread
    if dataset.path.endswith(".npy"):
        loader = np.load
    data = loader(dataset.path)
    return xarray.DataArray(data, dims=tuple(dataset.axes))


class TestIlastikApiPixelClassification:

    @pytest.mark.parametrize(
        "input_, proj",
        [
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XY),
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XYC),
            (TestData.DATA_3_CHANNEL, TestProjects.PIXEL_CLASS_3_CHANNEL),
            (TestData.DATA_1_CHANNEL_3D, TestProjects.PIXEL_CLASS_3D),
            (TestData.DATA_1_CHANNEL_3D, TestProjects.PIXEL_CLASS_3D_2D_3D_FEATURE_MIX),
        ],
    )
    def test_predict_pretrained(self, test_data_lookup: ApiTestDataLookup, input_, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input_)

        expected_prediction = _load_as_xarray(test_data_lookup.find_test_result(proj, input_, "Probabilities"))
        pipeline = PixelClassificationPipeline.from_ilp_file(project_path)

        prediction = pipeline.get_probabilities(_load_as_xarray(input_dataset))
        assert prediction.shape == expected_prediction.shape
        assert_predictions_equal_ilastik_cross(prediction, expected_prediction)

    @pytest.mark.parametrize(
        "input_, proj",
        [
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XYC),
        ],
    )
    def test_predict_pretrained_with_axes_reordering(
        self,
        test_data_lookup: ApiTestDataLookup,
        input_,
        proj,
    ):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input_)

        pipeline = PixelClassificationPipeline.from_ilp_file(project_path)
        expected_prediction = _load_as_xarray(test_data_lookup.find_test_result(proj, input_, "Probabilities"))

        input_data = _load_as_xarray(input_dataset)
        input_numpy = input_data.data

        reshaped_numpy = input_numpy.reshape(1, *input_numpy.shape)
        prediction = pipeline.get_probabilities(xarray.DataArray(reshaped_numpy, dims=(("c",) + input_data.dims)))
        assert prediction.shape == expected_prediction.shape
        np.testing.assert_array_almost_equal(prediction, expected_prediction, decimal=1)

    @pytest.mark.parametrize(
        "input_, proj",
        [
            (TestData.DATA_3_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XYC),
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_3_CHANNEL),
        ],
    )
    def test_project_wrong_num_channels(self, test_data_lookup, input_, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input_)

        pipeline = PixelClassificationPipeline.from_ilp_file(project_path)

        with pytest.raises(ValueError):
            pipeline.get_probabilities(_load_as_xarray(input_dataset))

    @pytest.mark.parametrize(
        "input_, proj",
        [
            (TestData.DATA_1_CHANNEL_3D, TestProjects.PIXEL_CLASS_1_CHANNEL_XYC),
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_3D),
        ],
    )
    def test_project_wrong_dimensionality(self, test_data_lookup, input_, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input_)

        pipeline = PixelClassificationPipeline.from_ilp_file(project_path)

        with pytest.raises(ValueError):
            pipeline.get_probabilities(_load_as_xarray(input_dataset))

    @pytest.mark.parametrize(
        "proj",
        [
            TestProjects.PIXEL_CLASS_NO_CLASSIFIER,
            TestProjects.PIXEL_CLASS_NO_DATA,
        ],
    )
    def test_project_insufficient_data(self, test_data_lookup, proj):
        project_path = test_data_lookup.find_project(proj)
        with pytest.raises(ValidationError):
            PixelClassificationPipeline.from_ilp_file(project_path)

    @pytest.mark.parametrize(
        "input_, proj",
        [
            (TestData.DATA_1_CHANNEL, TestProjects.PIXEL_CLASS_1_CHANNEL_XY),
            (TestData.DATA_3_CHANNEL, TestProjects.PIXEL_CLASS_3_CHANNEL),
        ],
    )
    def test_legacy_operation(self, test_data_lookup: ApiTestDataLookup, input_, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input_)

        expected_prediction = _load_as_xarray(test_data_lookup.find_test_result(proj, input_, "Probabilities"))
        with pytest.deprecated_call():
            pipeline = from_project_file(project_path)

        with pytest.deprecated_call():
            prediction = pipeline.predict(_load_as_xarray(input_dataset))

        assert prediction.shape == expected_prediction.shape
        assert_predictions_equal_ilastik_cross(prediction, expected_prediction)


class TestIlastikApiAutocontext:

    @pytest.mark.parametrize(
        "input_, proj",
        [
            (TestData.DATA_1_CHANNEL, TestProjects.AUTOCONTEXT_2D),
            (TestData.DATA_1_CHANNEL_3D, TestProjects.AUTOCONTEXT_3D),
        ],
    )
    def test_predict_pretrained(self, test_data_lookup: ApiTestDataLookup, input_, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input_)

        expected_prediction_stage_1 = _load_as_xarray(
            test_data_lookup.find_test_result(proj, input_, "Probabilities Stage 1")
        )
        expected_prediction_stage_2 = _load_as_xarray(
            test_data_lookup.find_test_result(proj, input_, "Probabilities Stage 2")
        )
        pipeline = AutocontextPipeline.from_ilp_file(project_path)

        prediction_stage_1 = pipeline.get_probabilities_stage_1(_load_as_xarray(input_dataset))
        assert prediction_stage_1.shape == expected_prediction_stage_1.shape
        assert_predictions_equal_ilastik_cross(prediction_stage_1, expected_prediction_stage_1)

        prediction_stage_2 = pipeline.get_probabilities_stage_2(_load_as_xarray(input_dataset))
        assert prediction_stage_2.shape == expected_prediction_stage_2.shape
        assert_predictions_equal_ilastik_cross(prediction_stage_2, expected_prediction_stage_2)

    @pytest.mark.parametrize(
        "input_, proj",
        [
            (TestData.DATA_3_CHANNEL, TestProjects.AUTOCONTEXT_2D),
        ],
    )
    def test_project_wrong_num_channels(self, test_data_lookup, input_, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input_)

        pipeline = AutocontextPipeline.from_ilp_file(project_path)

        with pytest.raises(ValueError):
            pipeline.get_probabilities_stage_2(_load_as_xarray(input_dataset))

    @pytest.mark.parametrize(
        "input_, proj",
        [
            (TestData.DATA_1_CHANNEL_3D, TestProjects.AUTOCONTEXT_2D),
            (TestData.DATA_1_CHANNEL, TestProjects.AUTOCONTEXT_3D),
        ],
    )
    def test_project_wrong_dimensionality(self, test_data_lookup, input_, proj):
        project_path = test_data_lookup.find_project(proj)
        input_dataset = test_data_lookup.find_dataset(input_)

        pipeline = AutocontextPipeline.from_ilp_file(project_path)

        with pytest.raises(ValueError):
            pipeline.get_probabilities_stage_2(_load_as_xarray(input_dataset))
