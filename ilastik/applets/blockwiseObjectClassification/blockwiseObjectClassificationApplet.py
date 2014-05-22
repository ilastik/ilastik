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

from opBlockwiseObjectClassification import OpBlockwiseObjectClassification
from blockwiseObjectClassificationSerializer import BlockwiseObjectClassificationSerializer

class BlockwiseObjectClassificationApplet(StandardApplet):
    def __init__(self,
                 workflow=None,
                 name="Blockwise Object Classification",
                 projectFileGroupName="BlockwiseObjectClassification"):
        super(BlockwiseObjectClassificationApplet, self).__init__(name=name, workflow=workflow)

        self._serializableItems = \
        [ BlockwiseObjectClassificationSerializer(projectFileGroupName, self.topLevelOperator) ]

    @property
    def singleLaneOperatorClass(self):
        return OpBlockwiseObjectClassification

    @property
    def broadcastingSlots(self):
        return ['Classifier', 'LabelsCount', 'SelectedFeatures', 'BlockShape3dDict', 'HaloPadding3dDict']
    
    @property
    def singleLaneGuiClass(self):
        from blockwiseObjectClassificationGui import BlockwiseObjectClassificationGui
        return BlockwiseObjectClassificationGui

    @property
    def dataSerializers(self):
        return self._serializableItems
