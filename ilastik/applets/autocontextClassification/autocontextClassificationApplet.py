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
from opAutocontextClassification import OpAutocontextClassification
from autocontextClassificationSerializer import AutocontextClassificationSerializer

class AutocontextClassificationApplet( StandardApplet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, workflow, projectFileGroupName ):
        self._topLevelOperator = OpAutocontextClassification( parent=workflow )
        super(AutocontextClassificationApplet, self).__init__( "Training" )

        # GUI needs access to the serializer to enable/disable prediction storage
        self.predictionSerializer = AutocontextClassificationSerializer(self._topLevelOperator, projectFileGroupName)
        self._serializableItems = [ self.predictionSerializer ]
        
        self._gui = None        

        # FIXME: For now, we can directly connect the progress signal from the classifier training operator
        #  directly to the applet's overall progress signal, because it's the only thing we report progress for at the moment.
        # If we start reporting progress for multiple tasks that might occur simulatneously,
        #  we'll need to aggregate the progress updates.
        #self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal.emit)
    
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        from autocontextClassificationGui import AutocontextClassificationGui
        singleImageOperator = self.topLevelOperator.getLane(imageLaneIndex)
        return AutocontextClassificationGui( singleImageOperator, self.shellRequestSignal, self.predictionSerializer )        
