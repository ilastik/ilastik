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
#		   http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.standardApplet import StandardApplet

from .slicGui import SlicGui
from .opSlic import OpSlicCached

class SlicApplet(StandardApplet):
    def __init__(self, workflow):
        super(SlicApplet, self).__init__("SLIC Applet", workflow)

    @property
    def singleLaneGuiClass(self):
        return SlicGui

    @property
    def singleLaneOperatorClass(self):
        return OpSlicCached

    @property
    def broadcastingSlots(self):
        return ['NumSegments', 'Compactness', 'MaxIter']
