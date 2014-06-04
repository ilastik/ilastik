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
from ilastik.workflows.carving.carvingApplet import CarvingApplet
from ilastik.utility import OpMultiLaneWrapper

from opSplitBodyCarving import OpSplitBodyCarving
from splitBodyCarvingSerializer import SplitBodyCarvingSerializer

class SplitBodyCarvingApplet(CarvingApplet):
    
    workflowName = "Split-body Carving"
    
    def __init__(self, workflow, *args, **kwargs):
        self._topLevelOperator = OpMultiLaneWrapper( OpSplitBodyCarving, parent=workflow )
        super(SplitBodyCarvingApplet, self).__init__(workflow, *args, **kwargs)
        self._serializers = None
        
    @property
    def dataSerializers(self):
        if self._serializers is None:
            self._serializers = [ SplitBodyCarvingSerializer(self.topLevelOperator, self._projectFileGroupName) ]
        return self._serializers
    
    def createSingleLaneGui(self, laneIndex):
        """
        Override from base class.
        """
        from splitBodyCarvingGui import SplitBodyCarvingGui
        # Get a single-lane view of the top-level operator
        topLevelOperatorView = self.topLevelOperator.getLane(laneIndex)

        gui = SplitBodyCarvingGui( self, topLevelOperatorView )

        gui.minLabelNumber = 2
        gui.maxLabelNumber = 2

        return gui
