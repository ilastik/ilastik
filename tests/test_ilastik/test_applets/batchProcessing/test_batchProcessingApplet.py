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
from unittest.mock import Mock

import pytest

from ilastik.applets.batchProcessing.batchProcessingApplet import BatchProcessingApplet
from ilastik.applets.dataSelection.opDataSelection import OpMultiLaneDataSelectionGroup


@pytest.fixture
def dataselectionApplet():
    dsa = Mock()
    dsa.num_lanes = 3  # required by BatchProcessingApplet.export_dataset
    dsa.topLevelOperator = Mock(spec=OpMultiLaneDataSelectionGroup)
    return dsa


@pytest.fixture
def batchProcessingApplet(dataselectionApplet):
    bpa = BatchProcessingApplet(
        workflow=Mock(), title="test", dataSelectionApplet=dataselectionApplet, dataExportApplet=Mock()
    )
    return bpa


def test_BatchProcessingCallsCustomizationHooks(batchProcessingApplet):
    """
    Make sure the customizationhooks
    * `prepare_for_entire_export`
    * `prepare_lane_for_export`
    * `post_process_lane_export`
    * `post_process_entire_export`

    see `ilastik.applets.dataExport.DataExportApplet.prepare_for_entire_export`
    """
    dataExportApplet = batchProcessingApplet.dataExportApplet

    dataExportApplet.prepare_for_entire_export.x.blah2.assert_not_called()
    dataExportApplet.post_process_entire_export.assert_not_called()
    dataExportApplet.prepare_lane_for_export.assert_not_called()
    dataExportApplet.post_process_lane_export.assert_not_called()

    export_function = Mock()

    lane_configs = list(range(42))

    batchProcessingApplet.run_export(lane_configs=lane_configs, export_to_array=False, export_function=export_function)

    dataExportApplet.prepare_for_entire_export.assert_called_once()
    dataExportApplet.post_process_entire_export.assert_called_once()
    assert dataExportApplet.prepare_lane_for_export.call_count == len(lane_configs)
    assert dataExportApplet.post_process_lane_export.call_count == len(lane_configs)


def test_BatchProcessingCallsPostProcessOnException(batchProcessingApplet):
    """
    Make sure the customizationhooks `post_process_entire_export` is called even
    in case of errors.
    """
    dataExportApplet = batchProcessingApplet.dataExportApplet

    dataExportApplet.prepare_for_entire_export.x.blah2.assert_not_called()
    dataExportApplet.post_process_entire_export.assert_not_called()
    dataExportApplet.prepare_lane_for_export.assert_not_called()
    dataExportApplet.post_process_lane_export.assert_not_called()

    export_function = Mock()
    export_function.side_effect = Exception("Who knows")

    lane_configs = [0]

    with pytest.raises(Exception):
        batchProcessingApplet.run_export(
            lane_configs=lane_configs, export_to_array=False, export_function=export_function
        )

    dataExportApplet.prepare_for_entire_export.assert_called_once()
    dataExportApplet.post_process_entire_export.assert_called_once()
    dataExportApplet.prepare_lane_for_export.assert_called_once()
    dataExportApplet.post_process_lane_export.assert_not_called()
