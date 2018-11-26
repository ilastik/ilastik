from __future__ import absolute_import
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
from ilastik.applets.base.applet import Applet
from .opCNNModelSelection import OpCNNModelSelection
from .cnnModelSelectionSerializer import CNNModelSelectionSerializer

class CNNModelSelectionApplet(Applet):
    """
    """
    def __init__(self, workflow, title, projectFileGroupName):
        self._topLevelOperator = OpCNNModelSelection(parent=workflow)

        super(CNNModelSelectionApplet, self).__init__("Model Selection")

        self._serializableItems = [CNNModelSelectionSerializer(self.topLevelOperator, projectFileGroupName)]

        self._gui = None

    def getMultiLaneGui(self):
        if self._gui is None:
            from .cnnModelSelectionGui import CNNModelSelectionGui
            self._gui = CNNModelSelectionGui(self,
                                             self.topLevelOperator,
                                             None,
                                             'Introduction text')
        return self._gui


    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        from .cnnModelSelectionGui import CNNModelSelectionGui
        return CNNModelSelectionGui
