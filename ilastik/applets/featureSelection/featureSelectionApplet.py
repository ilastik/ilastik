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
#          http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.standardApplet import StandardApplet
from .opFeatureSelection import OpFeatureSelection
from .featureSelectionSerializer import FeatureSelectionSerializer, Ilastik05FeatureSelectionDeserializer


class FeatureSelectionApplet(StandardApplet):
    """
    This applet allows the user to select sets of input data,
    which are provided as outputs in the corresponding top-level applet operator.
    """

    def __init__(self, workflow, guiName, projectFileGroupName):
        super(FeatureSelectionApplet, self).__init__(guiName, workflow)
        self._serializableItems = [FeatureSelectionSerializer(self.topLevelOperator, projectFileGroupName),
                                   Ilastik05FeatureSelectionDeserializer(self.topLevelOperator)]
        self.busy = False

    @property
    def singleLaneOperatorClass(self):
        return OpFeatureSelection

    @property
    def broadcastingSlots(self):
        return ['Scales', 'ComputeIn2d', 'FeatureIds', 'SelectionMatrix']

    @property
    def singleLaneGuiClass(self):
        from .featureSelectionGui import FeatureSelectionGui
        return FeatureSelectionGui

#    def createSingleLaneGui( self , laneIndex):
#        from featureSelectionGui import FeatureSelectionGui
#        opFeat = self.topLevelOperator.getLane(laneIndex)
#        gui = FeatureSelectionGui( opFeat, self )
#        return gui

    @property
    def dataSerializers(self):
        return self._serializableItems
