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

from opNanshePreprocessing import OpNanshePreprocessing
from ilastik.applets.nanshe.preprocessing.nanshePreprocessingSerializer import NanshePreprocessingSerializer

class NanshePreprocessingApplet( StandardApplet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(NanshePreprocessingApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ NanshePreprocessingSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpNanshePreprocessing

    @property
    def broadcastingSlots(self):
        return ["ToRemoveZeroedLines", "ErosionShape", "DilationShape", \
        "ToExtractF0", "HalfWindowSize", "WhichQuantile", \
        "TemporalSmoothingGaussianFilterStdev", "SpatialSmoothingGaussianFilterStdev", \
        "BiasEnabled", "Bias", "ToWaveletTransform", "Scale"]
    
    @property
    def singleLaneGuiClass(self):
        from ilastik.applets.nanshe.preprocessing.nanshePreprocessingGui import NanshePreprocessingGui
        return NanshePreprocessingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
