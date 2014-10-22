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

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Oct 15, 2014 15:27:45 EDT$"



from ilastik.applets.base.standardApplet import StandardApplet

from ilastik.applets.nanshe.dictionaryLearning.opNansheGenerateDictionary import OpNansheGenerateDictionaryCached
from ilastik.applets.nanshe.dictionaryLearning.nansheDictionaryLearningSerializer import NansheDictionaryLearningSerializer

class NansheDictionaryLearningApplet( StandardApplet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(NansheDictionaryLearningApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ NansheDictionaryLearningSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpNansheGenerateDictionaryCached

    @property
    def broadcastingSlots(self):
        return ["K", "Gamma1", "Gamma2", "NumThreads", "Batchsize", "NumIter", "Lambda1", "Lambda2", "PosAlpha", "PosD", \
                "Clean", "Mode", "ModeD"]
    
    @property
    def singleLaneGuiClass(self):
        from ilastik.applets.nanshe.dictionaryLearning.nansheDictionaryLearningGui import NansheDictionaryLearningGui
        return NansheDictionaryLearningGui

    @property
    def dataSerializers(self):
        return self._serializableItems
