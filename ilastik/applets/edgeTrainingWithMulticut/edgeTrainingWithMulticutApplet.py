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
#           http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.standardApplet import StandardApplet

from ilastik.applets.edgeTraining.edgeTrainingSerializer import EdgeTrainingSerializer
from ilastik.applets.multicut.multicutSerializer import MulticutSerializer

from opEdgeTrainingWithMulticut import OpEdgeTrainingWithMulticut

class EdgeTrainingWithMulticutApplet( StandardApplet ):
    """
    A composite applet that merely combines the functionality of the
    EdgeTraining and the Multicut applet, so they can share the same GUI.
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        self._topLevelOperator = OpEdgeTrainingWithMulticut( parent=workflow )
        super(EdgeTrainingWithMulticutApplet, self).__init__( guiName, workflow )
        
        # No need for a special serializer class -- just create instances of the EdgeTraining and Multicut serializers
        self._serializableItems = [ EdgeTrainingSerializer(self.topLevelOperator, projectFileGroupName),
                                    MulticutSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def singleLaneGuiClass(self):
        from edgeTrainingWithMulticutGui import EdgeTrainingWithMulticutGui
        return EdgeTrainingWithMulticutGui

    @property
    def dataSerializers(self):
        return self._serializableItems
