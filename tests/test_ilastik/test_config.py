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


def test_runtime_cfg_skip_pixel_size_check_default_is_false():
    """By default pixel size check should NOT be skipped."""
    cfg = RuntimeCfg()
    assert cfg.skip_pixel_size_check is False
