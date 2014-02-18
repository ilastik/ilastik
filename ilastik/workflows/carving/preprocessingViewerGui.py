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

import numpy

from PyQt4.QtGui import QColor

from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.layer import ColortableLayer

#ilastik
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

class PreprocessingViewerGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super(PreprocessingViewerGui, self).__init__(*args, **kwargs)
    
    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView
        
        # Supervoxels
        watershedSlot = opLane.WatershedImage
        if watershedSlot.ready():
            colortable = []
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            watershedLayer = ColortableLayer(LazyflowSource(watershedSlot), colortable)
            watershedLayer.name = "Watershed"
            watershedLayer.visible = False
            watershedLayer.opacity = 1.0
            layers.append(watershedLayer)

        ''' FIXME: disabled for 0.6 release
        wsSourceSlot = opLane.WatershedSourceImage
        if wsSourceSlot.ready():
            wsSourceLayer = self.createStandardLayerFromSlot( wsSourceSlot )
            wsSourceLayer.name = "Watershed Source"
            wsSourceLayer.visible = False
            wsSourceLayer.opacity = 1.0
            layers.append( wsSourceLayer )
        '''

        filteredSlot = opLane.FilteredImage
        if filteredSlot.ready():
            filteredLayer = self.createStandardLayerFromSlot( filteredSlot )
            filteredLayer.name = "Filtered Data"
            filteredLayer.visible = False
            filteredLayer.opacity = 1.0
            layers.append( filteredLayer )

        inputSlot = opLane.InputData
        if inputSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputSlot )
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append( inputLayer )

        ''' FIXME: disabled for 0.6 release
        rawSlot = opLane.RawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append( rawLayer )
        '''

        return layers 
