###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2019, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################

from typing import Sequence

from PyQt5.QtCore import QRect


def roi2rect(start: Sequence[int], stop: Sequence[int], axes: Sequence[str] = ("x", "y")) -> QRect:
    """Convert ROI to QRect, accounting for the specified axis order.

    ROI elements are swapped if necessary.

    Args:
        start: ROI start.
        stop: ROI stop.
        axes: Sequence of axis names that includes ``x`` and ``y``.

    Returns:
        QRect with non-negative width and height.

    Raises:
        ValueError: Invalid ROI, missing axes or invalid ROI/axes combination.

    Examples:
        >>> roi2rect([0, 2, 3], [0, 12, 103], ["spam", "y", "x"])
        PyQt5.QtCore.QRect(3, 2, 100, 10)
        >>> roi2rect([0, 12, 103], [0, 2, 3], ["spam", "y", "x"])
        PyQt5.QtCore.QRect(3, 2, 100, 10)
        >>> roi2rect([0, 2, 3], [0, 12, 103], ["spam", "y"])  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
          ...
        ValueError
        >>> roi2rect([1, 2], [8, 9])
        PyQt5.QtCore.QRect(1, 2, 7, 7)
    """
    if len(start) != len(stop) != len(axes):
        raise ValueError(f"axes {axes}, start {start}, stop {stop} have different lengths")

    try:
        ix = axes.index("x")
        iy = axes.index("y")
    except ValueError:
        raise ValueError(f"'x' or 'y' not found in axes {axes}")

    try:
        left = min(start[ix], stop[ix])
        top = min(start[iy], stop[iy])
        width = max(start[ix], stop[ix]) - left
        height = max(start[iy], stop[iy]) - top
        return QRect(left, top, width, height)
    except ValueError:
        raise ValueError(f"invalid start {start} or stop {stop} for axes {axes}")
