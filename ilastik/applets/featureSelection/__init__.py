###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
from typing import Callable, Iterable, Union

from ilastik.applets.base.applet import DatasetConstraintError

_SCALES = Iterable[Union[int, float]]


class FeatureSelectionConstraintError(DatasetConstraintError):
    def __init__(
        self,
        appletName: str,
        invalid_scales: _SCALES,
        invalid_z_scales: _SCALES,
        fixing_dialogs=Iterable[Callable],
    ):
        """
        Args:
          appletName: applet where the exception is happening
          invalid_scales: list of scales that are not compatible in the x-y plane
          invalid_z_scales: list of scales that are not compatible in the z-plane
          fixing_dialogs: list of functions to show dialogs which can alleviate the dataset constraint.
        """
        message = "\nSome of your selected feature scales are too large for your dataset.\n"
        if invalid_scales:
            message += f"Reduce or remove these scales:\n{invalid_scales}\n\n"

        if invalid_z_scales:
            message += f"Reduce, remove or switch to 2D computation for these scales:\n{invalid_z_scales}\n\n"

        message += "Alternatively use another dataset."

        super().__init__(appletName, message)
        self.fixing_dialogs = fixing_dialogs
        self.invalid_scales = invalid_scales
        self.invalid_z_scales = invalid_z_scales

    def __str__(self):
        return f"Constraint of '{self.appletName}' applet was violated: {self.message}"


from .featureSelectionApplet import FeatureSelectionApplet
