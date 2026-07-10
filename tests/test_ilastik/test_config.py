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
from ilastik.config import RuntimeCfg


def test_runtime_cfg_defaults():
    """RuntimeCfg should have safe defaults for all fields."""
    cfg = RuntimeCfg()
    assert cfg.tiktorch_executable is None
    assert cfg.preferred_cuda_device_id is None
    assert cfg.skip_pixel_size_check is False


def test_runtime_cfg_skip_pixel_size_check_can_be_set():
    """skip_pixel_size_check should be settable to True."""
    cfg = RuntimeCfg(skip_pixel_size_check=True)
    assert cfg.skip_pixel_size_check is True



def test_skip_pixel_size_check_prevents_lane_inspection():
    """
    When runtime_cfg.skip_pixel_size_check is True, _check_pixel_size_mismatch
    should return immediately without inspecting any lanes.
    """
    from unittest.mock import MagicMock, patch
    from ilastik.config import runtime_cfg
    from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui

    # Patch runtime_cfg.skip_pixel_size_check to True
    original = runtime_cfg.skip_pixel_size_check
    try:
        runtime_cfg.skip_pixel_size_check = True

        # Create a minimal mock of DataSelectionGui
        gui = MagicMock(spec=DataSelectionGui)
        gui.topLevelOperator = MagicMock()

        # Call the real method on the mock instance
        DataSelectionGui._check_pixel_size_mismatch(gui, 0, 3)

        # If skip is True, getLane should never be called
        gui.topLevelOperator.getLane.assert_not_called()
    finally:
        runtime_cfg.skip_pixel_size_check = original


def test_skip_pixel_size_check_set_when_checkbox_checked():
    """
    When the user checks 'Don't warn me again' in the pixel size mismatch
    dialog, runtime_cfg.skip_pixel_size_check should be set to True,
    preventing future warnings for the rest of the session.
    """
    from unittest.mock import MagicMock, patch
    from ilastik.config import runtime_cfg
    from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui

    original = runtime_cfg.skip_pixel_size_check
    try:
        runtime_cfg.skip_pixel_size_check = False

        gui = MagicMock()
        mock_lane_op = MagicMock()
        mock_slot = MagicMock()
        mock_slot.ready.return_value = True
        mock_lane_op.ImageGroup = [mock_slot, mock_slot]
        mock_lane_op.DatasetRoles.value = ["Raw Data", "Probabilities"]
        gui.topLevelOperator.getLane.return_value = mock_lane_op

        with patch(
            "ilastik.applets.dataSelection.dataSelectionGui.OpDataSelectionGroup.eq_resolution_and_units_xyzt",
            return_value=False,
        ):
            mock_checkbox = MagicMock()
            mock_checkbox.isChecked.return_value = True
            mock_dialog = MagicMock()

            with (
                patch(
                    "ilastik.applets.dataSelection.dataSelectionGui.QMessageBox",
                    return_value=mock_dialog,
                ),
                patch(
                    "ilastik.applets.dataSelection.dataSelectionGui.QCheckBox",
                    return_value=mock_checkbox,
                ),
            ):
                DataSelectionGui._check_pixel_size_mismatch(gui, 0, 0)

        assert runtime_cfg.skip_pixel_size_check is True
    finally:
        runtime_cfg.skip_pixel_size_check = original
