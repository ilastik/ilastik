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
from ilastik.applets.base.appletSerializer import AppletSerializer

class PredictionViewerSerializer(AppletSerializer):

    def __init__(self, topLevelOperator, predictionGroupName):
        super(PredictionViewerSerializer, self).__init__("PredictionViewer")
        self._predictionGroupName = predictionGroupName
        self._topLevelOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5File, projectFilePath):
        pass
    
    def deserializeFromHdf5(self, hdf5File, projectFilePath, headless=False):
        try:
            predictionGroup = hdf5File[self._predictionGroupName]
        except:
            return

        pmapColors = None
        labelNames = None
        try:        
            pmapColors = predictionGroup['PmapColors'].value
            self._topLevelOperator.PmapColors.setValue( list(pmapColors) )
            
        except KeyError:
            pass

        try:        
            labelNames = predictionGroup['LabelNames'].value
            self._topLevelOperator.LabelNames.setValue( list(labelNames) )
        except KeyError:
            pass
    
    

    
