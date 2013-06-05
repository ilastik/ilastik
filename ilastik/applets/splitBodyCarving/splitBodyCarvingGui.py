import os
from functools import partial
import numpy

from PyQt4.QtGui import QColor

from lazyflow.roi import TinyVector
from lazyflow.utility.jsonConfig import JsonConfigParser, AutoEval

from volumina.layer import ColortableLayer
from volumina.pixelpipeline.datasources import LazyflowSource

from ilastik.workflows.carving.carvingGui import CarvingGui

from opSplitBodyCarving import OpSplitBodyCarving

SplitPointListSchema = {
    "_schema_name" : "split-point-list-schema",
    "_schema_version" : 1.0,
    
    "raveler-label" : int,
    "coordinates" : AutoEval(numpy.array) # xyz
}
SplitPointParser = JsonConfigParser( SplitPointListSchema )

class SplitBodyCarvingGui(CarvingGui):
    
    def __init__(self, topLevelOperatorView):
        drawerUiPath = os.path.join( os.path.split(__file__)[0], 'splitBodyCarvingDrawer.ui' )
        super( SplitBodyCarvingGui, self ).__init__(topLevelOperatorView, drawerUiPath=drawerUiPath)
        
    def labelingContextMenu(self, names, op, position5d):                
        pos = TinyVector(position5d)
        sample_roi = (pos, pos+1)
        ravelerLabelSample = self.topLevelOperatorView.RavelerLabels(*sample_roi).wait()
        ravelerLabel = ravelerLabelSample[0,0,0,0,0]
        
        menu = super( SplitBodyCarvingGui, self ).labelingContextMenu(names, op, position5d)
        menu.addSeparator()
        highlightAction = menu.addAction( "Highlight Raveler Object {}".format( ravelerLabel ) )
        highlightAction.triggered.connect( partial(self.topLevelOperatorView.CurrentRavelerLabel.setValue, ravelerLabel ) )

        # Auto-seed also auto-highlights
        autoSeedAction = menu.addAction( "Auto-seed background for Raveler Object {}".format( ravelerLabel ) )
        autoSeedAction.triggered.connect( partial(OpSplitBodyCarving.autoSeedBackground, self.topLevelOperatorView, ravelerLabel ) )
        autoSeedAction.triggered.connect( partial(self.topLevelOperatorView.CurrentRavelerLabel.setValue, ravelerLabel ) )

        return menu

    # Show list, sorted by raveler label (or possibly by z-plane?)
    # When user pressed "next":
    # - Highlight raveler object
    # - Show split-point annotation
    # - Show "Save As r1-A" or something
    # - Repeat, but now show raveler object excluding pieces that have been cut off, and show next split point (possibly in that same raveler object)
    # - Deleting an object means that it's pixels will automatically go back to the raveler object's pixels
    
    def setupLayers(self):
        def findLayer(f, layerlist):
            for l in layerlist:
                if f(l):
                    return l
            return None

        layers = []
        carvingLayers = super(SplitBodyCarvingGui, self).setupLayers()        
        
        highlightedObjectSlot = self.topLevelOperatorView.CurrentRavelerObject
        if highlightedObjectSlot.ready():
            # 0=Transparent, 1=blue
            colortable = [QColor(0, 0, 0, 0).rgba(), QColor(0, 0, 255).rgba()]
            highlightedObjectLayer = ColortableLayer(LazyflowSource(highlightedObjectSlot), colortable, direct=True)
            highlightedObjectLayer.name = "Current Raveler Object"
            highlightedObjectLayer.visible = True
            highlightedObjectLayer.opacity = 0.25
            layers.append(highlightedObjectLayer)

        remainingRavelerObjectSlot = self.topLevelOperatorView.CurrentRavelerObjectRemainder
        if remainingRavelerObjectSlot.ready():
            # 0=Transparent, 1=blue
            colortable = [QColor(0, 0, 0, 0).rgba(), QColor(255, 0, 0).rgba()]
            remainingObjectLayer = ColortableLayer(LazyflowSource(remainingRavelerObjectSlot), colortable, direct=True)
            remainingObjectLayer.name = "Remaining Raveler Object"
            remainingObjectLayer.visible = True
            remainingObjectLayer.opacity = 0.25
            layers.append(remainingObjectLayer)

        ravelerLabelsSlot = self.topLevelOperatorView.RavelerLabels
        if ravelerLabelsSlot.ready():
            colortable = []
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            ravelerLabelLayer = ColortableLayer(LazyflowSource(ravelerLabelsSlot), colortable, direct=True)
            ravelerLabelLayer.name = "Raveler Labels"
            ravelerLabelLayer.visible = False
            ravelerLabelLayer.opacity = 0.4
            layers.append(ravelerLabelLayer)

        maskedSegSlot = self.topLevelOperatorView.MaskedSegmentation
        if maskedSegSlot.ready():
            colortable = [QColor(0,0,0,0).rgba(), QColor(0,0,0,0).rgba(), QColor(0,255,0).rgba()]
            maskedSegLayer = ColortableLayer(LazyflowSource(maskedSegSlot), colortable, direct=True)
            maskedSegLayer.name = "Masked Segmentation"
            maskedSegLayer.visible = True
            maskedSegLayer.opacity = 0.3
            layers.append(maskedSegLayer)
            
            # Hide the original carving segmentation.
            # TODO: Remove it from the list altogether?
            carvingSeg = findLayer( lambda l: l.name == "segmentation", carvingLayers )
            if carvingSeg is not None:
                carvingSeg.visible = False
        
        layers += carvingLayers

        return layers

