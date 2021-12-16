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
    def test_parse_project_pixel_features(self, test_data_lookup, proj, expected_sel_matrix, expected_compute_in_2d):
        project_path = test_data_lookup.find_project(proj)

        with IlastikProject(project_path) as proj:
            matrix = proj.feature_matrix
            assert matrix
            np.testing.assert_array_equal(matrix.selections, expected_sel_matrix)
            np.testing.assert_array_equal(matrix.compute_in_2d, expected_compute_in_2d)

    def test_parse_project_object_threshold_settings(self, test_data_lookup):
        project_path = test_data_lookup.find_project(TestProjects.OBJ_CLASS_PRED_1_CHANNEL)
        expected_threshold_settings = {
            "method": 0,
            "min_size": 42,
            "max_size": 4242,
            "low_threshold": 0.42,
            "high_threshold": 0.8,
            "smoother_sigmas": {"x": 1.4000000000000004, "y": 0.9, "z": 1.0},
            "channel": 1,
            "core_channel": 0,
        }

        with IlastikProject(project_path) as proj:
            threshold_settings = proj.thresholding_settings
            for k, v in expected_threshold_settings.items():
                assert getattr(threshold_settings, k) == v

    def test_parse_project_object_features(self, test_data_lookup):
        project_path = test_data_lookup.find_project(TestProjects.OBJ_CLASS_SEG_1_CHANNEL)

        selected_features = {
            "2D Convex Hull Features": {
                "DefectCenter": {
                    "advanced": False,
                    "detailtext": b"Combined centroid of convexity defects, which are defined as areas of the convex hull, not covered by the original object.",
                    "displaytext": b"Defect Center",
                    "group": b"Location",
                    "tooltip": b"Convex Hull DefectCenter",
                }
            },
            "2D Skeleton Features": {
                "Diameter": {
                    "advanced": False,
                    "detailtext": b"The longest path between two endpoints on the skeleton.",
                    "displaytext": b"Diameter",
                    "group": b"Shape",
                    "tooltip": b"Skeleton Diameter",
                }
            },
            "Standard Object Features": {
                "Count": {
                    "advanced": False,
                    "detailtext": b"Total size of the object in pixels. No correction for anisotropic resolution or anything else.",
                    "displaytext": b"Size in pixels",
                    "group": b"Shape",
                    "tooltip": b"Count",
                },
                "Mean in neighborhood": {
                    "advanced": False,
                    "detailtext": b"Mean intensity in the object neighborhood. For multi-channel data, this feature is computed channel-wise. The size of the neighborhood is determined from the controls in the lower part of the dialogue.",
                    "displaytext": b"Mean Intensity in neighborhood",
                    "group": b"Intensity Distribution",
                    "margin": np.array([10, 20]),
                    "tooltip": b"Mean in neighborhood, as defined by neighborhood size below",
                },
            },
        }

        with IlastikProject(project_path) as proj:
            object_features = proj.selected_object_features

            assert_dict_equal(selected_features, object_features.selected_features)

    @pytest.mark.parametrize(
        "proj, expected_factory, expected_classifier",
        [
            (
                TestProjects.OBJ_CLASS_SEG_1_CHANNEL,
                ParallelVigraRfLazyflowClassifierFactory,
                ParallelVigraRfLazyflowClassifier,
            ),
            (
                TestProjects.OBJ_CLASS_PRED_1_CHANNEL,
                ParallelVigraRfLazyflowClassifierFactory,
                ParallelVigraRfLazyflowClassifier,
            ),
        ],
    )
    def test_parse_project_object_classifier(self, test_data_lookup, proj, expected_factory, expected_classifier):
        project_path = test_data_lookup.find_project(proj)

        with IlastikProject(project_path) as proj:
            assert issubclass(proj.classifier.factory, expected_factory)
            assert isinstance(proj.classifier.instance, expected_classifier)
            assert proj.ready_for_prediction


def assert_dict_equal(a, b):
    """Helper function to compare dicts that might have numpy arrays as values"""
    if isinstance(a, dict):
        assert isinstance(b, dict), f"Expected dictionary for second operand, got {type(b)}"
        assert a.keys() == b.keys()
        for k in a:
            assert_dict_equal(a[k], b[k])
    elif isinstance(a, np.ndarray):
        np.testing.assert_array_equal(a, b)
    else:
        assert a == b, f"{a} not equal to {b}"
