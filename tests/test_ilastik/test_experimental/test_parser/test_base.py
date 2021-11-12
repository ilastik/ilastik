import pytest
import numpy as np

from ilastik.experimental.parser import IlastikProject

from ..types import TestProjects, ApiTestDataLookup
from lazyflow.classifiers.parallelVigraRfLazyflowClassifier import (
    ParallelVigraRfLazyflowClassifierFactory,
    ParallelVigraRfLazyflowClassifier,
)


class TestIlastikParser:
    @pytest.mark.parametrize(
        "proj, expected_num_channels",
        [
            (TestProjects.PIXEL_CLASS_1_CHANNEL_XYC, 1),
            (TestProjects.PIXEL_CLASS_3_CHANNEL, 3),
        ],
    )
    def test_parse_project_number_of_channels(self, test_data_lookup: ApiTestDataLookup, proj, expected_num_channels):
        project_path = test_data_lookup.find_project(proj)
        with IlastikProject(project_path) as proj:
            assert proj.data_info.num_channels == expected_num_channels

    @pytest.mark.parametrize(
        "proj, expected_factory, expected_classifier",
        [
            (
                TestProjects.PIXEL_CLASS_1_CHANNEL_XYC,
                ParallelVigraRfLazyflowClassifierFactory,
                ParallelVigraRfLazyflowClassifier,
            ),
        ],
    )
    def test_parse_project_classifier(self, test_data_lookup, proj, expected_factory, expected_classifier):
        project_path = test_data_lookup.find_project(proj)

        with IlastikProject(project_path) as proj:
            assert isinstance(proj.classifier.factory, expected_factory)
            assert isinstance(proj.classifier.instance, expected_classifier)

    tests = [
        (
            TestProjects.PIXEL_CLASS_1_CHANNEL_XYC,
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
            np.array([True, True, True, True, True, True, True]),
        ),
        (
            TestProjects.PIXEL_CLASS_3_CHANNEL,
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
            np.array([True, True, True, True, True, True, True]),
        ),
        (
            TestProjects.PIXEL_CLASS_3D_2D_3D_FEATURE_MIX,
            np.array(
                [
                    [True, False, False, False, False, True, False],
                    [False, False, False, True, False, False, False],
                    [False, False, False, True, False, False, False],
                    [False, False, False, True, False, False, False],
                    [False, False, False, False, True, False, False],
                    [False, False, False, False, True, False, False],
                ]
            ),
            np.array([False, False, False, True, False, True, False]),
        ),
    ]

    @pytest.mark.parametrize("proj, expected_sel_matrix, expected_compute_in_2d", tests)
    def test_parse_project_features(self, test_data_lookup, proj, expected_sel_matrix, expected_compute_in_2d):
        project_path = test_data_lookup.find_project(proj)

        with IlastikProject(project_path) as proj:
            matrix = proj.feature_matrix
            assert matrix
            np.testing.assert_array_equal(matrix.selections, expected_sel_matrix)
            np.testing.assert_array_equal(matrix.compute_in_2d, expected_compute_in_2d)
