# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from ilastik.applets.base.appletSerializer import AppletSerializer

class PredictionViewerSerializer(AppletSerializer):

    def __init__(self, topLevelOperator, predictionGroupName):
        super(PredictionViewerSerializer, self).__init__("PredictionViewer")
        self._predictionGroupName = predictionGroupName
        self._topLevelOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5File, projectFilePath):
        pass
    
    def deserializeFromHdf5(self, hdf5File, projectFilePath):
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
    
    

    