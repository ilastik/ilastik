import os
from PyQt4 import uic
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from volumina.volumeEditor import VolumeEditor

from ilastik.utility.gui import ThreadRouter, threadRouted

class MultiEditorGui(LayerViewerGui):
    
    def __init__(self, parentApplet, topLevelOperatorView, additionalMonitoredSlots=[], centralWidgetOnly=False, crosshair=True):
        super(MultiEditorGui, self).__init__(parentApplet, topLevelOperatorView, additionalMonitoredSlots, centralWidgetOnly, crosshair)
        
        print "initializing extra editor...."
        self._extra_editor = VolumeEditor( self.layerstack, self )
        
        for layer in self.layerstack:
            print "Layer: {}".format(layer.name)
        
        self.extraVolumeEditorWidget.init(self._extra_editor)

    def _after_init(self):
        super(MultiEditorGui, self)._after_init()
        print "AFTER INIT:"
        for layer in self.layerstack:
            print "Layer: {}".format(layer.name)
            
        print "layerstack id:", id(self.layerstack)
        print "editor layerstack id:", id(self.editor.layerStack)
        print "extra editor layerstack id:", id(self._extra_editor.layerStack)
        

    
    def _initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uic.loadUi(localDir+"/centralWidget.ui", self)

    def updateAllLayers(self, slot=None):
        super(MultiEditorGui, self).updateAllLayers()
        # If the datashape changed, tell the editor
        # FIXME: This may not be necessary now that this gui doesn't handle the multi-image case...
        newDataShape = self.determineDatashape()
        if newDataShape is not None and self._extra_editor.dataShape != newDataShape:
            self._extra_editor.dataShape = newDataShape
                       
            # Find the xyz midpoint
            midpos5d = [x/2 for x in newDataShape]
            
            # center viewer there
            self.setExtraViewerPos(midpos5d)

    @threadRouted
    def setExtraViewerPos(self, pos, setTime=False, setChannel=False):
        try:
            pos5d = self.validatePos(pos, dims=5)
            
            # set xyz position
            pos3d = pos5d[1:4]
            self._extra_editor.posModel.slicingPos = pos3d
            
            # set time and channel if requested
            if setTime:
                self._extra_editor.posModel.time = pos5d[0]
            if setChannel:
                self._extra_editor.posModel.channel = pos5d[4]

            self._extra_editor.navCtrl.panSlicingViews( pos3d, [0,1,2] )
        except Exception, e:
            raise
            #logger.warn("Failed to navigate to position (%s): %s" % (pos, e))
        return
