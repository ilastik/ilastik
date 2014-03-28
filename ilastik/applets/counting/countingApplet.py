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

from opCounting import OpCounting
from countingSerializer import CountingSerializer

class CountingApplet(StandardApplet):
    def __init__(self,
                 name="Counting",
                 workflow=None,
                 projectFileGroupName="Counting"):
        self._topLevelOperator = OpCounting(parent=workflow)
        super(CountingApplet, self).__init__(name=name, workflow=workflow)

        #self._serializableItems = [
        #    ObjectClassificationSerializer(projectFileGroupName,
        #                                   self.topLevelOperator)]
        self._serializableItems = [CountingSerializer(self._topLevelOperator, projectFileGroupName)]   # Legacy (v0.5) importer
        self.predictionSerializer = self._serializableItems[0]

        self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal.emit)

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        from countingGui import CountingGui
        return CountingGui
