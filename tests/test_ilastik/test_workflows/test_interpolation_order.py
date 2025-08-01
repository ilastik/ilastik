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
    PixelClassificationWorkflow,
    AutocontextTwoStage,
    ObjectClassificationWorkflowPrediction,
    CountingWorkflow,
)
from lazyflow.operators.opResize import OpResize
from lazyflow.utility.io_util.write_ome_zarr import INTERPOLATION_ORDER_DEFAULT

"""
Ensure interpolation order is appropriate in all workflows for all available export sources.
"""


@pytest.fixture
def pc_workflow(pixel_classification_ilp_2d3c):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(pixel_classification_ilp_2d3c))
    return shell.projectManager.workflow


@pytest.mark.parametrize(
    "export_source,expected_order",
    [
        (PixelClassificationWorkflow.ExportNames.PROBABILITIES, OpResize.Interpolation.LINEAR),
        (PixelClassificationWorkflow.ExportNames.SIMPLE_SEGMENTATION, OpResize.Interpolation.NEAREST),
        (PixelClassificationWorkflow.ExportNames.UNCERTAINTY, OpResize.Interpolation.LINEAR),
        (PixelClassificationWorkflow.ExportNames.FEATURES, OpResize.Interpolation.LINEAR),
        (PixelClassificationWorkflow.ExportNames.LABELS, OpResize.Interpolation.NEAREST),
    ],
)
def test_interpolation_order_pc(pc_workflow, export_source, expected_order):
    op_data_export = pc_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(export_source)
    export_slot_meta = op_data_export.ImageToExport[0].meta
    default_is_expected = expected_order == INTERPOLATION_ORDER_DEFAULT

    assert (
        "appropriate_interpolation_order" in export_slot_meta or default_is_expected
    ), "interpolation order meta only allowed to be absent if default interpolation is appropriate"
    if "appropriate_interpolation_order" in export_slot_meta:
        assert export_slot_meta.appropriate_interpolation_order == expected_order


@pytest.fixture
def autocontext_workflow(autocontext_ilp_2d3c):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(autocontext_ilp_2d3c))
    return shell.projectManager.workflow


@pytest.mark.parametrize(
    "export_source,expected_order",
    [
        (0, OpResize.Interpolation.LINEAR),  # Probabilities Stage 1
        (1, OpResize.Interpolation.NEAREST),  # Simple Segmentation Stage 1
        (2, OpResize.Interpolation.LINEAR),  # Uncertainty Stage 1
        (3, OpResize.Interpolation.LINEAR),  # Features Stage 1
        (4, OpResize.Interpolation.NEAREST),  # Labels Stage 1
        (5, OpResize.Interpolation.LINEAR),  # Input Stage 1
        (6, OpResize.Interpolation.LINEAR),  # Probabilities Stage 2
        (7, OpResize.Interpolation.NEAREST),  # Simple Segmentation Stage 2
        (8, OpResize.Interpolation.LINEAR),  # Uncertainty Stage 2
        (9, OpResize.Interpolation.LINEAR),  # Features Stage 2
        (10, OpResize.Interpolation.NEAREST),  # Labels Stage 2
        (11, OpResize.Interpolation.LINEAR),  # Input Stage 2
        (12, OpResize.Interpolation.LINEAR),  # Probabilities All Stages
    ],
)
def test_interpolation_order_autocontext(autocontext_workflow: AutocontextTwoStage, export_source, expected_order):
    op_data_export = autocontext_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(export_source)
    export_slot_meta = op_data_export.ImageToExport[0].meta
    default_is_expected = expected_order == INTERPOLATION_ORDER_DEFAULT

    assert (
        "appropriate_interpolation_order" in export_slot_meta or default_is_expected
    ), "interpolation order meta only allowed to be absent if default interpolation is appropriate"
    if "appropriate_interpolation_order" in export_slot_meta:
        assert export_slot_meta.appropriate_interpolation_order == expected_order


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


@pytest.mark.parametrize(
    "export_source,expected_order",
    [
        (ObjectClassificationWorkflowPrediction.ExportNames.OBJECT_PREDICTIONS, OpResize.Interpolation.NEAREST),
        (ObjectClassificationWorkflowPrediction.ExportNames.OBJECT_PROBABILITIES, OpResize.Interpolation.LINEAR),
        (
            ObjectClassificationWorkflowPrediction.ExportNames.BLOCKWISE_OBJECT_PREDICTIONS,
            OpResize.Interpolation.NEAREST,
        ),
        (
            ObjectClassificationWorkflowPrediction.ExportNames.BLOCKWISE_OBJECT_PROBABILITIES,
            OpResize.Interpolation.LINEAR,
        ),
        (ObjectClassificationWorkflowPrediction.ExportNames.OBJECT_IDENTITIES, OpResize.Interpolation.NEAREST),
    ],
)
def test_interpolation_order_oc(oc_workflow, export_source, expected_order):
    op_data_export = oc_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(export_source)
    export_slot_meta = op_data_export.ImageToExport[0].meta
    default_is_expected = expected_order == INTERPOLATION_ORDER_DEFAULT

    assert (
        "appropriate_interpolation_order" in export_slot_meta or default_is_expected
    ), "interpolation order meta only allowed to be absent if default interpolation is appropriate"
    if "appropriate_interpolation_order" in export_slot_meta:
        assert export_slot_meta.appropriate_interpolation_order == expected_order


@pytest.fixture
def mc_workflow(multicut_ilp_3d1c):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(multicut_ilp_3d1c))
    return shell.projectManager.workflow


def test_interpolation_order_multicut(mc_workflow):
    op_data_export = mc_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(0)  # there's only Multicut Segmentation
    export_slot_meta = op_data_export.ImageToExport[0].meta

    assert "appropriate_interpolation_order" in export_slot_meta
    assert export_slot_meta.appropriate_interpolation_order == OpResize.Interpolation.NEAREST


@pytest.fixture
def tracking_learning_workflow(tracking_with_learning_from_predictions_ilp_5t2d):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(tracking_with_learning_from_predictions_ilp_5t2d))
    return shell.projectManager.workflow


@pytest.mark.parametrize("export_source", range(3))  # ["Tracking-Result", "Merger-Result", "Object-Identities"]
def test_interpolation_order_structured_tracking(tracking_learning_workflow, export_source):
    op_data_export = tracking_learning_workflow.dataExportTrackingApplet.topLevelOperator
    op_data_export.SelectedExportSource.setValue(export_source)
    op_data_export.InputSelection.setValue(export_source)
    export_slot_meta = op_data_export.ImageToExport[0].meta

    assert "appropriate_interpolation_order" in export_slot_meta
    assert export_slot_meta.appropriate_interpolation_order == OpResize.Interpolation.NEAREST


@pytest.fixture
def cell_density_counting_workflow(cell_density_counting_ilp_2d3c):
    shell = HeadlessShell()
    shell.openProjectFile(projectFilePath=str(cell_density_counting_ilp_2d3c))
    return shell.projectManager.workflow


def test_interpolation_order_cell_density_counting(cell_density_counting_workflow: CountingWorkflow):
    op_data_export = cell_density_counting_workflow.dataExportApplet.topLevelOperator
    op_data_export.InputSelection.setValue(0)  # only has Probabilities
    export_slot_meta = op_data_export.ImageToExport[0].meta

    assert (
        "appropriate_interpolation_order" not in export_slot_meta
        or export_slot_meta.appropriate_interpolation_order == OpResize.Interpolation.LINEAR
    )
