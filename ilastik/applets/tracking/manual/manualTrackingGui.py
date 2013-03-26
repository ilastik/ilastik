from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot

from ilastik.widgets.featureTableWidget import FeatureEntry
from ilastik.widgets.featureDlg import FeatureDlg

import os
import numpy
from ilastik.utility import bind
from lazyflow.operators import OpSubRegion

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from ilastik.applets.layerViewer import LayerViewerGui
from ilastik.applets.labeling import LabelingGui

import volumina.colortables as colortables
from volumina.api import \
    LazyflowSource, GrayscaleLayer, ColortableLayer, AlphaModulatedLayer, \
    ClickableColortableLayer, LazyflowSinkSource

from volumina.interpreter import ClickInterpreter

from ilastik.applets.objectExtraction import config


class ManualTrackingGui(LayerViewerGui):

    def appletDrawer( self ):
        return self._drawer

    def reset( self ):
        print "TrackinGui.reset(): not implemented"

    def _loadUiFile(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")        
        return self._drawer
    
    def initAppletDrawerUi(self):        
        self._drawer = self._loadUiFile()
        self._drawer.newTrack.pressed.connect(self._onNewTrackPressed)
        self._drawer.delTrack.pressed.connect(self._onDelTrackPressed)
        self._drawer.delSubtrack.pressed.connect(self._onDelSubtrackPressed)
        self._drawer.activeTrackBox.currentIndexChanged.connect(self._currentActiveTrackChanged)
        
    ###########################################
    ###########################################
    
    def __init__(self, topLevelOperatorView):
        """
        """    
        
        self.topLevelOperatorView = topLevelOperatorView
        super(ManualTrackingGui, self).__init__(topLevelOperatorView)
        
        self.mainOperator = topLevelOperatorView
        
        if self.mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = self.mainOperator.LabelImage.meta.shape
        self.mainOperator.LabelImage.notifyMetaChanged( self._onMetaChanged)
        
        labels = {}
        for t in range(self.mainOperator.LabelImage.meta.shape[0]):
            labels[t]={}  
        self.mainOperator.Labels.setValue(labels)
            

    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.LabelImage:
            if slot.meta.shape:                
                self.editor.dataShape = slot.meta.shape

                maxt = slot.meta.shape[0] - 1                
                self._drawer.from_time.setValue(0)                
                self._drawer.to_time.setValue(maxt)
            
        if slot is self.mainOperator.RawImage:    
            if slot.meta.shape and not self.rawsrc:    
                self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
                layerraw = GrayscaleLayer( self.rawsrc )
                layerraw.name = "Raw"
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
        
        ct = colortables.create_random_16bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        self.trackingsrc = LazyflowSource( self.topLevelOperatorView.TrackImage )
        trackingLayer = ColortableLayer( self.trackingsrc, ct )
        trackingLayer.name = "Manual Tracking"
        trackingLayer.visible = False
        trackingLayer.opacity = 0.8
        layers.append(trackingLayer)
        
        
        self.objectssrc = LazyflowSource( self.topLevelOperatorView.BinaryImage )
#        ct = colortables.create_default_8bit()
        ct = colortables.create_random_16bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        ct[1] = QColor(255,255,0,50).rgba() # make 0 transparent
        objLayer = ColortableLayer( self.objectssrc, ct )
        objLayer.name = "Objects"
        objLayer.opacity = 0.8
        objLayer.visible = True
        layers.append(objLayer)


        ## raw data layer
        self.rawsrc = None
        self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
        rawLayer = GrayscaleLayer( self.rawsrc )
        rawLayer.name = "Raw"        
        layers.insert( len(layers), rawLayer )   
        
        
        if self.topLevelOperatorView.LabelImage.meta.shape:
            self.editor.dataShape = self.topLevelOperatorView.LabelImage.meta.shape

            maxt = self.topLevelOperatorView.LabelImage.meta.shape[0] - 1
            maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
            maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
            maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1
        
            self._drawer.from_time.setValue(0)
            self._drawer.to_time.setValue(maxt) 
            self._drawer.from_x.setValue(0)
            self._drawer.to_x.setValue(maxx)
            self._drawer.from_y.setValue(0)
            self._drawer.to_y.setValue(maxy)   
            self._drawer.from_z.setValue(0)    
            self._drawer.to_z.setValue(maxz)
            
#            self._drawer.lineageFromBox.setRange(0,maxt-1)
#            self._drawer.lineageFromBox.setValue(0)
#            self._drawer.lineageToBox.setRange(0,maxt-2)
#            self._drawer.lineageToBox.setValue(maxt-2)    
        
        self.topLevelOperatorView.RawImage.notifyReady( self._onReady )
        self.topLevelOperatorView.RawImage.notifyMetaChanged( self._onMetaChanged )
        
        return layers


    @staticmethod
    def _getObject(slot, pos5d):
        slicing = tuple(slice(i, i+1) for i in pos5d)
        arr = slot[slicing].wait()
        return arr.flat[0]


    def handleEditorLeftClick(self, position5d, globalWindowCoordiante):
        oid = self._getObject(self.mainOperator.LabelImage, position5d)
        if oid == 0:
            return
                
        activeTrack = self.mainOperator.ActiveTrack
        if not activeTrack.ready() or activeTrack.value == 0:
            print 'ActiveTrack slot not ready'
            return        
        activeTrack = activeTrack.value
        
        t = position5d[0]

        labelslot = self.mainOperator.Labels
        if not labelslot.ready():
            print 'Label slot not ready'
            return
        labels = labelslot.value        

        if t not in labels.keys():
            labels[t] = {}
        if oid not in labels[t].keys():
            labels[t][oid] = set()
                        
        labels[t][oid].add(activeTrack)
        labelslot.setValue(labels)
        labelslot.setDirty([t,])
        print 'added (t,oid,activeTrack) =', (t,oid, activeTrack)
        

        
        
    
    def _currentActiveTrackChanged(self):
        self.mainOperator.ActiveTrack.setValue(self._getActiveTrack())
        
    def _getActiveTrack(self):
        if self._drawer.activeTrackBox.count() > 0:
            return int(self._drawer.activeTrackBox.currentText())
        else:
            return 0
    
    def _onNewTrackPressed(self):
        activeTrackBox = self._drawer.activeTrackBox
        allTracks = [int(activeTrackBox.itemText(i)) for i in range(activeTrackBox.count())]
        if len(allTracks) == 0:
            activeTrackBox.addItem(str(1))
        else:
            activeTrackBox.addItem(str(max(allTracks)+1))
        activeTrackBox.setCurrentIndex(activeTrackBox.count()-1)
    
    def _onDelTrackPressed(self):        
        activeTrackBox = self._drawer.activeTrackBox
        if activeTrackBox.count() == 0:
            print 'there is no active track to delete'
            return 
        
        track2remove = activeTrackBox.currentIndex()
        activeTrackBox.removeItem(track2remove)
        
        labelslot = self.mainOperator.Labels
        if not labelslot.ready():
            return
        labels = labelslot.value        

        for t in labels.keys():
            for oid in labels[t].keys():
                if track2remove in labels[t][oid]:
                    labels[t][oid].remove(track2remove)
        labelslot.setValue(labels)  
        
    
    def _onDelSubtrackPressed(self):
        pass
    
    def _onAddToTrackPressed(self):
        pass
    
    def _onDelFromTrackPressed(self):
        pass
    
    