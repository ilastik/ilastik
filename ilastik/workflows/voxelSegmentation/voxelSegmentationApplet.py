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

from .opVoxelSegmentation import OpVoxelSegmentation
from .voxelSegmentationGui import VoxelSegmentationGui
from .voxelSegmentationSerializer import VoxelSegmentationSerializer


class VoxelSegmentationApplet(StandardApplet):

    def __init__(self, workflow, projectFileGroupName):
        self._topLevelOperator = OpVoxelSegmentation(parent=workflow)

        def on_classifier_changed(slot, roi):
            if self._topLevelOperator.classifier_cache.Output.ready() and \
               self._topLevelOperator.classifier_cache.fixAtCurrent.value is True and \
               self._topLevelOperator.classifier_cache.Output.value is None:
                # When the classifier is deleted (e.g. because the number of features has changed,
                #  then notify the workflow. (Export applet should be disabled.)
                self.appletStateUpdateRequested.emit()
        self._topLevelOperator.classifier_cache.Output.notifyDirty(on_classifier_changed)

        super(VoxelSegmentationApplet, self).__init__("Training")
        self._topLevelOperator = OpVoxelSegmentation(parent=workflow)
        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [VoxelSegmentationSerializer(self._topLevelOperator, projectFileGroupName)]  # Default serializer for new projects   # Legacy (v0.5) importer

        self._gui = None

        # GUI needs access to the serializer to enable/disable prediction storage
        self.predictionSerializer = self._serializableItems[0]

        # FIXME: For now, we can directly connect the progress signal from the classifier training operator
        #  directly to the applet's overall progress signal, because it's the only thing we report progress for at the moment.
        # If we start reporting progress for multiple tasks that might occur simulatneously,
        #  we'll need to aggregate the progress updates.
        self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal)

        # super(VoxelSegmentationApplet, self).__init__(workflow, projectFileGroupName)

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        return VoxelSegmentationGui
