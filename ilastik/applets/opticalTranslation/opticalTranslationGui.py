from ilastik.applets.layerViewer import LayerViewerGui
from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.layer import GrayscaleLayer, ColortableLayer, RGBALayer
import volumina.colortables as colortables
from lazyflow.rtype import SubRegion

from PyQt4.QtGui import QColor, QProgressDialog
from lazyflow.operators.generic import OpSubRegion
from PyQt4.QtCore import Qt, QString
from PyQt4 import uic

import os


class OpticalTranslationGui( LayerViewerGui ):
    
    def appletDrawer( self ):
        return self._drawer

    def reset( self ):
        print "OpticalTranslationGui.reset(): not implemented"

    def __init__(self, topLevelOperatorView):
        """
        """        
        self.topLevelOperatorView = topLevelOperatorView
        super(OpticalTranslationGui, self).__init__(topLevelOperatorView)
        
        self.mainOperator = topLevelOperatorView
        
        if self.mainOperator.BinaryImage.meta.shape:
            self.editor.dataShape = self.mainOperator.BinaryImage.meta.shape
        self.mainOperator.BinaryImage.notifyMetaChanged( self._onMetaChanged)
    
    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.BinaryImage:
            if slot.meta.shape:                
                self.editor.dataShape = slot.meta.shape                
            
        if slot is self.mainOperator.RawImage:    
            if slot.meta.shape and not self.rawsrc:    
                self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
                layerraw = GrayscaleLayer( self.rawsrc )
                layerraw.name = "Raw Image"
                self.layerstack.append( layerraw )
    
    def _onReady( self, slot ):
        if slot is self.mainOperator.RawImage:
            if slot.meta.shape and not self.rawsrc:
                self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
                layerraw = GrayscaleLayer( self.rawsrc )    
                layerraw.name = "Raw"
                self.layerstack.append( layerraw )

    def setupLayers( self ):        
        layers = []
        
        self.translationsrc = self.mainOperator.TranslationVectorsDisplay   
#        self.translationsrc = self.mainOperator.TranslationVectors
        opSubRegion = OpSubRegion(graph=self.topLevelOperatorView.graph)
        opSubRegion.Input.connect( self.translationsrc )
        start = [0] * len(self.translationsrc.meta.shape)        
        stop = list(self.translationsrc.meta.shape)
        stop[-1] = 3
        opSubRegion.Start.setValue( tuple(start) )
        opSubRegion.Stop.setValue( tuple(stop) )
        translationLayer = self.createStandardLayerFromSlot( opSubRegion.Output )
#        self.translationsrc = LazyflowSource( self.mainOperator.TranslationVectorsDisplay)#        
#        translationLayer = RGBALayer(self.translationsrc)
        translationLayer.name = "Translation Vector"
        translationLayer.opacity = 0.8
        translationLayer.visible = False
        layers.append(translationLayer)

        ct = colortables.create_default_8bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        ct[1] = QColor(0,255,0,255).rgba() # foreground is green
        self.warpedSrc = LazyflowSource( self.mainOperator.WarpedImage )
        warpedLayer = ColortableLayer( self.warpedSrc, ct )
        warpedLayer.name = "Translation Corrected Binary Image"
        warpedLayer.visible = False
        warpedLayer.opacity = 0.4
        layers.append(warpedLayer)


        ct = colortables.create_default_8bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        ct[1] = QColor(255,0,0,255).rgba() # foreground is read
        self.binarySrc = LazyflowSource( self.mainOperator.BinaryImage )
        binaryLayer = ColortableLayer( self.binarySrc, ct )
        binaryLayer.name = "Binary Image"
        binaryLayer.visible = True
        binaryLayer.opacity = 0.8
        layers.append(binaryLayer)
                
        ## raw data layer        
        self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
        rawLayer = GrayscaleLayer( self.rawsrc )
        rawLayer.name = "Raw Image"        
        layers.insert( len(layers), rawLayer )   
        
        
        if self.topLevelOperatorView.TranslationVectors.meta.shape:
            self.editor.dataShape = self.topLevelOperatorView.TranslationVectors.meta.shape    
        
        self.topLevelOperatorView.RawImage.notifyReady( self._onReady )
        self.topLevelOperatorView.RawImage.notifyMetaChanged( self._onMetaChanged )
        
        return layers
    
    def _loadUiFile(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")        
        return self._drawer
    
    def initAppletDrawerUi(self):        
        self._drawer = self._loadUiFile()
        
        self._drawer.computeTranslationButton.pressed.connect(self._onComputeTranslationButtonPressed)
        self._drawer.methodBox.currentIndexChanged.connect(self._onMethodChanged)    
    
    def _onMethodChanged(self):
        if self._drawer.methodBox.currentIndex() == 0:
            self.mainOperator.Parameters.value['method'] = 'xor'
        elif self._drawer.methodBox.currentIndex() == 1:
            self.mainOperator.Parameters.value['method'] = 'nxcorr'
        elif self._drawer.methodBox.currentIndex() == 2:
            self.mainOperator.Parameters.value['method'] = 'xcorr'
        self.mainOperator.Parameters.setDirty([])
            
    def _onComputeTranslationButtonPressed(self):        
        self._onMethodChanged()
        
        m = self.mainOperator.TranslationVectors.meta
        maxt = m.shape[0]
        progress = QProgressDialog("Computing Translation Vectors...", "Stop", 0, maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())
        progress.forceShow()
        
        reqs = []
        for t in range(maxt):
            reqs.append(self.mainOperator.TranslationVectorsComputation([t]))
            reqs[-1].submit()
        
        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()
        
        progress.setValue(maxt)
        
        roi = SubRegion(self.mainOperator.TranslationVectors, start=5*(0,), stop=m.shape)
        self.mainOperator.TranslationVectors.setDirty(roi)
        
        print 'Translation Vector Computation: done.'
        
        
        