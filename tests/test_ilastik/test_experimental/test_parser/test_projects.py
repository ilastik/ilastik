import h5py
import numpy as np
import pytest

from ilastik.experimental.parser import AutocontextProject, PixelClassificationProject
from lazyflow.classifiers.parallelVigraRfLazyflowClassifier import (
    ParallelVigraRfLazyflowClassifier,
    ParallelVigraRfLazyflowClassifierFactory,
)

from ..types import ApiTestDataLookup, TestProjects


class TestIlastikPixelClassificationParser:
    @pytest.mark.parametrize(
        "proj, expected_num_channels",
        [
            (TestProjects.PIXEL_CLASS_1_CHANNEL_XYC, 1),
            (TestProjects.PIXEL_CLASS_3_CHANNEL, 3),
        ],
    )
    def test_parse_project_number_of_channels(self, test_data_lookup: ApiTestDataLookup, proj, expected_num_channels):
        project_path = test_data_lookup.find_project(proj)
        with h5py.File(project_path, "r") as f:
            project = PixelClassificationProject.model_validate(f)

        assert project.input_data.num_channels == expected_num_channels

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

        with h5py.File(project_path, "r") as f:
            project = PixelClassificationProject.model_validate(f)

        assert isinstance(project.classifier.classifier_factory, expected_factory)
        assert isinstance(project.classifier.classifier, expected_classifier)

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

        with h5py.File(project_path, "r") as f:
            project = PixelClassificationProject.model_validate(f)

        matrix = project.feature_matrix
        assert matrix
        np.testing.assert_array_equal(matrix.selections, expected_sel_matrix)
        np.testing.assert_array_equal(matrix.compute_in_2d, expected_compute_in_2d)


class TestIlastikAutocontextParser:

    @pytest.mark.parametrize(
        "proj, expected_factory, expected_classifier",
        [
            (
                TestProjects.AUTOCONTEXT_2D,
                ParallelVigraRfLazyflowClassifierFactory,
                ParallelVigraRfLazyflowClassifier,
            ),
        ],
    )
    def test_parse_project_classifier(self, test_data_lookup, proj, expected_factory, expected_classifier):
        project_path = test_data_lookup.find_project(proj)

        with h5py.File(project_path, "r") as f:
            project: AutocontextProject = AutocontextProject.model_validate(f)

        assert isinstance(project.classifier_stage1.classifier_factory, expected_factory)
        assert isinstance(project.classifier_stage1.classifier, expected_classifier)

        assert isinstance(project.classifier_stage2.classifier_factory, expected_factory)
        assert isinstance(project.classifier_stage2.classifier, expected_classifier)

    tests = [
        (
            TestProjects.AUTOCONTEXT_2D,
            np.array(
                [
                    [True, False, True, False, True, False, False],
                    [False, False, True, False, True, False, False],
                    [False, False, True, False, True, False, False],
                    [False, False, True, False, True, False, False],
                    [False, False, True, False, True, False, False],
                    [False, False, True, False, True, False, False],
                ]
            ),
            np.array([True, True, True, True, True, True, True]),
            np.array(
                [
                    [True, False, False, True, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, True, False, False, True, False, False],
                    [False, True, False, False, True, False, False],
                ]
            ),
            np.array([True, True, True, True, True, True, True]),
        ),
        (
            TestProjects.AUTOCONTEXT_3D,
            np.array(
                [
                    [True, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                ]
            ),
            np.array([False, True, True, True, True, True, True]),
            np.array(
                [
                    [True, False, False, True, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, False, True, False, False, False, False],
                    [False, True, False, False, False, False, False],
                    [False, True, False, False, False, False, False],
                ]
            ),
            np.array([True, False, True, True, True, True, True]),
        ),
    ]

    @pytest.mark.parametrize(
        "proj, expected_sel_matrix_1, expected_compute_in_2d_1, expected_sel_matrix_2, expected_compute_in_2d_2", tests
    )
    def test_parse_project_features(
        self,
        test_data_lookup,
        proj,
        expected_sel_matrix_1,
        expected_compute_in_2d_1,
        expected_sel_matrix_2,
        expected_compute_in_2d_2,
    ):
        project_path = test_data_lookup.find_project(proj)

        with h5py.File(project_path, "r") as f:
            project: AutocontextProject = AutocontextProject.model_validate(f)

        matrix_1 = project.feature_matrix_stage1
        assert matrix_1
        np.testing.assert_array_equal(matrix_1.selections, expected_sel_matrix_1)
        np.testing.assert_array_equal(matrix_1.compute_in_2d, expected_compute_in_2d_1)

        matrix_2 = project.feature_matrix_stage2
        assert matrix_2
        np.testing.assert_array_equal(matrix_2.selections, expected_sel_matrix_2)
        np.testing.assert_array_equal(matrix_2.compute_in_2d, expected_compute_in_2d_2)
