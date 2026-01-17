###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import pytest

from ilastik.shell.headless.headlessShell import HeadlessShell
from ilastik.workflows import (
    AutocontextTwoStage,
    CountingWorkflow,
    ObjectClassificationWorkflowPrediction,
    PixelClassificationWorkflow,
)
from lazyflow.utility.data_semantics import ImageTypes

"""
Ensure image semantics metadata is correctly carried into export slots
"""


@pytest.fixture
def pc_workflow(pixel_classification_ilp_2d3c):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(pixel_classification_ilp_2d3c))
    return shell.projectManager.workflow


@pytest.mark.parametrize(
    "export_source,expected_semantics",
    [
        (PixelClassificationWorkflow.ExportNames.PROBABILITIES, ImageTypes.Intensities),
        (PixelClassificationWorkflow.ExportNames.SIMPLE_SEGMENTATION, ImageTypes.Labels),
        (PixelClassificationWorkflow.ExportNames.UNCERTAINTY, ImageTypes.Intensities),
        (PixelClassificationWorkflow.ExportNames.FEATURES, ImageTypes.Intensities),
        (PixelClassificationWorkflow.ExportNames.LABELS, ImageTypes.Labels),
    ],
)
def test_pixel_classification(pc_workflow, export_source, expected_semantics):
    op_data_export = pc_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(export_source)
    export_slot_meta = op_data_export.ImageToExport[0].meta
    default_is_expected = expected_semantics == ImageTypes.Intensities

    assert (
        "data_semantics" in export_slot_meta or default_is_expected
    ), "interpolation order meta only allowed to be absent if default interpolation is appropriate"
    if "data_semantics" in export_slot_meta:
        assert export_slot_meta.data_semantics == expected_semantics


@pytest.fixture
def autocontext_workflow(autocontext_ilp_2d3c):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(autocontext_ilp_2d3c))
    return shell.projectManager.workflow


@pytest.mark.parametrize(
    "export_source,expected_semantics",
    [
        (0, ImageTypes.Intensities),  # Probabilities Stage 1
        (1, ImageTypes.Labels),  # Simple Segmentation Stage 1
        (2, ImageTypes.Intensities),  # Uncertainty Stage 1
        (3, ImageTypes.Intensities),  # Features Stage 1
        (4, ImageTypes.Labels),  # Labels Stage 1
        (5, ImageTypes.Intensities),  # Input Stage 1
        (6, ImageTypes.Intensities),  # Probabilities Stage 2
        (7, ImageTypes.Labels),  # Simple Segmentation Stage 2
        (8, ImageTypes.Intensities),  # Uncertainty Stage 2
        (9, ImageTypes.Intensities),  # Features Stage 2
        (10, ImageTypes.Labels),  # Labels Stage 2
        (11, ImageTypes.Intensities),  # Input Stage 2
        (12, ImageTypes.Intensities),  # Probabilities All Stages
    ],
)
def test_autocontext(autocontext_workflow: AutocontextTwoStage, export_source, expected_semantics):
    op_data_export = autocontext_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(export_source)
    export_slot_meta = op_data_export.ImageToExport[0].meta
    default_is_expected = expected_semantics == ImageTypes.Intensities

    assert (
        "data_semantics" in export_slot_meta or default_is_expected
    ), "interpolation order meta only allowed to be absent if default interpolation is appropriate"
    if "data_semantics" in export_slot_meta:
        assert export_slot_meta.data_semantics == expected_semantics


@pytest.fixture(params=["predictions", "labels"])
def oc_workflow(request, object_classification_from_predictions_ilp_2d3c, object_classification_from_labels_ilp_2d3c):
    project = (
        object_classification_from_predictions_ilp_2d3c
        if request.param == "predictions"
        else object_classification_from_labels_ilp_2d3c
    )
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(project))
    return shell.projectManager.workflow


@pytest.mark.parametrize("export_source", ObjectClassificationWorkflowPrediction.ExportNames)
def test_object_classification(oc_workflow, export_source):
    """
    All oc outputs should be treated as labels since they should always correspond to the
    binary/label object image used as input for the workflow.
    """
    op_data_export = oc_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(export_source)
    export_slot_meta = op_data_export.ImageToExport[0].meta

    assert "data_semantics" in export_slot_meta
    if "data_semantics" in export_slot_meta:
        assert export_slot_meta.data_semantics == ImageTypes.Labels


@pytest.fixture
def mc_workflow(multicut_ilp_3d1c):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(multicut_ilp_3d1c))
    return shell.projectManager.workflow


def test_multicut(mc_workflow):
    op_data_export = mc_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(0)  # there's only Multicut Segmentation
    export_slot_meta = op_data_export.ImageToExport[0].meta

    assert "data_semantics" in export_slot_meta
    assert export_slot_meta.data_semantics == ImageTypes.Labels


@pytest.fixture
def tracking_learning_workflow(tracking_with_learning_from_predictions_ilp_5t2d):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(tracking_with_learning_from_predictions_ilp_5t2d))
    return shell.projectManager.workflow


@pytest.mark.parametrize("export_source", range(3))  # ["Tracking-Result", "Merger-Result", "Object-Identities"]
def test_structured_tracking(tracking_learning_workflow, export_source):
    op_data_export = tracking_learning_workflow.dataExportTrackingApplet.topLevelOperator
    op_data_export.SelectedExportSource.setValue(export_source)
    op_data_export.InputSelection.setValue(export_source)
    export_slot_meta = op_data_export.ImageToExport[0].meta

    assert "data_semantics" in export_slot_meta
    assert export_slot_meta.data_semantics == ImageTypes.Labels


@pytest.fixture
def cell_density_counting_workflow(cell_density_counting_ilp_2d3c):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(cell_density_counting_ilp_2d3c))
    return shell.projectManager.workflow


def test_cell_density_counting(cell_density_counting_workflow: CountingWorkflow):
    op_data_export = cell_density_counting_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(0)  # only has Probabilities
    export_slot_meta = op_data_export.ImageToExport[0].meta

    assert "data_semantics" not in export_slot_meta or export_slot_meta.data_semantics == ImageTypes.Intensities
