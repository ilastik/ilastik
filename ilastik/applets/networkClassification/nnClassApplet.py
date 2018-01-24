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
#          http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.standardApplet import StandardApplet
from .opNNclass import OpNNClassification
from .nnClassSerializer import NNClassificationSerializer


class NNClassApplet(StandardApplet):

    def __init__( self, workflow, projectFileGroupName ):
        # self._topLevelOperator = OpNNClassification(parent=workflow)
        
        # def on_classifier_changed(slot, roi):
        #     if self._topLevelOperator.classifier_cache.Output.ready() and \
        #        self._topLevelOperator.classifier_cache.fixAtCurrent.value is True and \
        #        self._topLevelOperator.classifier_cache.Output.value is None:
        #         # When the classifier is deleted (e.g. because the number of features has changed,
        #         #  then notify the workflow. (Export applet should be disabled.)
        #         self.appletStateUpdateRequested()
        # self._topLevelOperator.classifier_cache.Output.notifyDirty( on_classifier_changed )

        super(NNClassApplet, self).__init__( "NN Classification", workflow=workflow  )

        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [NNClassificationSerializer(self.topLevelOperator, projectFileGroupName)]   # Legacy (v0.5) importer


        self._gui = None
        
        self.predictionSerializer = self._serializableItems[0]


    @property
    def broadcastingSlots( self ):
        return []

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        from .nnClassGui import NNClassGui
        return NNClassGui

    @property
    def singleLaneOperatorClass( self ):
        return OpNNClassification