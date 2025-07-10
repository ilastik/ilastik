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
from lazyflow.graph import InputSlot, Operator, OutputSlot


class OpLabelBase(Operator):
    """Minimal interface for Operators that take an input volume and produce a
    consecutive labeling as an output volume"""

    Input = InputSlot()
    """Volume to (re)label, up to 5D"""

    CachedOutput = OutputSlot()
    """Cached label image - internally always whole time slices are stored
    Axistags and shape are the same as on the Input, dtype is an integer
    datatype.
    This slot extends the ROI to the full xyz volume (c and t are unaffected)
    and computes the labeling for the whole volume. As long as the input does
    not get dirty, subsequent requests to this slot guarantee consistent
    labelings.
    """

    CleanBlocks = OutputSlot()
    """Expose for Cache serialization, slicings for clean blocks stored in the cache"""
