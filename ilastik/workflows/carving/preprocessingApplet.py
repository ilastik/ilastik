###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
from ilastik.applets.base.standardApplet import StandardApplet

from .opPreprocessing import OpPreprocessing
from .preprocessingSerializer import PreprocessingSerializer


class PreprocessingApplet(StandardApplet):
    def __init__(self, workflow, title, projectFileGroupName, supportIlastik05Import=False):
        super(PreprocessingApplet, self).__init__(title, workflow)

        self._workflow = workflow

        self._serializableItems = [PreprocessingSerializer(self.topLevelOperator, projectFileGroupName)]

        self._gui = None
        self._title = title

    def anyLaneReady(self):
        return any([opPre.cachedResult[0] is not None for opPre in self.topLevelOperator.innerOperators])

    def createSingleLaneGui(self, laneIndex):
        from .preprocessingGui import PreprocessingGui

        opPre = self.topLevelOperator.getLane(laneIndex)
        self._gui = PreprocessingGui(self, opPre)

        if opPre.deserialized:
            self._gui.setWriteprotect()

        return self._gui

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneOperatorClass(self):
        return OpPreprocessing

    @property
    def broadcastingSlots(self):
        return ["Sigma", "Filter"]
