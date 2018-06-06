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
from __future__ import absolute_import
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

class NNClassificationDataExportApplet(DataExportApplet):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for Neural Network predictions.
    """

    def __init__(self, workflow, title, isBatch=False):
    # Base class init
        super(NNClassificationDataExportApplet, self).__init__(workflow, title, isBatch)

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from .nnClassificationDataExportGui import NNClassificationDataExportGui
            self._gui = NNClassificationDataExportGui(self, self.topLevelOperator)
        return self._gui



