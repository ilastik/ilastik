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
        # self.__topLevelOperator = OpNNClassification(parent=workflow)
        
        super(NNClassApplet, self).__init__( "NN Classification", workflow=workflow)

        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [NNClassificationSerializer(self.topLevelOperator, projectFileGroupName)]   # Legacy (v0.5) importer


        self._gui = None
        
        self.predictionSerializer = self._serializableItems[0]


    @property
    def broadcastingSlots(self):
        return ['Classifier']

    @property
    def dataSerializers(self):
        return self._serializableItems


    # @property
    # def topLevelOperator(self):
    #     return self.__topLevelOperator

    @property
    def singleLaneGuiClass(self):
        from .nnClassGui import NNClassGui
        return NNClassGui

    # def getMultiLaneGui(self):
    #     if self._gui is None:
    #         from .nnClassGui import NNClassGui
    #         self._gui = NNClassGui( self, self.topLevelOperator )
    #     return self._gui

    @property
    def singleLaneOperatorClass(self):
        return OpNNClassification