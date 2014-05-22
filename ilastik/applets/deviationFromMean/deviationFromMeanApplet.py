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
from opDeviationFromMean import OpDeviationFromMean
from deviationFromMeanSerializer import DeviationFromMeanSerializer

class DeviationFromMeanApplet( StandardApplet ):
    """
    This applet serves as an example multi-image-lane applet.
    The GUI is not aware of multiple image lanes (it is written as if the applet were single-image only).
    The top-level operator is explicitly multi-image (it is not wrapped in an operatorwrapper).
    """
    def __init__( self, workflow, projectFileGroupName ):
        # Multi-image operator
        self._topLevelOperator = OpDeviationFromMean(parent=workflow)
        
        # Base class
        super(DeviationFromMeanApplet, self).__init__( "Deviation From Mean", workflow )
        self._serializableItems = [ DeviationFromMeanSerializer( self._topLevelOperator, projectFileGroupName ) ]
            
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def singleLaneGuiClass(self):
        from deviationFromMeanGui import DeviationFromMeanGui
        return DeviationFromMeanGui

    @property
    def dataSerializers(self):
        return self._serializableItems


