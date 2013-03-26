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
from lazyflow.rtype import SubRegion
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
            

    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.LabelImage:
            if slot.meta.shape:                
                self.editor.dataShape = slot.meta.shape
            
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
        trackingLayer.visible = True
        trackingLayer.opacity = 0.8
        layers.append(trackingLayer)
        
        
        self.objectssrc = LazyflowSource( self.topLevelOperatorView.BinaryImage )
#        ct = colortables.create_default_8bit()
        ct = colortables.create_random_16bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        ct[1] = QColor(255,255,0,100).rgba() # make 0 transparent
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

#        labelslot = self.mainOperator.Labels
#        if not labelslot.ready():
#            print 'Label slot not ready'
#            return
#        labels = labelslot.value
                

        self._addObjectToTrack(activeTrack,oid,t)
        print 'manualTrackingGui::handleEditorLeftClick: Labels = ', self.mainOperator.labels
        
        roi = SubRegion(self.mainOperator.TrackImage, start=[t,] + 4*[0,], stop=[t+1,] + list(self.mainOperator.TrackImage.meta.shape[1:]))
        self.mainOperator.TrackImage.setDirty(roi)

        self.editor.posModel.time = self.editor.posModel.time + 1
#        self.editor.posModel.time( t+1 )
        
    def handleEditorRightClick(self, position5d, globalWindowCoordiante):
        oid = self._getObject(self.mainOperator.LabelImage, position5d)
        if oid == 0:
            return
        
        t = position5d[0]
        menu = QMenu(self)        
        delLabel = {}
        delSubtrack = {}
        if oid in self.mainOperator.labels[t].keys():
            for l in self.mainOperator.labels[t][oid]:
                text = "remove label " + str(l)
                delLabel[text] = l
                menu.addAction(text)
                
                text = "remove label " + str(l) + " from here"
                delSubtrack[text] = l
                menu.addAction(text)
            
        markDiv = "mark object " +str(oid) + " as division"
        menu.addAction(markDiv)
        
        unmarkDiv = "unmark object " + str(oid) + " as division"
        menu.addAction(unmarkDiv)
        
        runTracking = "run automatic tracking for object " + str(oid)
        menu.addAction(runTracking)
                    
        action = menu.exec_(globalWindowCoordiante)
        if action is None:
            return
        selection = str(action.text())
        if selection in delLabel.keys():
            self.mainOperator.labels[t][oid].remove(delLabel[selection])
            
            roi = SubRegion(self.mainOperator.TrackImage, start=[t,] + 4*[0,], stop=[t+1,] + list(self.mainOperator.TrackImage.meta.shape[1:]))
            self.mainOperator.TrackImage.setDirty(roi)
            
        elif selection in delSubtrack.keys():
            track2remove = delSubtrack[selection]
            maxt = self.mainOperator.LabelImage.meta.shape[0]
            for t in range(t,maxt):
                for oid in self.mainOperator.labels[t].keys():
                    if track2remove in self.mainOperator.labels[t][oid]:
                        self.mainOperator.labels[t][oid].remove(track2remove)
            
            roi = SubRegion(self.mainOperator.TrackImage, start=[t,] + 4*[0,], stop=[maxt,] + list(self.mainOperator.TrackImage.meta.shape[1:]))
            self.mainOperator.TrackImage.setDirty(roi)
            
        elif selection == markDiv:
            print 'mark as div: to be implemented'
            
        elif selection == unmarkDiv:
            print 'unmark as div: to be implemented'
        
        elif selection == runTracking:
            self._runSubtracking(position5d, oid)
            
        else:
            assert False, "cannot reach this"
                        
    
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
        
        track2remove = self._getActiveTrack()
        idx2remove = activeTrackBox.currentIndex()
        activeTrackBox.removeItem(idx2remove)
        
#        labelslot = self.mainOperator.Labels
#        if not labelslot.ready():
#            return
#        labels = labelslot.value        

        affectedT = []
        for t in self.mainOperator.labels.keys():
            for oid in self.mainOperator.labels[t].keys():
                if track2remove in self.mainOperator.labels[t][oid]:
                    self.mainOperator.labels[t][oid].remove(track2remove)
                    affectedT.append(t)
                    
        if len(affectedT) > 0:
            roi = SubRegion(self.mainOperator.TrackImage, start=[min(affectedT),] + 4*[0,], stop=[max(affectedT)+1,] + list(self.mainOperator.TrackImage.meta.shape[1:]))
            self.mainOperator.TrackImage.setDirty(roi)
#        labelslot.setValue(labels)  
    
    def _addObjectToTrack(self, activeTrack, oid, t):
        if activeTrack == 0:
            print 'activeTrack is 0'
            return
        
        if t not in self.mainOperator.labels.keys():
            self.mainOperator.labels[t] = {}
        if oid not in self.mainOperator.labels[t].keys():
            self.mainOperator.labels[t][oid] = set()
                        
        self.mainOperator.labels[t][oid].add(activeTrack)
#        labelslot.setValue(labels)
#        labelslot.setDirty([t,])        
        print 'added (t,oid,activeTrack) =', (t,oid, activeTrack)
        
        
    def _runSubtracking(self, position5d, oid):
        window = 150
        
        t_start = position5d[0]
        activeTrack = self._getActiveTrack()
        if activeTrack == 0:
            print 'active track is 0'
            return 
        
        self._addObjectToTrack(self._getActiveTrack(), oid, t_start)
                
        sroi = [slice(0,1),]
        for idx,p in enumerate(position5d[1:-1]):
            sroi += [ slice(max(0,p-window/2),min(p+window/2, self.mainOperator.LabelImage.meta.shape[idx+1])), ]
        
        key_start = [t_start,0,0,0,0]
        key_stop = [t_start+1,] + list(self.mainOperator.LabelImage.meta.shape[1:])
        roi = SubRegion(self.mainOperator.LabelImage, start=key_start, stop=key_stop)
        li_prev = self.mainOperator.LabelImage.get(roi).wait()[sroi]

        oid_prev = oid
        
        for t in range(t_start+1, self.mainOperator.LabelImage.meta.shape[0]):
            key_start[0] = t
            key_stop[0] = t+1
            roi = SubRegion(self.mainOperator.LabelImage, start=key_start, stop=key_stop)
            li_cur = self.mainOperator.LabelImage.get(roi).wait()[sroi]
            
            li_prev_oid = (li_prev == oid_prev)
            li_cur_pos = (li_cur > 0)
            uniqueLabels = list(numpy.unique(numpy.where(li_prev_oid == li_cur_pos, li_cur, 0)))
            if 0 in uniqueLabels:
                uniqueLabels.remove(0)
            if len(uniqueLabels) != 1:                
                print 'the tracking is ambiguous, abort at t =', t, ', label candidates = ', uniqueLabels
                break
            
            self._addObjectToTrack(activeTrack, uniqueLabels[0], t)
            
            oid_prev = uniqueLabels[0]
            li_prev = li_cur
    
        
        roi = SubRegion(self.mainOperator.TrackImage, start=[t_start,] + 4*[0,], stop=[max(t_start+1,t-1),] + list(self.mainOperator.TrackImage.meta.shape[1:]))
        self.mainOperator.TrackImage.setDirty(roi)

        if t > 1:
            self.editor.posModel.time = t - 1
        