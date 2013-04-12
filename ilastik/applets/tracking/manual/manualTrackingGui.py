from PyQt4.QtGui import *
from PyQt4 import uic, QtGui

import os
import numpy

import logging
from lazyflow.rtype import SubRegion
from copy import copy
from ilastik.applets.tracking.base.trackingUtilities import LineageH5
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from ilastik.applets.layerViewer import LayerViewerGui

import volumina.colortables as colortables
from volumina.api import LazyflowSource, GrayscaleLayer, ColortableLayer


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
        self._drawer.divEvent.pressed.connect(self._onDivEventPressed)
        self._drawer.activeTrackBox.currentIndexChanged.connect(self._currentActiveTrackChanged)
        self._drawer.divisionsList.itemActivated.connect(self._onDivisionsListActivated)
        self._drawer.markMisdetection.pressed.connect(self._onMarkMisdetectionPressed)
        self._drawer.exportButton.pressed.connect(self._onExportButtonPressed)
        self._drawer.gotoLabel.pressed.connect(self._onGotoLabel)
        self._drawer.printMultiple.pressed.connect(self._onPrintMultipleLabelsInTimestep)
        self._drawer.printApp.pressed.connect(self._onPrintAppearancesInMergers)
        
        self._drawer.from_time.valueChanged.connect(self._setRanges)
        self._drawer.from_x.valueChanged.connect(self._setRanges)
        self._drawer.from_y.valueChanged.connect(self._setRanges)
        self._drawer.from_z.valueChanged.connect(self._setRanges)
        self._drawer.to_time.valueChanged.connect(self._setRanges)
        self._drawer.to_x.valueChanged.connect(self._setRanges)
        self._drawer.to_y.valueChanged.connect(self._setRanges)
        self._drawer.to_z.valueChanged.connect(self._setRanges)
        
        
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
        
        self.ct = colortables.create_random_16bit()        
        
        self.divLock = False
        self.divs = []
        self.labelsWithDivisions = {}
        self.misdetLock = False
        self.misdetIdx = -1
            

    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.LabelImage:
            if slot.meta.shape:                
                self.editor.dataShape = slot.meta.shape
                
                maxt = slot.meta.shape[0] - 1
                self._setRanges()
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
                
        self.ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent        
        self.ct[255] = QColor(0,0,0,255).rgba() # make -1 black
        self.ct[-1] = QColor(0,0,0,255).rgba()
        self.trackingsrc = LazyflowSource( self.topLevelOperatorView.TrackImage )
        trackingLayer = ColortableLayer( self.trackingsrc, self.ct )
        trackingLayer.name = "Manual Tracking"
        trackingLayer.visible = True
        trackingLayer.opacity = 0.8
        layers.append(trackingLayer)
        
        ct = colortables.create_random_16bit()
        ct[1] = QColor(230,0,0,150).rgba()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        self.untrackedsrc = LazyflowSource( self.topLevelOperatorView.UntrackedImage )
        untrackedLayer = ColortableLayer( self.untrackedsrc, ct )
        untrackedLayer.name = "Untracked Objects"
        untrackedLayer.visible = False
        untrackedLayer.opacity = 0.8
        layers.append(untrackedLayer)
        
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
            
            maxt = self.topLevelOperatorView.LabelImage.meta.shape[0] - 1
            maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
            maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
            maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1
        
            self._setRanges()
            self._drawer.from_time.setValue(0)
            self._drawer.to_time.setValue(maxt) 
            self._drawer.from_x.setValue(0)
            self._drawer.to_x.setValue(maxx)
            self._drawer.from_y.setValue(0)
            self._drawer.to_y.setValue(maxy)   
            self._drawer.from_z.setValue(0)    
            self._drawer.to_z.setValue(maxz)
        
        self.topLevelOperatorView.RawImage.notifyReady( self._onReady )
        self.topLevelOperatorView.RawImage.notifyMetaChanged( self._onMetaChanged )
        
        self._setDivisionsList()
        self._setActiveTrackList()
        
        return layers

    def _addDivisionToListWidget(self, trackid, child1, child2, t_parent):
        divItem = QListWidgetItem("%d: %d, %d" % (trackid, child1, child2))
        divItem.setBackground(QColor(self.ct[trackid]))
        divItem.setCheckState(False)
        self._drawer.divisionsList.addItem(divItem)
        if t_parent not in self.labelsWithDivisions.keys():
            self.labelsWithDivisions[t_parent] = []
        if t_parent+1 not in self.labelsWithDivisions.keys():
            self.labelsWithDivisions[t_parent+1] = []
        self.labelsWithDivisions[t_parent].append(trackid)
        self.labelsWithDivisions[t_parent+1].append(child1)
        self.labelsWithDivisions[t_parent+1].append(child2)

    def _setDivisionsList(self):
        for trackid in self.mainOperator.divisions.keys():
            self._addDivisionToListWidget(trackid, self.mainOperator.divisions[trackid][0][0], self.mainOperator.divisions[trackid][0][1],
                                          self.mainOperator.divisions[trackid][-1])
        # set all items checked
        for idx in range(self._drawer.divisionsList.count()):
            self._drawer.divisionsList.item(idx).setCheckState(True)
    
    def _setActiveTrackList(self):
        activeTrackBox = self._drawer.activeTrackBox
        allTracks = set()
        for t in self.mainOperator.labels.keys():            
            for oid in self.mainOperator.labels[t].keys():
                for tr in list(self.mainOperator.labels[t][oid]):
                    allTracks.add(tr)        
        print 'allTracks = ', allTracks
        
        items = set()
        for idx in range(activeTrackBox.count()):
            items.add(int(activeTrackBox.itemText(idx)))
            
        for tid in sorted(allTracks):
            if tid not in items:
                activeTrackBox.addItem(str(tid), self.ct[tid])
        
        activeTrackBox.setCurrentIndex(activeTrackBox.count()-1)
    
    @staticmethod
    def _getObject(slot, pos5d):
        slicing = tuple(slice(i, i+1) for i in pos5d)
        arr = slot[slicing].wait()
        return arr.flat[0]

    def _setDirty(self, slot, timesteps):
        if slot is self.mainOperator.TrackImage:
            roi = SubRegion(self.mainOperator.TrackImage, start=[min(timesteps),] + 4*[0,], stop=[max(timesteps)+1,] + list(self.mainOperator.TrackImage.meta.shape[1:]))
            self.mainOperator.TrackImage.setDirty(roi)
        elif slot is self.mainOperator.Labels:
            self.mainOperator.Labels.setDirty(timesteps)
        elif slot is self.mainOperator.Divisions:
            self.mainOperator.Divisions.setDirty([])
        elif slot is self.mainOperator.UntrackedImage:
            roi = SubRegion(self.mainOperator.UntrackedImage, start=[min(timesteps),] + 4*[0,], stop=[max(timesteps)+1,] + list(self.mainOperator.TrackImage.meta.shape[1:]))
            self.mainOperator.UntrackedImage.setDirty(roi)
            
    def handleEditorLeftClick(self, position5d, globalWindowCoordiante):
        if self.divLock:
            oid = self._getObject(self.mainOperator.LabelImage, position5d)
            item = (position5d[0], oid)
            if len(self.divs) == 0:                
                self.divs.append(item)
                self.editor.posModel.time = self.editor.posModel.time + 1                
            elif len(self.divs) > 0:
                if position5d[0] != self.divs[0][0] + 1:
                    print 'the daughter cells must be in timestep', self.divs[0][0] + 1
                    return
                if item not in self.divs:
                    self.divs.append(item)
                
            if len(self.divs) == 3:                
                activeTrack = self._getActiveTrack()
                if (self.divs[0][1] not in self.mainOperator.labels[self.divs[0][0]]) or (activeTrack not in self.mainOperator.labels[self.divs[0][0]][self.divs[0][1]]):                    
                    QtGui.QMessageBox.critical(self, "Error", "Error: The mother cell must have the active track as a label.", QtGui.QMessageBox.Ok)
                    self.divLock = False
                    self.divs = []
                    self._drawer.divEvent.setChecked(False)
                    return
#                self._addObjectToTrack(activeTrack, self.divs[0][1], self.divs[0][0])
                div = [activeTrack,]
                
                for i in range(1,3):
                    activeTrack = self._addNewTrack()
                    self._addObjectToTrack(activeTrack, self.divs[i][1], self.divs[i][0])
                    div += [activeTrack,]
                
                self._addDivisionToListWidget(div[0], div[1], div[2], self.editor.posModel.time-1)                
                
                self.mainOperator.divisions[div[0]] = (div[1:], self.divs[0][0])
                print 'divisions = ', self.mainOperator.divisions
                
                self._setDirty(self.mainOperator.Divisions, [])
                self._setDirty(self.mainOperator.Labels, [self.divs[0][0],self.divs[0][0]+1])
                self._setDirty(self.mainOperator.TrackImage, [self.divs[0][0]])            
                self._setDirty(self.mainOperator.UntrackedImage, [self.divs[0][0]])
                
                # release the division lock
                self.divLock = False
                self.divs = []
                self._drawer.divEvent.setChecked(False)
                
                self._drawer.activeTrackBox.setEnabled(True)
                self._drawer.delTrack.setEnabled(True)
                self._drawer.newTrack.setEnabled(True)
                self._drawer.markMisdetection.setEnabled(True)
        else:
            oid = self._getObject(self.mainOperator.LabelImage, position5d)
            if oid == 0:
                return
                    
            activeTrack = self.mainOperator.ActiveTrack
            if not activeTrack.ready() or activeTrack.value == 0:
                QtGui.QMessageBox.critical(self, "Error", "Error: There is no active track.", QtGui.QMessageBox.Ok)            
                return        
            activeTrack = activeTrack.value
            
            t = position5d[0]
    
            res = self._addObjectToTrack(activeTrack,oid,t)
            if res == -1:
                return
#            print 'manualTrackingGui::handleEditorLeftClick: Labels = ', self.mainOperator.labels
            
            self._setDirty(self.mainOperator.TrackImage, [t])
            self._setDirty(self.mainOperator.UntrackedImage, [t])
            self._setDirty(self.mainOperator.Labels, [t])
    
            self.editor.posModel.time = self.editor.posModel.time + 1

            
        
    def handleEditorRightClick(self, position5d, globalWindowCoordiante):
        if self.divLock:
            return
                
        oid = self._getObject(self.mainOperator.LabelImage, position5d)
        if oid == 0:
            return
        
        t = position5d[0]
        activeTrack = self._getActiveTrack()
        menu = QMenu(self)        
        delLabel = {}
        delSubtrack = {}
        trackids = []
        if oid in self.mainOperator.labels[t].keys():
            for l in self.mainOperator.labels[t][oid]:
                trackids.append(l)
                text = "remove label " + str(l)
                delLabel[text] = l
                menu.addAction(text)
                
                if activeTrack != self.misdetIdx:
                    text = "remove label " + str(l) + " from here"
                    delSubtrack[text] = l
                    menu.addAction(text)
        
        if activeTrack != self.misdetIdx:
            runTracking = "run automatic tracking for object " + str(oid)
            menu.addAction(runTracking)
        
        delDivision = {}
        if activeTrack != self.misdetIdx:
            for trackid in trackids:
                if trackid in self.mainOperator.divisions.keys() and self.mainOperator.divisions[trackid][1] == t:
                    text = "remove division event from label " + str(trackid)
                    delDivision[text] = trackid
                    menu.addAction(text)
        
        action = menu.exec_(globalWindowCoordiante)
        if action is None:
            return

        selection = str(action.text())
        if selection in delLabel.keys():
            self._delLabel(t, oid, delLabel[selection])
            
            self._setDirty(self.mainOperator.TrackImage, [t])
            self._setDirty(self.mainOperator.UntrackedImage, [t])
            self._setDirty(self.mainOperator.Labels, [t])
            
        elif selection in delSubtrack.keys():
            track2remove = delSubtrack[selection]
            maxt = self.mainOperator.LabelImage.meta.shape[0]
            for t in range(t,maxt):
                for oid in self.mainOperator.labels[t].keys():
                    if track2remove in self.mainOperator.labels[t][oid]:
                        self._delLabel(t, oid, track2remove)
            
            self._setDirty(self.mainOperator.TrackImage, range(t,maxt))
            self._setDirty(self.mainOperator.UntrackedImage, range(t, maxt))
            self._setDirty(self.mainOperator.Labels, range(t,maxt))
            
        elif selection == runTracking:
            self._runSubtracking(position5d, oid)
        
        elif selection in delDivision.keys():
            self._delDivisionEvent(delDivision[selection])
            
        else:
            assert False, "cannot reach this"
               
    def _delDivisionEvent(self, parent_label):
        children = self.mainOperator.divisions[parent_label][0]            
        text = "%d: %d, %d" % (parent_label, children[0], children[1])
        for idx in range(self._drawer.divisionsList.count()):
            if str(self._drawer.divisionsList.item(idx).text()) == text:
                self._drawer.divisionsList.takeItem(idx)
                break
        t_parent = self.mainOperator.divisions[parent_label][-1]
        del self.mainOperator.divisions[parent_label]
        self.labelsWithDivisions[t_parent].remove(parent_label)
        self.labelsWithDivisions[t_parent+1].remove(children[0])
        self.labelsWithDivisions[t_parent+1].remove(children[1])
        
        self._setDirty(self.mainOperator.Divisions, [])
    
    def _currentActiveTrackChanged(self):
        self.mainOperator.ActiveTrack.setValue(self._getActiveTrack())
        self._setStyleSheet(self._drawer.activeTrackBox, QColor(self.ct[self._getActiveTrack()]))
        
    def _getActiveTrack(self):
        if self._drawer.activeTrackBox.count() > 0:
            return int(self._drawer.activeTrackBox.currentText())
        else:
            return 0
        
    def _addNewTrack(self):
        activeTrackBox = self._drawer.activeTrackBox
        allTracks = [int(activeTrackBox.itemText(i)) for i in range(activeTrackBox.count())]
        if len(allTracks) == 1: # trackid self.misdetIdx is misdetection
            activeTrackBox.addItem(str(1), self.ct[1])
        else:
            newTrack = max(allTracks)+1
            if newTrack % 255 == 0:
                newTrack += 2
            elif newTrack % 256 == 0:
                newTrack += 1
            activeTrackBox.addItem(str(newTrack), self.ct[newTrack])
        activeTrackBox.setCurrentIndex(activeTrackBox.count()-1)
        return self._getActiveTrack()
        
    def _onNewTrackPressed(self):
        self._addNewTrack()
    
    def _delLabel(self, t, oid, track2remove):        
        if t in self.labelsWithDivisions.keys() and track2remove in self.labelsWithDivisions[t]:
            QtGui.QMessageBox.critical(self, "Error", "Error: Cannot remove label " + str(track2remove) +
                                       " at t=" + str(t) + ", since it is involved in a division event." + 
                                       " Remove division event first.", QtGui.QMessageBox.Ok)
            return
        self.mainOperator.labels[t][oid].remove(track2remove)
        self._setDirty(self.mainOperator.Labels, [t])
        self._setDirty(self.mainOperator.TrackImage, [t])
        self._setDirty(self.mainOperator.UntrackedImage, [t])
        
    def _onDelTrackPressed(self):        
        activeTrackBox = self._drawer.activeTrackBox
        if activeTrackBox.count() == 0:
            print 'there is no active track to delete'
            return 
        
        track2remove = self._getActiveTrack()
        idx2remove = activeTrackBox.currentIndex()
        activeTrackBox.removeItem(idx2remove)     

        affectedT = []
        for t in self.mainOperator.labels.keys():
            for oid in self.mainOperator.labels[t].keys():
                if track2remove in self.mainOperator.labels[t][oid]:
                    self._delLabel(t,oid,track2remove)                    
                    affectedT.append(t)
        
#        # delete the track from division events if present:
#        for key in self.mainOperator.divisions.keys():
#            if track2remove in key or track2remove in self.mainOperator.divisions[key][0]:
#                self._delDivisionEvent(key)                
                
        if len(affectedT) > 0:
            self._setDirty(self.mainOperator.TrackImage, affectedT)
            self._setDirty(self.mainOperator.UntrackedImage, affectedT)
            self._setDirty(self.mainOperator.Labels, affectedT)
    
    def _addObjectToTrack(self, activeTrack, oid, t):
        if t not in self.mainOperator.labels.keys():
            self.mainOperator.labels[t] = {}
        if oid not in self.mainOperator.labels[t].keys():
            self.mainOperator.labels[t][oid] = set()
        if activeTrack == self.misdetIdx:
            if len(self.mainOperator.labels[t][oid]) > 0:
                QtGui.QMessageBox.critical(self, "Error", "Error: This object is already marked as part of a track, cannot mark it as a misdetection.", QtGui.QMessageBox.Ok)            
                return -1
        else:
            for tracklist in self.mainOperator.labels[t].values():
                if activeTrack in tracklist:                
                    QtGui.QMessageBox.critical(self, "Error", "Error: There is already an object with this track id in this timeslice", QtGui.QMessageBox.Ok)            
                    return -1
        
        if self.misdetIdx in self.mainOperator.labels[t][oid]:
            QtGui.QMessageBox.critical(self, "Error", "Error: This object is already marked as a misdetection. Cannot mark it as part of a track.", QtGui.QMessageBox.Ok)            
            return -1
        
        self.mainOperator.labels[t][oid].add(activeTrack)  
        self._setDirty(self.mainOperator.Labels, [t])
        print 'added (t,oid,activeTrack) =', (t,oid, activeTrack)
        
        
    def _runSubtracking(self, position5d, oid):
        window = 40
        
        t_start = position5d[0]
        activeTrack = self._getActiveTrack()
        if activeTrack == 0:
            QtGui.QMessageBox.critical(self, "Error", "Error: There is no active track.", QtGui.QMessageBox.Ok)
            return 
        
        res = self._addObjectToTrack(self._getActiveTrack(), oid, t_start)
        if res == -1:
            return
                
        sroi = [slice(0,1),]
        for idx,p in enumerate(position5d[1:-1]):
            sroi += [ slice(max(0,p-window/2),min(p+window/2, self.mainOperator.LabelImage.meta.shape[idx+1])), ]
        
        key_start = [t_start,0,0,0,0]
        key_stop = [t_start+1,] + list(self.mainOperator.LabelImage.meta.shape[1:])
        roi = SubRegion(self.mainOperator.LabelImage, start=key_start, stop=key_stop)
        li_prev = self.mainOperator.LabelImage.get(roi).wait()[sroi]
        oid_prev = oid
        t_end = self.mainOperator.LabelImage.meta.shape[0] - 1 
        
        for t in range(t_start+1, self.mainOperator.LabelImage.meta.shape[0]):
            key_start[0] = t
            key_stop[0] = t+1
            roi = SubRegion(self.mainOperator.LabelImage, start=key_start, stop=key_stop)
            li_cur = self.mainOperator.LabelImage.get(roi).wait()[sroi]
            
#            li_prev_oid = (li_prev == oid_prev)
#            li_cur_pos = (li_cur > 0)
#            uniqueLabels = list(numpy.unique(numpy.where(li_prev_oid == li_cur_pos, li_cur, 0)))
            li_prev_oid = (li_prev == oid_prev)
            uniqueLabels = list(numpy.unique(li_prev_oid * li_cur))
            if 0 in uniqueLabels:
                uniqueLabels.remove(0)
            if len(uniqueLabels) != 1:                
                print 'the tracking is ambiguous, abort at t =', t, ', label candidates = ', uniqueLabels
                roi = SubRegion(self.mainOperator.LabelImage, start=[t-1,0,0,0,0], stop=[t,] + list(self.mainOperator.LabelImage.meta.shape[1:]))
                li = self.mainOperator.LabelImage.get(roi).wait()
                coords = numpy.where(li == oid_prev)
                mid = len(coords[1]) / 2
                cur_slicing_pos = self.editor.posModel.slicingPos 
                self.editor.posModel.slicingPos = [coords[1][mid], coords[2][mid], cur_slicing_pos[2]]
                t_end = t-1
                break
            
            res = self._addObjectToTrack(activeTrack, uniqueLabels[0], t)
            if res == -1:
                return
            
            oid_prev = uniqueLabels[0]
            li_prev = li_cur
    
        self._setDirty(self.mainOperator.TrackImage, range(t_start, max(t_start+1,t_end-1)))
        self._setDirty(self.mainOperator.UntrackedImage, range(t_start, max(t_start+1,t_end-1)))
        self._setDirty(self.mainOperator.Labels, range(t_start, max(t_start+1,t_end-1)))

        if t_end > 0:
            self.editor.posModel.time = t_end
    
    def _onDivEventPressed(self):
        if self._getActiveTrack() == self.misdetIdx:
            QtGui.QMessageBox.critical(self, "Error", "Error: Cannot add a division event for misdetections. Disable misdetection.", QtGui.QMessageBox.Ok)
            return
        self.divLock = not self.divLock             
        self._drawer.divEvent.setChecked(not self.divLock)
        self.divs = []
        
        if self.divLock:
            self._drawer.activeTrackBox.setEnabled(False)
            self._drawer.delTrack.setEnabled(False)
            self._drawer.newTrack.setEnabled(False)
            self._drawer.markMisdetection.setEnabled(False)
        else:
            self._drawer.activeTrackBox.setEnabled(True)
            self._drawer.delTrack.setEnabled(True)
            self._drawer.newTrack.setEnabled(True)
            self._drawer.markMisdetection.setEnabled(True)


    def _setStyleSheet(self, widget, qcolor):                         
        values = "{r}, {g}, {b}, {a}".format(r = qcolor.red(),
                                     g = qcolor.green(),
                                     b = qcolor.blue(),
                                     a = qcolor.alpha()
                                     )
        widget.setStyleSheet("QComboBox { background-color: rgba("+values+"); }")
    
    def _onDivisionsListActivated(self):        
        parent = int(str(self._drawer.divisionsList.currentItem().text()).split(':')[0])
        t = self.mainOperator.divisions[parent][1]        
        
        roi = SubRegion(self.mainOperator.LabelImage, start=[t,0,0,0,0], stop=[t+1,] + list(self.mainOperator.LabelImage.meta.shape[1:]))
        li = self.mainOperator.LabelImage.get(roi).wait()
        
        found = False
        for oid in self.mainOperator.labels[t].keys():
            if parent in self.mainOperator.labels[t][oid]:
                found = True
                break
        
        if not found:
            QtGui.QMessageBox.critical(self, "Error", "Error: Cannot find the division label.", QtGui.QMessageBox.Ok)
            return
        
        coords = numpy.where(li == oid)
        self.editor.posModel.slicingPos = [coords[1][0], coords[2][0], coords[3][0]]        
        self.editor.posModel.time = t
    

    def _onMarkMisdetectionPressed(self):
        self.misdetLock = not self.misdetLock             
        self._drawer.markMisdetection.setChecked(not self.misdetLock)
                
        activeTrackBox = self._drawer.activeTrackBox
        
        if self.misdetLock:            
            self.lastActiveTrackIdx = activeTrackBox.currentIndex()
            self._drawer.divEvent.setEnabled(False)
            self._drawer.delTrack.setEnabled(False)
            self._drawer.newTrack.setEnabled(False)
            self._drawer.activeTrackBox.setEnabled(False)
            
            # add -1 to the tracks if not already present
            row = -1
            for idx in range(self._drawer.activeTrackBox.count()):
                if int(self._drawer.activeTrackBox.itemText(idx)) == self.misdetIdx:
                    row = idx
                    break
            if row == -1:
                activeTrackBox.addItem(str(self.misdetIdx), self.ct[-1]) # , QColor(0, 0, 0).rgba()
                row = activeTrackBox.count() - 1
            
            activeTrackBox.setCurrentIndex(row)
            self._currentActiveTrackChanged()
        else:
            activeTrackBox.setCurrentIndex(self.lastActiveTrackIdx)
            self._currentActiveTrackChanged()
            
            self._drawer.divEvent.setEnabled(True)
            self._drawer.delTrack.setEnabled(True)
            self._drawer.newTrack.setEnabled(True)
            self._drawer.activeTrackBox.setEnabled(True)
        
    def _setRanges(self):
        maxt = self.topLevelOperatorView.LabelImage.meta.shape[0] - 1
        maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
        maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
        maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1
        
        from_time = self._drawer.from_time
        to_time = self._drawer.to_time
        from_x = self._drawer.from_x
        to_x = self._drawer.to_x
        from_y = self._drawer.from_y
        to_y = self._drawer.to_y
        from_z = self._drawer.from_z
        to_z = self._drawer.to_z
                
        from_time.setRange(0, to_time.value()-1)        
        to_time.setRange(from_time.value()+1,maxt)      
        
        from_x.setRange(0,to_x.value())
        to_x.setRange(from_x.value(),maxx)
        
        from_y.setRange(0,to_y.value())
        to_y.setRange(from_y.value(),maxy)
        
        from_z.setRange(0,to_z.value())
        to_z.setRange(from_z.value(),maxz)
    
    def _getEvents(self):
        time_range = [int(self._drawer.from_time.value()), int(self._drawer.to_time.value())+1]
        x_range = [int(self._drawer.from_x.value()), int(self._drawer.to_x.value())+1]
        y_range = [int(self._drawer.from_y.value()), int(self._drawer.to_y.value())+1]
        z_range = [int(self._drawer.from_z.value()), int(self._drawer.to_z.value())+1]
        size_range = [int(self._drawer.from_size.value()), int(self._drawer.to_size.value())+1]
        
        oid2tids, alltids = self.mainOperator._getObjects(time_range, x_range, y_range, z_range, size_range, self.misdetIdx)
        if self.misdetIdx in alltids:
            alltids.remove(self.misdetIdx)
        divisions = self.mainOperator.divisions
                
        moves = {}
        divs = {}
        mergers = {}
        apps = {}
        disapps = {}
        multiMoves = {}
        for t in oid2tids.keys():
            moves[t] = []
            divs[t] = []
            mergers[t] = []
            apps[t] = []
            disapps[t] = []
            multiMoves[t] = []
        
        t_start = time_range[0]
        t_end = time_range[1]-1
                            
        for tid in sorted(list(alltids)):
            oid_prev = None            
            
            for t in sorted(oid2tids.keys()):  
                oid_cur = None                
                for o in oid2tids[t].keys():
                    if tid in oid2tids[t][o]:
                        oid_cur = o
#                        found = True
                        break
                       
                if (oid_prev is not None) and (oid_cur is None): # track ends
                    if oid_prev in divisions.keys(): # division
                        [tid_child1, tid_child2], t_div = divisions[oid_prev]
                        oid_child1 = None
                        oid_child2 = None
                        for o in oid2tids[t].keys():
                            if tid_child1 in oid2tids[t][o]:
                                oid_child1 = o
                            if tid_child2 in oid2tids[t][o]:
                                oid_child2 = o
                                          
                        if (t_div == t-1) and (oid_child1 is not None) and (oid_child2 is not None):
                            # check if both children can be found in the next time frame                            
                            child1_exists = (oid_child1 in oid2tids[t].keys())
                            child2_exists = (oid_child2 in oid2tids[t].keys())
                            if child1_exists and child2_exists:
                                divs[t].append((oid_prev,oid_child1,oid_child2,0.))                                
                            elif child1_exists:
                                moves[t].append((oid_prev,oid_child1,0.))
                            elif child2_exists:
                                moves[t].append((oid_prev,oid_child2,0.))
                            
                            break
                                    
                    # else: disappearance
                    disapps[t].append((oid_prev, 0.))                    
                    # do not break, maybe the track starts somewhere else again (due to the size/fov filter)
                
                elif (oid_prev is None) and (t != t_start) and (oid_cur is not None) and (oid_cur not in apps[t]) and (oid_cur not in divisions.keys()): # track starts
                    apps[t].append((oid_cur, 0.))                    
                
                elif (oid_prev is not None) and (oid_cur is not None): # move
                    moves[t].append((oid_prev, oid_cur, 0.))
                    
                    if len(oid2tids[t][oid_cur]) == 1 and len(oid2tids[t-1][oid_prev]) > 1:
                        t_multiprev = None
                        oid_multiprev = None
                                                
                        for tt in reversed(range(t)):
                            for o in oid2tids[tt].keys():
                                if tid in oid2tids[tt][o] and len(oid2tids[tt][o]) == 1:
                                    oid_multiprev = o
                                    t_multiprev = tt                                    
                                    break
                        if t_multiprev is not None and oid_multiprev is not None: 
                            multiMoves[t].append((oid_multiprev, oid_cur, t_multiprev, 0.))
                
                oid_prev = oid_cur
        
        merger_sizes = {}
        for t in oid2tids.keys():
            for oid in oid2tids[t].keys():
                if len(oid2tids[t][oid]) > 1:
                    mergers[t].append((oid, len(oid2tids[t][oid]), 0.))                    
                    m_size = len(oid2tids[t][oid])
                    if m_size not in merger_sizes.keys():
                        merger_sizes[m_size] = 0
                    merger_sizes[m_size] += 1
        
        print 'Merger-Sizes:', merger_sizes
        
        return oid2tids, disapps, apps, divs, moves, mergers, multiMoves
        
        
    def _onExportButtonPressed(self):
        import h5py
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory',os.getenv('HOME'))      
        
        if directory is None or str(directory) == '':
            print "cancelled."
            return
        directory = str(directory)
        
        oid2tids, disapps, apps, divs, moves, mergers, multiMoves = self._getEvents()
        
        
        for t in sorted(oid2tids.keys()):
            fn =  directory + "/" + str(t).zfill(5)  + ".h5"
            print 'Writing file', fn
            
            roi = SubRegion(self.mainOperator.LabelImage, start=[t,0,0,0,0], stop=[t+1,] + list(self.mainOperator.LabelImage.meta.shape[1:]))        
            labelImage = self.mainOperator.LabelImage.get(roi).wait()
            labelImage = labelImage[0,...,0]
             
            dis_at = numpy.asarray(disapps[t])
            app_at = numpy.asarray(apps[t])
            div_at = numpy.asarray(divs[t])
            mov_at = numpy.asarray(moves[t])
            merger_at = numpy.asarray(mergers[t])
            multiMoves_at = numpy.asarray(multiMoves[t])
                    
            # write only if file exists
            with LineageH5(fn, 'a') as f_curr:
                # delete old label image
                if "segmentation" in f_curr.keys():
                    del f_curr["segmentation"]
                
                seg = f_curr.create_group("segmentation")            
                # write label image
                seg.create_dataset("labels", data = labelImage, dtype=numpy.uint32, compression=1)
                
                oids_meta = numpy.unique(labelImage).astype(numpy.uint32)[1:]  
                ones = numpy.ones(oids_meta.shape, dtype=numpy.uint8)
                if 'objects' in f_curr.keys(): del f_curr['objects']
                f_meta = f_curr.create_group('objects').create_group('meta')
                f_meta.create_dataset('id', data=oids_meta, compression=1)
                f_meta.create_dataset('valid', data=ones, compression=1)

                # delete old tracking
                if "tracking" in f_curr.keys():
                    del f_curr["tracking"]
    
                tg = f_curr.create_group("tracking")            
                
                # write associations
                if len(app_at):
                    app_at = numpy.array(sorted(app_at, key=lambda a_entry: a_entry[0]))[::-1]
                    ds = tg.create_dataset("Appearances", data=app_at[:, :-1], dtype=numpy.uint32, compression=1)
                    ds.attrs["Format"] = "cell label appeared in current file"    
                    ds = tg.create_dataset("Appearances-Energy", data=app_at[:, -1], dtype=numpy.double, compression=1)
                    ds.attrs["Format"] = "lower energy -> higher confidence"    
                if len(dis_at):
                    dis_at = numpy.array(sorted(dis_at, key=lambda a_entry: a_entry[0]))[::-1]
                    ds = tg.create_dataset("Disappearances", data=dis_at[:, :-1], dtype=numpy.uint32, compression=1)
                    ds.attrs["Format"] = "cell label disappeared in current file"
                    ds = tg.create_dataset("Disappearances-Energy", data=dis_at[:, -1], dtype=numpy.double, compression=1)
                    ds.attrs["Format"] = "lower energy -> higher confidence"    
                if len(mov_at):
                    mov_at = numpy.array(sorted(mov_at, key=lambda a_entry: a_entry[0]))[::-1]
                    ds = tg.create_dataset("Moves", data=mov_at[:, :-1], dtype=numpy.uint32, compression=1)
                    ds.attrs["Format"] = "from (previous file), to (current file)"    
                    ds = tg.create_dataset("Moves-Energy", data=mov_at[:, -1], dtype=numpy.double, compression=1)
                    ds.attrs["Format"] = "lower energy -> higher confidence"                
                if len(div_at):
                    div_at = numpy.array(sorted(div_at, key=lambda a_entry: a_entry[0]))[::-1]
                    ds = tg.create_dataset("Splits", data=div_at[:, :-1], dtype=numpy.uint32, compression=1)
                    ds.attrs["Format"] = "ancestor (previous file), descendant (current file), descendant (current file)"    
                    ds = tg.create_dataset("Splits-Energy", data=div_at[:, -1], dtype=numpy.double, compression=1)
                    ds.attrs["Format"] = "lower energy -> higher confidence"
                if len(merger_at):
                    merger_at = numpy.array(sorted(merger_at, key=lambda a_entry: a_entry[0]))[::-1]
                    ds = tg.create_dataset("Mergers", data=merger_at[:, :-1], dtype=numpy.uint32, compression=1)
                    ds.attrs["Format"] = "descendant (current file), number of objects"    
                    ds = tg.create_dataset("Mergers-Energy", data=merger_at[:, -1], dtype=numpy.double, compression=1)
                    ds.attrs["Format"] = "lower energy -> higher confidence"
                if len(multiMoves_at):
                    multiMoves_at = numpy.array(sorted(multiMoves_at, key=lambda a_entry: a_entry[0]))[::-1]
                    ds = tg.create_dataset("MultiFrameMoves", data=multiMoves_at[:, :-1], dtype=numpy.uint32, compression=1)
                    ds.attrs["Format"] = "from (file at t_from), to (current file), t_from"    
                    ds = tg.create_dataset("MultiFrameMoves-Energy", data=multiMoves_at[:, -1], dtype=numpy.double, compression=1)
                    ds.attrs["Format"] = "lower energy -> higher confidence"
        
            print "-> results successfully written"
              

    def _onGotoLabel(self):
        t = self._drawer.timeBox.value()
        tid = self._drawer.tidBox.value()
        
        if t < 0 or t >= self.mainOperator.LabelImage.meta.shape[0]:
            QtGui.QMessageBox.critical(self, "Error", "Error: Cannot access time step "  + str(t) + ".", QtGui.QMessageBox.Ok)
            return
        
        roi = SubRegion(self.mainOperator.LabelImage, start=[t,0,0,0,0], stop=[t+1,] + list(self.mainOperator.LabelImage.meta.shape[1:]))
        li = self.mainOperator.LabelImage.get(roi).wait()
        
        found = False
        for oid in self.mainOperator.labels[t].keys():
            if tid in self.mainOperator.labels[t][oid]:
                found = True
                break
        
        if not found:
            QtGui.QMessageBox.critical(self, "Error", "Error: Cannot find track id " + str(tid) + " at time " + str(t) + ".", QtGui.QMessageBox.Ok)
            return
        
        coords = numpy.where(li == oid)
        self.editor.posModel.slicingPos = [coords[1][0], coords[2][0], coords[3][0]]        
        self.editor.posModel.time = t     
    
    def _onPrintMultipleLabelsInTimestep(self):
        maxt = self.mainOperator.LabelImage.meta.shape[0]
        
        affectedTids = {}
        for t in range(maxt):
            affectedTids_at = []
            tids_at= []
            for l in self.mainOperator.labels[t].keys():
                for tid in list(self.mainOperator.labels[t][l]):
                    if tid in tids_at:
                        affectedTids_at.append(tid)
                    tids_at.append(tid)
            affectedTids[t] = affectedTids_at
            
        print 'Multiple Track IDs in one Timestep:'
        print '==================================='
        for t in sorted(affectedTids.keys()):
            for el in sorted(affectedTids[t]):
                print '(t, tid) = ', (t, el)
        
        print 
        print
            
            
    def _onPrintAppearancesInMergers(self):
        maxt = self.mainOperator.LabelImage.meta.shape[0]
    
        oid2tids, disapps, apps, divs, moves, mergers, multiMoves = self._getEvents()
            
        affectedTids = {}
        for t in range(maxt):
            affectedTids_at = []
            if t in apps.keys():
                for app in apps[t]:
                    # FIXME: make a numpy array out of that and search in the first column
                    for merg in mergers[t]:
                        if app[0] == merg[0]:
                            tid = self.mainOperator.labels[t][app[0]]
                            affectedTids_at.append(tid)                            
            if t in disapps.keys():
                if t == 0:
                    continue
                for disapp in disapps[t]:
                        for merg in mergers[t-1]:
                            if disapp[0] == merg[0]:
                                tid = self.mainOperator.labels[t-1][disapp[0]]
                                affectedTids_at.append(tid)
            affectedTids[t] = affectedTids_at
            
        
        print 'Mergers with appearing/disappearing labels:'
        print '==========================================='
        for t in sorted(affectedTids.keys()):
            for el in sorted(affectedTids[t]):
                print '(t, tid) = ', (t, el)
        
        print 
        print
    
    
