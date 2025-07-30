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
from ilastik.workflows import PixelClassificationWorkflow
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
