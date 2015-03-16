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

print "----- SLT -----> in SubModelSelectionApplet" ###xxx

from ilastik.applets.base.standardApplet import StandardApplet

print " ==== SLT ===1==> before import opSubModelSelection" ###xxx
from opSubModelSelection import OpSubModelSelection





print " ==== SLT ===2==> before import subModelSelectionSerializer" ###xxx
from subModelSelectionSerializer import SubModelSelectionSerializer
print " ==== SLT ===3==> after import subModelSelectionSerializer" ###xxx

class SubModelSelectionApplet( StandardApplet ):
    print " ==== SLT ===1==> in SubModelSelectionApplet" ###xxx
    """
    This is a simple applet facilitating sub model selection
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        print " ==== SLT ===1==> in __init__ SubModelSelectionApplet" ###xxx
        super(SubModelSelectionApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ SubModelSelectionSerializer(self.topLevelOperator, projectFileGroupName) ]
        
        print " ==== SLT ===1==> end __init__ SubModelSelectionApplet" ###xxx

    @property
    def singleLaneOperatorClass(self):
        return OpSubModelSelection

    @property
    def broadcastingSlots(self):
        return ['MinValueT', 'MaxValueT','MinValueX', 'MaxValueX','MinValueY', 'MaxValueY','MinValueZ', 'MaxValueZ']
    
    @property
    def singleLaneGuiClass(self):
        from subModelSelectionGui import SubModelSelectionGui
        return SubModelSelectionGui

    @property
    def dataSerializers(self):
        return self._serializableItems
