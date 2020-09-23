import pytest
import numpy as np

from ilastik.experimental.parser import IlastikProject

from ..types import TestData, ApiTestDataLookup
from lazyflow.classifiers.parallelVigraRfLazyflowClassifier import (
    ParallelVigraRfLazyflowClassifierFactory,
    ParallelVigraRfLazyflowClassifier,
)
from lazyflow.classifiers.sklearnLazyflowClassifier import SklearnLazyflowClassifierFactory, SklearnLazyflowClassifier


class TestIlastikParser:
    @pytest.mark.parametrize(
        "proj, expected_num_channels",
        [
            (TestData.PIXEL_CLASS_1_CHANNEL, 1),
            (TestData.PIXEL_CLASS_3_CHANNEL, 3),
        ],
    )
    def test_parse_project_number_of_channels(self, test_data_lookup: ApiTestDataLookup, proj, expected_num_channels):
        project_path = test_data_lookup.find(proj)
        with IlastikProject(project_path) as proj:
            assert proj.data_info.num_channels == expected_num_channels

    @pytest.mark.parametrize(
        "proj, expected_factory, expected_classifier",
        [
            (
                TestData.PIXEL_CLASS_1_CHANNEL,
                ParallelVigraRfLazyflowClassifierFactory,
                ParallelVigraRfLazyflowClassifier,
            ),
            (TestData.PIXEL_CLASS_1_CHANNEL_SKLEARN, SklearnLazyflowClassifierFactory, SklearnLazyflowClassifier),
        ],
    )
    def test_parse_project_classifier(self, test_data_lookup, proj, expected_factory, expected_classifier):
        project_path = test_data_lookup.find(proj)

        with IlastikProject(project_path) as proj:
            assert isinstance(proj.classifier.factory, expected_factory)
            assert isinstance(proj.classifier.instance, expected_classifier)

    tests = [
        (
            TestData.PIXEL_CLASS_1_CHANNEL,
            np.array(
                [
                    [True, False, True, False, True, False, True],
                    [False, True, False, True, False, True, False],
                    [False, True, False, True, False, True, False],
                    [False, True, False, True, False, True, False],
                    [False, False, True, False, True, False, True],
                    [False, False, True, False, True, False, True],
                ]
            ),
        ),
        (
            TestData.PIXEL_CLASS_3_CHANNEL,
            np.array(
                [
                    [True, True, True, True, False, False, False],
                    [False, True, True, True, False, False, False],
                    [False, True, True, True, False, False, False],
                    [False, True, True, True, False, False, False],
                    [False, True, True, True, False, False, False],
                    [False, True, True, True, False, False, False],
                ]
            ),
        ),
    ]

    @pytest.mark.parametrize("proj, expected_sel_matrix", tests)
    def test_parse_project_features(self, test_data_lookup, proj, expected_sel_matrix):
        project_path = test_data_lookup.find(proj)

        with IlastikProject(project_path) as proj:
            matrix = proj.features.as_matrix()

            assert matrix
            np.testing.assert_array_equal(matrix.selections, expected_sel_matrix)
