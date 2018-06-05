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
#                 http://ilastik.org/license.html
###############################################################################
from __future__ import division
from builtins import range
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtGui import QColor, QPixmap, QIcon, QTextCursor

import sys
import os
import numpy
import vigra
from functools import partial

import logging
from lazyflow.rtype import SubRegion
from copy import copy
from ilastik.utility.gui.threadRouter import threadRouted
from lazyflow.request.request import Request
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility import log_exception
from ilastik.utility import bind
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
from ilastik.applets.base.applet import DatasetConstraintError

import volumina.colortables as colortables
from volumina.api import LazyflowSource, GrayscaleLayer, ColortableLayer
from volumina.utility import ShortcutManager

from ilastik.config import cfg as ilastik_config

import copy

class AnnotationsGui(LayerViewerGui):

    def appletDrawer( self ):
        return self._drawer

    def _loadUiFile(self):
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawerObjects.ui")
        return self._drawer
    
    def initAppletDrawerUi(self):        
        self._drawer = self._loadUiFile()
        
        if not ilastik_config.getboolean("ilastik", "debug"):
            self._drawer.exportTifButton.hide()            
        self._drawer.exportDivisions.hide()
        self._drawer.exportMergers.hide()
        self._drawer.newTrack.pressed.connect(self._onNewTrackPressed)
        self._drawer.delTrack.pressed.connect(self._onDelTrackPressed)        
        self._drawer.divEvent.pressed.connect(self._onDivEventPressed)
        self._drawer.exportMergers.pressed.connect(self._onExportMergersButtonPressed)
        self._drawer.exportDivisions.pressed.connect(self._onExportDivisionsButtonPressed)
        self._drawer.activeTrackBox.currentIndexChanged.connect(self._currentActiveTrackChanged)
        self._drawer.divisionsList.itemActivated.connect(self._onDivisionsListActivated)
        self._drawer.markMisdetection.pressed.connect(self._onMarkMisdetectionPressed)
        self._drawer.exportButton.pressed.connect(self._onExportButtonPressed)
        self._drawer.exportTifButton.pressed.connect(self._onExportTifButtonPressed)
        self._drawer.gotoLabel.pressed.connect(self._onGotoLabel)
        self._drawer.activeTrackBox.setToolTip("Active track label and colour.")

        self.editor.posModel.timeChanged.connect(self.updateTime)

        self.topLevelOperatorView.Labels.setValue(self.topLevelOperatorView.labels)
        self.topLevelOperatorView.Divisions.setValue(self.topLevelOperatorView.divisions)

        self._drawer.logOutput.setVisible(False)
        self._drawer.labelDivisions.setVisible(False)
        self._drawer.divisionsList.setVisible(False)
        self._drawer.timeStepLabel.setVisible(False)
        self._drawer.trackIDLabel.setVisible(False)
        self._drawer.timeBox.setVisible(False)
        self._drawer.tidBox.setVisible(False)
        self._drawer.gotoLabel.setVisible(False)
        self._drawer.automaticTrackingLabel.setVisible(False)
        self._drawer.xLabel.setVisible(False)
        self._drawer.yLabel.setVisible(False)
        self._drawer.zLabel.setVisible(False)
        self._drawer.windowXBox.setVisible(False)
        self._drawer.windowYBox.setVisible(False)
        self._drawer.windowZBox.setVisible(False)
        self._drawer.exportLabel.setVisible(False)
        self._drawer.nextUnlabeledObject.pressed.connect(self.goToNextUnlabeledObject)
        self._drawer.nextUnlabeledDivision.pressed.connect(self.goToNextUnlabeledDivision)
        self._drawer.nextUnlabeledMerger.pressed.connect(self.goToNextUnlabeledMerger)
        self._drawer.nextUnlabeledObjectFrame.pressed.connect(self.goToNextUnlabeledObjectFrame)

        self._drawer.nextUnlabeledObject.setToolTip(
            "Centers the view on the next unlabeled object ordered by time frames.")
        self._drawer.nextUnlabeledObjectFrame.setToolTip(
            "Centers the view on the next unlabeled object in the current time frame.")

        self._drawer.nextUnlabeledDivision.setToolTip(
            "Centers the view on the next unlabeled division with a probability cut-off "+ \
            str(self.divisionProbabilityCutOff)+". " + \
            "Divisions are suggested in the order of increasing probabilities.")
        self._drawer.nextUnlabeledMerger.setToolTip(
            "Centers the view on the next unlabeled merger with a probability cut-off "+ \
            str(self.mergerProbabilityCutOff)+". " + \
            "Mergers are suggested in the order of increasing probabilities.")

        self.topLevelOperatorView.MaxNumObj.notifyDirty(bind(self.updateMergerButtons))
        self.updateMergerButtons()

    def updateMergerButtons(self):
        flag = self.topLevelOperatorView.MaxNumObj.value > 1
        self._drawer.nextUnlabeledMerger.setVisible(flag)

    def goToNextUnlabeledDivision(self):
        self.divFeatures = self.topLevelOperatorView.DivisionProbabilities(list(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0]))).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        labels = self.topLevelOperatorView.labels
        divisions = self.topLevelOperatorView.divisions

        shape = self.topLevelOperatorView.LabelImage.meta.shape
        time_start = 0
        time_stop = shape[0]

        divisionCandidates = []
        for t in range(time_start, time_stop):
            stop = list(shape)
            stop[0] = t+1
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,0,0,0,0],
                                stop=stop)
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                divFlag = False
                if ul in list(labels[t].keys()):
                    trackIDs = list(labels[t][ul])
                    for trackID in trackIDs:
                        if trackID in list(divisions.keys()):
                            divFlag = True
                if not divFlag and ul > 0 and t in range(len(self.divFeatures)) and ul in range(len(self.divFeatures[t])) and \
                                self.divFeatures[t][ul][1]>self.divisionProbabilityCutOff:
                    divisionCandidates.append([t,ul,self.divFeatures[t][ul][1]])
        if divisionCandidates == []:
            self._informationMessage("No more DIVISIONS found for the division probability cut-off {}!".format(self.divisionProbabilityCutOff))
        else:
            sorted(divisionCandidates,key=lambda x:x[2])
            minIndex = 0
            t = divisionCandidates[minIndex][0]
            ul = divisionCandidates[minIndex][1]
            self._gotoObject(ul,t, keepXYZ=False)

            if ul in list(labels[t].keys()) and len(labels[t][ul]) > 0:
                for track in labels[t][ul]:
                    for i in range(self._drawer.activeTrackBox.count()):
                        if int(self._drawer.activeTrackBox.itemText(i)) == track:
                            self._drawer.activeTrackBox.setCurrentIndex(i)
                            break

            feats = self.mainOperator.ObjectFeatures([t]).wait()
            rc = feats[t][default_features_key]['RegionCenter']
            lower = feats[t][default_features_key]['Coord<Minimum>']
            upper = feats[t][default_features_key]['Coord<Maximum>']

            for idx in range(rc.shape[0]):
                if idx == ul:
                    # for 2d data, set z-coordinate to 0:
                    if len(rc[idx]) == 2:
                        x, y = rc[idx]
                        z = 0
                        x_lower, y_lower = lower[idx]
                        x_upper, y_upper = upper[idx]
                        z_lower = 0
                        z_upper = 0
                        dx = abs(x_upper-x_lower)/3
                        dy = abs(y_upper-y_lower)/3
                        d = min([dx,dy])
                    elif len(rc[idx]) == 3:
                        x, y, z = rc[idx]
                        x_lower, y_lower, z_lower = lower[idx]
                        x_upper, y_upper, z_upper = upper[idx]
                        dx = abs(x_upper-x_lower)/3
                        dy = abs(y_upper-y_lower)/3
                        dz = abs(z_upper-z_lower)/3
                        d = min([dx,dy,dz])
                    else:
                        raise DatasetConstraintError ("Tracking", "The RegionCenter feature must have dimensionality 2 or 3.")

                    for imageView in self.editor.imageViews:
                        imageView._croppingMarkers.crop_extents_model.setEditable(True)
                        imageView._croppingMarkers.crop_extents_model.set_volume_shape_3d_cropped(
                            [x_lower-d,y_lower-d,z_lower-d],[x_upper+d,y_upper+d,z_upper+d])
                        imageView._croppingMarkers.setVisible(True)

            return ul, t

        return None, None

    def goToNextUnlabeledMerger(self):
        self.mergerFeatures = self.topLevelOperatorView.DetectionProbabilities(list(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0]))).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        labels = self.mainOperator.labels

        shape = self.topLevelOperatorView.LabelImage.meta.shape
        time_start = 0
        time_stop = shape[0]

        mergerCandidates = []
        for t in range(time_start, time_stop):
            stop = list(shape)
            stop[0] = t+1
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,0,0,0,0],
                                stop=stop)
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                if ul > 0:
                    mergerIndex = 0
                    maxValue = max(self.mergerFeatures[t][ul])
                    index = list(self.mergerFeatures[t][ul]).index(maxValue)
                    if maxValue > self.mergerProbabilityCutOff:
                        mergerIndex = index
                    if mergerIndex >0:
                        if ( t not in labels.keys() or not ul in labels[t].keys()) or( ul in labels[t].keys() and mergerIndex > len(labels[t][ul])):
                            mergerCandidates.append([t,ul,maxValue])

        if mergerCandidates == []:
            self._informationMessage("No more MERGERS found for the merger probability cut-off {}!".format(self.mergerProbabilityCutOff))
        else:
            mergerCandidates = sorted(mergerCandidates,key=lambda x:x[2])
            minIndex = 0
            t = mergerCandidates[minIndex][0]
            ul = mergerCandidates[minIndex][1]
            self._gotoObject(ul,t, keepXYZ=False)
            return ul, t

        return None, None

    def goToNextUnlabeledObject(self):
        labels = self.mainOperator.labels

        shape = self.topLevelOperatorView.LabelImage.meta.shape
        time_start = 0
        time_stop = shape[0]

        for t in range(time_start, time_stop):
            stop = list(shape)
            stop[0] = t+1
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,0,0,0,0],
                                stop=stop)
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                if ul > 0 and (t not in labels.keys() or not ul in labels[t].keys()):
                    self._gotoObject(ul, t, keepXYZ=False)
                    return ul, t

        self._informationMessage("No more UNLABELED objects found!")

        return None, None

    def goToNextUnlabeledObjectFrame(self):

        labels = self.mainOperator.labels
        t = self.editor.posModel.time

        shape = self.topLevelOperatorView.LabelImage.meta.shape
        stop = list(shape)
        stop[0] = t+1
        roi = SubRegion(self.topLevelOperatorView.LabelImage,
                            start=[t,0,0,0,0],
                            stop=stop)
        li = self.topLevelOperatorView.LabelImage.get(roi).wait()
        uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

        for ul in uniqueLabels:
            if ul > 0 and (t not in labels.keys() or not ul in labels[t].keys()):
                self._gotoObject(ul, t, keepXYZ=False)
                return ul, t

        self._informationMessage("No more UNLABELED objects found in the current time frame!")

        return None, None

    def updateTime(self):
        maxTime = self.topLevelOperatorView.LabelImage.meta.shape[0]
        delta = 0 - self.editor.posModel.time
        if delta > 0:
            self.editor.navCtrl.changeTimeRelative(delta)
        else:
            delta = maxTime - self.editor.posModel.time
            if delta < 0:
                self.editor.navCtrl.changeTimeRelative(delta)

    def _initShortcuts(self):
        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        shortcutGroupName = "Training"

        mgr.register( "d", ActionInfo( shortcutGroupName,
                                       "Mark Division Event",
                                       "Mark Division Event (Click on parent object first, then on the two children.)",
                                       self._drawer.divEvent.click,
                                       self._drawer.divEvent,
                                       self._drawer.divEvent ) )
        
        mgr.register( "s", ActionInfo( shortcutGroupName,
                                       "Start New Track",
                                       "Start New Track",
                                       self._drawer.newTrack.click,
                                       self._drawer.newTrack,
                                       self._drawer.newTrack ) )

        mgr.register( "f", ActionInfo( shortcutGroupName,
                                       "Mark False Detection",
                                       "Mark False Detection",
                                       self._drawer.markMisdetection.click,
                                       self._drawer.markMisdetection,
                                       self._drawer.markMisdetection ) )
        
        mgr.register( "q", ActionInfo( shortcutGroupName,
                                       "Increment Active Track ID",
                                       "Increment Active Track ID",
                                       self._incrementActiveTrack,
                                       self,
                                       None ) )
        
        mgr.register( "a", ActionInfo( shortcutGroupName,
                                       "Decrement Active Track ID",
                                       "Decrement Active Track ID",
                                       self._decrementActiveTrack,
                                       self,
                                       None ) ) 
        
    def __init__(self, parentApplet, topLevelOperatorView):
        self.topLevelOperatorView = topLevelOperatorView
        self.divisionProbabilityCutOff = 0.5
        self.mergerProbabilityCutOff = 1/self.topLevelOperatorView.MaxNumObj.value

        super(AnnotationsGui, self).__init__(parentApplet, topLevelOperatorView)
        
        self.mainOperator = topLevelOperatorView
        
        self.applet = self.mainOperator.parent.parent.annotationsApplet
        
        self.mainOperator.LabelImage.notifyMetaChanged( self._onMetaChanged)
        self.mainOperator.LabelImage.notifyDirty( self._reset )

        self.ct = colortables.create_random_16bit()
        
        self.divLock = False
        self.divs = []
        self.labelsWithDivisions = {}
        self.misdetLock = False
        self.misdetIdx = -1

        if self.mainOperator.LabelImage.meta.shape:
            # FIXME: assumes t,x,y,z,c
            if self.mainOperator.LabelImage.meta.shape[3] == 1: # 2D images
                self._drawer.windowZBox.setValue(1)
                self._drawer.windowZBox.setEnabled(False)
        
        self._initShortcuts()
        self.editor.posModel.timeChanged.connect(self.updateTime)
        try:
            self.editor.navCtrl.changeTimeRelative(0 - self.editor.posModel.time)
        except:
            pass

        self.features = self.topLevelOperatorView.ObjectFeatures(list(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0]))).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        self._initAnnotations()

        self.__cleanup_fns = []
        self.topLevelOperatorView.Labels.notifyDirty( bind(self._updateLabels) )

        self.volumeEditorWidget.quadViewStatusBar.setToolTipTimeButtons(True)
        self.volumeEditorWidget.quadViewStatusBar.setToolTipTimeSlider(True)
        self.deleteAllTraining = False

    def _onInitializeAnnotations(self):
        self._questionMessage("All your annotations will be lost! You should save the project, " + \
                                  "then save it under a new name and continue without loss of current annotations. " + \
                                  "Do you really want to delete all your annotations?")

        if self.deleteAllTraining:
            self.mainOperator.Annotations.setValue({})
            self.deleteAllTraining = False
        else:
            return
        self.mainOperator.Divisions.setValue({})
        self.mainOperator.Labels.setValue({})

        self.mainOperator.divisions = {}
        self.labelsWithDivisions = {}
        self.divs = []

        roi = {}
        roi["start"]=(0,0,0,0,0)
        roi["stop"]=self.mainOperator.TrackImage.meta.shape

        self.divLock = False
        self.misdetLock = False
        self.misdetIdx = -1

        self.mainOperator.initOutputs()

        self._reset()

        self._setDirty(self.mainOperator.LabelImage, list(range(self.mainOperator.TrackImage.meta.shape[0])))
        self._setDirty(self.mainOperator.Labels, list(range(self.mainOperator.TrackImage.meta.shape[0])))
        self._setDirty(self.mainOperator.Divisions, list(range(self.mainOperator.TrackImage.meta.shape[0])))
        self._setDirty(self.mainOperator.Appearances, list(range(self.mainOperator.TrackImage.meta.shape[0])))
        self._setDirty(self.mainOperator.Disappearances, list(range(self.mainOperator.TrackImage.meta.shape[0])))
        self._setDirty(self.mainOperator.TrackImage, list(range(self.mainOperator.TrackImage.meta.shape[0])))
        self._setDirty(self.mainOperator.UntrackedImage, list(range(self.mainOperator.TrackImage.meta.shape[0])))

        self.setupLayers()

    def stopAndCleanUp(self):
        super(AnnotationsGui, self).stopAndCleanUp()

        for fn in self.__cleanup_fns:
            fn()

    def _updateLabels(self):
        pass

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

    def _initAnnotations(self):
        self._onSaveAnnotations()
        self._onSaveAppearances()
        self._onSaveDisappearances()

        self.topLevelOperatorView.Labels.setValue(self.topLevelOperatorView.labels)
        self.topLevelOperatorView.Divisions.setValue(self.topLevelOperatorView.divisions)
        self.topLevelOperatorView.Appearances.setValue(self.topLevelOperatorView.appearances)
        self.topLevelOperatorView.Disappearances.setValue(self.topLevelOperatorView.disappearances)

    def _onSaveAnnotations(self, time=None, label=None, time_interval=None, delete=False, track=None, division=False):

        if division:
            if "divisions" not in self.topLevelOperatorView.Annotations.value.keys():
                self.topLevelOperatorView.Annotations.value["divisions"] = {}

            for parentTrack in self.topLevelOperatorView.divisions.keys():
                t = self.topLevelOperatorView.divisions[parentTrack][1]
                child1Track = self.topLevelOperatorView.divisions[parentTrack][0][0]
                child2Track = self.topLevelOperatorView.divisions[parentTrack][0][1]

                parent = self.getLabel(t, parentTrack)
                child1 = self.getLabel(t+1, child1Track)
                child2 = self.getLabel(t+1, child2Track)

                if not (parent and child1 and child2):
                    logger.info("WARNING:Your divisions and labels do not match for time {} and parent track {} with label {}!".format(t,parentTrack,parent))
                    pass
                else:
                    if parentTrack not in self.topLevelOperatorView.Annotations.value["divisions"].keys():
                        self.topLevelOperatorView.Annotations.value["divisions"][parentTrack] = {}
                    self.topLevelOperatorView.Annotations.value["divisions"][parentTrack] = self.topLevelOperatorView.divisions[parentTrack]
        else:

            if "labels" not in self.topLevelOperatorView.Annotations.value.keys():
                self.topLevelOperatorView.Annotations.value["labels"] = {}

            if time is not None and label is not None and track is not None:
                if time not in self.topLevelOperatorView.Annotations.value["labels"].keys():
                    self.topLevelOperatorView.Annotations.value["labels"][time] = {}
                self.topLevelOperatorView.Annotations.value["labels"][time][label] = self.topLevelOperatorView.labels[time][label]

            elif delete and time_interval is not None and time_interval[0] is not None and time_interval[1] is not None and label is not None and track is not None:
                time_range = range(time_interval[0],time_interval[1])
                if time_interval[1] == time_interval[0]+1:
                    t = time_interval[0]

                    if t in self.topLevelOperatorView.labels.keys():
                        if label in self.topLevelOperatorView.Annotations.value["labels"][t].keys():
                            if track in self.topLevelOperatorView.Annotations.value["labels"][t][label]:
                                self.topLevelOperatorView.Annotations.value["labels"][t][label].remove(track)
                                if len(self.topLevelOperatorView.Annotations.value["labels"][t][label]) == 0:
                                    del self.topLevelOperatorView.Annotations.value["labels"][t][label]
                else:
                    annotations = copy.deepcopy(self.topLevelOperatorView.Annotations.value)
                    for t in time_range:
                        if t in annotations["labels"].keys():
                            labelsT = annotations["labels"][t].keys()
                            for lab in labelsT:
                                if lab in labelsT:
                                    trackSet = annotations["labels"][t][lab]
                                    for tr in trackSet:
                                        if track == tr:
                                            self.topLevelOperatorView.Annotations.value["labels"][t][lab].remove(track)
                                if len(self.topLevelOperatorView.Annotations.value["labels"][t][lab]) == 0:
                                    del self.topLevelOperatorView.Annotations.value["labels"][t][lab]

            elif time_interval is not None and time_interval[0] is not None and time_interval[1] is not None and label is not None and track is not None:
                time_range = range(time_interval[0],time_interval[1])
                for t in time_range:
                    if t not in self.topLevelOperatorView.labels.keys():
                        self.topLevelOperatorView.labels[t] = {}
                    if label not in self.topLevelOperatorView.labels[t].keys():
                        self.topLevelOperatorView.labels[t][label] = set()
                    self.topLevelOperatorView.labels[t][label].add(track)

                    if t not in self.topLevelOperatorView.Annotations.value["labels"].keys():
                        self.topLevelOperatorView.Annotations.value["labels"][t] = {}
                    self.topLevelOperatorView.Annotations.value["labels"][t][label] = self.topLevelOperatorView.labels[t][label]
            else:
                for t in self.topLevelOperatorView.labels.keys():
                    for lab in self.topLevelOperatorView.labels[t].keys():
                        if t not in self.topLevelOperatorView.Annotations.value["labels"].keys():
                            self.topLevelOperatorView.Annotations.value["labels"][t] = {}
                        if lab not in self.topLevelOperatorView.Annotations.value["labels"][t].keys():
                            self.topLevelOperatorView.Annotations.value["labels"][t][lab] = self.topLevelOperatorView.labels[t][lab]

                if "divisions" in self.topLevelOperatorView.Annotations.value.keys() and self.topLevelOperatorView.Annotations.value["divisions"] == {} and \
                        "labels" in self.topLevelOperatorView.Annotations.value.keys() and self.topLevelOperatorView.Annotations.value["labels"] == {}:
                    annotations = self.topLevelOperatorView.Annotations.value
                    del annotations["labels"]
                    del annotations["divisions"]
                    self.topLevelOperatorView.Annotations.setValue(annotations)

                for t in self.topLevelOperatorView.labels.keys():
                    for lab in self.topLevelOperatorView.labels[t].keys():
                        if t not in self.topLevelOperatorView.Annotations.value["labels"].keys() and lab in self.topLevelOperatorView.Annotations.value["labels"][t].keys():
                            del self.topLevelOperatorView.labels[t][lab]

        self._setDirty(self.mainOperator.Annotations, list(range(self.mainOperator.TrackImage.meta.shape[0])))
        self._setDirty(self.mainOperator.Labels, list(range(self.mainOperator.TrackImage.meta.shape[0])))
        self._setDirty(self.mainOperator.Divisions, list(range(self.mainOperator.TrackImage.meta.shape[0])))

    def _onSaveAppearances(self):
        self.topLevelOperatorView.Appearances.setValue({})
        for t in self.topLevelOperatorView.appearances.keys():
            for oid in self.topLevelOperatorView.appearances[t].keys():
                for track in self.topLevelOperatorView.appearances[t][oid].keys():
                    if t not in self.topLevelOperatorView.Appearances.value.keys():
                        self.topLevelOperatorView.Appearances.value[t] = {}
                    if oid not in self.topLevelOperatorView.Appearances.value[t].keys():
                        self.topLevelOperatorView.Appearances.value[t][oid] = {}
                    if track not in self.topLevelOperatorView.Appearances.value[t][oid].keys():
                        self.topLevelOperatorView.Appearances.value[t][oid][track] = self.topLevelOperatorView.appearances[t][oid][track]

        self._setDirty(self.mainOperator.Appearances, list(range(self.mainOperator.TrackImage.meta.shape[0])))

    def _onSaveDisappearances(self):
        self.topLevelOperatorView.Disappearances.setValue({})
        for t in self.topLevelOperatorView.disappearances.keys():
            for oid in self.topLevelOperatorView.disappearances[t].keys():
                for track in self.topLevelOperatorView.disappearances[t][oid].keys():
                    if t not in self.topLevelOperatorView.Disappearances.value.keys():
                        self.topLevelOperatorView.Disappearances.value[t] = {}
                    if oid not in self.topLevelOperatorView.Disappearances.value[t].keys():
                        self.topLevelOperatorView.Disappearances.value[t][oid] = {}
                    if track not in self.topLevelOperatorView.Disappearances.value[t][oid].keys():
                        self.topLevelOperatorView.Disappearances.value[t][oid][track] = self.topLevelOperatorView.disappearances[t][oid][track]

        self._setDirty(self.mainOperator.Disappearances, list(range(self.mainOperator.TrackImage.meta.shape[0])))

    def getLabel(self, time, track):
        for label in list(self.mainOperator.labels[time].keys()):
            if self.mainOperator.labels[time][label] == set([track]):
                return label
        return False

    def updateTime(self):
        maxTime = self.topLevelOperatorView.LabelImage.meta.shape[0]
        delta = 0 - self.editor.posModel.time
        if delta > 0:
            self.editor.navCtrl.changeTimeRelative(delta)
        else:
            delta = maxTime - self.editor.posModel.time
            if delta < 0:
                self.editor.navCtrl.changeTimeRelative(delta)

    def setupLayers( self ):
        layers = []
 
        self.ct[0] = QColor(0,0,0,0).rgba()
        self.ct[255] = QColor(0,0,0,255).rgba()
        self.ct[-1] = QColor(0,0,0,255).rgba()       
        
        if self.topLevelOperatorView.TrackImage.ready():
            self.trackingsrc = LazyflowSource( self.topLevelOperatorView.TrackImage )
            trackingLayer = ColortableLayer( self.trackingsrc, self.ct )
            trackingLayer.name = "Tracking Annotations"
            trackingLayer.visible = True
            trackingLayer.opacity = 0.8

            def toggleTrackingVisibility():
                trackingLayer.visible = not trackingLayer.visible
                
            trackingLayer.shortcutRegistration = ( "e", ShortcutManager.ActionInfo( 
                                                            "Layer Visibilities",
                                                            "Toggle Structured Tracking Layer Visibility",
                                                            "Toggle Structured Tracking Layer Visibility",
                                                            toggleTrackingVisibility,
                                                            self,
                                                            trackingLayer ) )
            layers.append(trackingLayer)
        
        
        if self.topLevelOperatorView.UntrackedImage.ready():
            ct = colortables.create_random_16bit()
            for i in range(len(ct)):
                ct[i] = QColor(230,0,0,150).rgba() 
            ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
            self.untrackedsrc = LazyflowSource( self.topLevelOperatorView.UntrackedImage )
            untrackedLayer = ColortableLayer( self.untrackedsrc, ct )
            untrackedLayer.name = "Untracked Objects"
            untrackedLayer.visible = False
            untrackedLayer.opacity = 0.8
            layers.append(untrackedLayer)
        
        if self.topLevelOperatorView.LabelImage.ready():
            ct = colortables.create_random_16bit()
            for i in range(len(ct)):
                ct[i] = QColor(255,255,0,100).rgba()
            ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
            self.objectssrc = LazyflowSource( self.topLevelOperatorView.LabelImage )             
            objLayer = ColortableLayer( self.objectssrc, ct )
            objLayer.name = "Objects"
            objLayer.opacity = 0.8
            objLayer.visible = True
            
            def toggleObjectVisibility():
                objLayer.visible = not objLayer.visible
                
            objLayer.shortcutRegistration = ( "r", ShortcutManager.ActionInfo(
                                                       "Layer Visibilities",
                                                       "Toggle Objects Layer Visibility",
                                                       "Toggle Objects Layer Visibility",
                                                       toggleObjectVisibility,
                                                       self,
                                                       objLayer ) )            
            layers.append(objLayer)


        if self.mainOperator.RawImage.ready():
            self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
            rawLayer = GrayscaleLayer( self.rawsrc )
            rawLayer.name = "Raw"        
            layers.insert( len(layers), rawLayer )   
        
        
        self.topLevelOperatorView.RawImage.notifyReady( self._onReady )
        self.topLevelOperatorView.RawImage.notifyMetaChanged( self._onMetaChanged )

        self._reset()
        return layers

    @threadRouted
    def _reset(self, *args, **kwargs):
        self._setDivisionsList()
        self._setActiveTrackList()
        self._drawer.logOutput.clear()

    @threadRouted
    def _addDivisionToListWidget(self, trackid, child1, child2, t_parent):
        divItem = QtWidgets.QListWidgetItem("%d: %d, %d" % (trackid, child1, child2))
        divItem.setBackground(QColor(self.ct[trackid]))
        divItem.setCheckState(False)
        self._drawer.divisionsList.addItem(divItem)
        if t_parent not in list(self.labelsWithDivisions.keys()):
            self.labelsWithDivisions[t_parent] = []
        if t_parent+1 not in list(self.labelsWithDivisions.keys()):
            self.labelsWithDivisions[t_parent+1] = []
        self.labelsWithDivisions[t_parent].append(trackid)
        self.labelsWithDivisions[t_parent+1].append(child1)
        self.labelsWithDivisions[t_parent+1].append(child2)

    @threadRouted
    def _setDivisionsList(self):
        self._drawer.divisionsList.clear()

        for trackid in list(self.mainOperator.divisions.keys()):
            self._addDivisionToListWidget(trackid, self.mainOperator.divisions[trackid][0][0], self.mainOperator.divisions[trackid][0][1],
                                          self.mainOperator.divisions[trackid][-1])
        # set all items checked
        for idx in range(self._drawer.divisionsList.count()):
            self._drawer.divisionsList.item(idx).setCheckState(True)

    @threadRouted
    def _setActiveTrackList(self):
        activeTrackBox = self._drawer.activeTrackBox

        activeTrackBox.clear()

        allTracks = set()
        for t in list(self.mainOperator.labels.keys()):            
            for oid in list(self.mainOperator.labels[t].keys()):
                for tr in list(self.mainOperator.labels[t][oid]):
                    allTracks.add(tr)        
        
        items = set()
        for idx in range(activeTrackBox.count()):
            items.add(int(activeTrackBox.itemText(idx)))
            
        for tid in sorted(allTracks):
            if tid not in items:
                pm = QPixmap(16,16)
                pm.fill(QColor(self.ct[tid]))
                activeTrackBox.insertItem(tid, QIcon(pm), str(tid))

        if activeTrackBox.count() >= 1:
            activeTrackBox.setCurrentIndex(activeTrackBox.count()-1)
    
    def _incrementActiveTrack(self):
        activeTrackBox = self._drawer.activeTrackBox
        if not activeTrackBox.isEnabled():
            return
        ind = activeTrackBox.currentIndex()
        if ind+1 < activeTrackBox.count():            
            activeTrackBox.setCurrentIndex(ind+1)

    def _decrementActiveTrack(self):
        activeTrackBox = self._drawer.activeTrackBox
        if not activeTrackBox.isEnabled():
            return
        ind = activeTrackBox.currentIndex()
        if ind-1 >= 0:            
            activeTrackBox.setCurrentIndex(ind-1)
                    
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
        elif slot is self.mainOperator.Annotations:
            self.mainOperator.Annotations.setDirty([])
        elif slot is self.mainOperator.Appearances:
            self.mainOperator.Appearances.setDirty([])
        elif slot is self.mainOperator.Disappearances:
            self.mainOperator.Disappearances.setDirty([])
        elif slot is self.mainOperator.Divisions:
            self.mainOperator.Divisions.setDirty([])
        elif slot is self.mainOperator.UntrackedImage:
            roi = SubRegion(self.mainOperator.UntrackedImage, start=[min(timesteps),] + 4*[0,], stop=[max(timesteps)+1,] + list(self.mainOperator.TrackImage.meta.shape[1:]))
            self.mainOperator.UntrackedImage.setDirty(roi)

    def handleEditorLeftClick(self, position5d, globalWindowCoordiante):

        if self.divLock:
            oid = self._getObject(self.mainOperator.LabelImage, position5d)
            if not oid == 0:
                item = (position5d[0], oid)
                if len(self.divs) == 0:
                    self.divs.append(item)
                    self._setPosModel(time=self.editor.posModel.time + 1)
                elif len(self.divs) > 0:
                    if position5d[0] != self.divs[0][0] + 1:
                        self._criticalMessage("Error: The daughter cells are expected to be in time step " + str(self.divs[0][0] + 1))
                        return
                    if item not in self.divs:
                        self.divs.append(item)

                if len(self.divs) == 3:
                    activeTrack = self._getActiveTrack()
                    if (self.divs[0][1] not in self.mainOperator.labels[self.divs[0][0]]) or (activeTrack not in self.mainOperator.labels[self.divs[0][0]][self.divs[0][1]]):
                        self._criticalMessage("Error: The label of the parent cell must match the active track label.")
                        self.divLock = False
                        self.divs = []
                        self._drawer.divEvent.setChecked(False)
                        self._drawer.divEvent.setText("Division Event")
                        self._enableButtons(enable=True)
                        return

                    div = [activeTrack,]

                    for i in range(1,3):
                        activeTrack = self._addNewTrack()
                        self._addObjectToTrack(activeTrack, self.divs[i][1], self.divs[i][0])
                        div += [activeTrack,]

                    self._addDivisionToListWidget(div[0], div[1], div[2], self.editor.posModel.time-1)

                    self.mainOperator.divisions[div[0]] = (div[1:], self.divs[0][0])
                    self._log('division (t,parent,child1,child2) = ' + str((self.editor.posModel.time-1, div[0], div[1], div[2])) + ' added.')

                    self._setDirty(self.mainOperator.Divisions, [])
                    self._setDirty(self.mainOperator.Labels, [self.divs[0][0],self.divs[0][0]+1])
                    self._setDirty(self.mainOperator.TrackImage, [self.divs[0][0]])
                    self._setDirty(self.mainOperator.UntrackedImage, [self.divs[0][0]])

                    # release the division lock
                    self.divLock = False
                    self.divs = []
                    self._drawer.divEvent.setChecked(False)
                    self._drawer.divEvent.setText("Division Event")
                    self._enableButtons(exceptButtons=[self._drawer.divEvent], enable=True)
            self._onSaveAnnotations(division=True)
        else:

            for imageView in self.editor.imageViews:
                imageView._croppingMarkers.setVisible(False)

            oid = self._getObject(self.mainOperator.LabelImage, position5d)
            if oid == 0:
                return
                    
            activeTrack = self.mainOperator.ActiveTrack
            if not activeTrack.ready() or activeTrack.value == 0:
                self._criticalMessage("Error: Please start a new track first.")            
                return        
            activeTrack = activeTrack.value
            
            t = position5d[0]

            res = self._addObjectToTrack(activeTrack,oid,t)

            if res == -99 or res == -98:
                self._informationMessage("Info: Object " + str(oid) + " in time frame " + str(t) + " is outside the current crop.")
                return
            elif res == -1:
                return
            elif res == -2:
                self._setPosModel(time=self.editor.posModel.time + 1)
                return
            
            self._setDirty(self.mainOperator.TrackImage, [t])
            self._setDirty(self.mainOperator.UntrackedImage, [t])
            self._setDirty(self.mainOperator.Labels, [t])
    
            self._setPosModel(time=self.editor.posModel.time + 1)

            self._onSaveAnnotations(time=t,label=oid,track=activeTrack)

    def handleEditorRightClick(self, position5d, globalWindowCoordiante):

        if self.divLock:
            return

        for imageView in self.editor.imageViews:
            imageView._croppingMarkers.setVisible(False)

        oid = self._getObject(self.mainOperator.LabelImage, position5d)
        if oid == 0:
            return
        
        t = position5d[0]
        activeTrack = self._getActiveTrack()
        
        trackids = []
        if t in list(self.mainOperator.labels.keys()) and oid in list(self.mainOperator.labels[t].keys()):
            for l in self.mainOperator.labels[t][oid]:
                trackids.append(l)
        
        title = "Object " + str(oid)
        if len(trackids) == 0:
            title += " contains no track ids."
        elif len(trackids) == 1:
            title += " contains track id " + str(trackids[0]) + "."
        else:
            title += " contains track ids " + str(trackids) + "."
        menu = QtWidgets.QMenu( self )
        
        menuTitle = QtWidgets.QAction(title, menu)
        font = menuTitle.font()
        font.setItalic(True)
        font.setBold(True)
        menuTitle.setFont(font)
        menuTitle.setEnabled(False)
        menu.addAction(menuTitle)
        menu.addSeparator()
        
        delLabel = {}
        delSubtrackToEnd = {}
        delSubtrackToStart = {}
        setActiveTrack = {}
        runTracking = {}
        markAppearance = {}
        markDisappearance = {}
        removeAppearance = {}
        removeDisappearance = {}
        maxTime = self.topLevelOperatorView.LabelImage.meta.shape[0]

        delDivision = {}
        if activeTrack != self.misdetIdx:
            for trackid in trackids:
                if trackid in list(self.mainOperator.divisions.keys()) and self.mainOperator.divisions[trackid][1] == t:
                    text = "remove division event from track " + str(trackid)
                    delDivision[text] = trackid
                    menu.addSeparator()
                    menu.addAction(text)

        divisionChildren = []
        for divTrack in list(self.mainOperator.divisions.keys()):
            if self.mainOperator.divisions[divTrack][1] == t-1:
                divisionChildren.append(self.mainOperator.divisions[divTrack][0][0])
                divisionChildren.append(self.mainOperator.divisions[divTrack][0][1])

        for l in trackids:
            if activeTrack != self.misdetIdx and t < maxTime:
                text = "run automatic tracking for object " + str(oid) + " with track " + str(l)
                runTracking[text] = l
                menu.addAction(text)

            text = "set active track to " + str(l)
            setActiveTrack[text] = l
            menu.addAction(text)

            text = "remove track " + str(l) + " for object " + str(oid)
            delLabel[text] = l
            menu.addAction(text)

            if l != self.misdetIdx:
                if t < maxTime:
                    text = "remove track " + str(l) + " from here to end"
                    delSubtrackToEnd[text] = l
                    menu.addAction(text)

                if t > 0:
                    text = "remove track " + str(l) + " from here to start"
                    delSubtrackToStart[text] = l
                    menu.addAction(text)

            menu.addSeparator()

            isAppearance = self._isAppearance(t,oid,l)
            isDisappearance = self._isDisappearance(t,oid,l)

            opTracking = self.mainOperator.parent.parent.trackingApplet.topLevelOperator[0]
            if isAppearance:
                text = "remove appearance from track " + str(l)
                removeAppearance[text] = l
                menu.addAction(text)
            elif opTracking._type(t,l)[0] in ["FIRST","SINGLETON(FIRST_LAST)"] and t >0 and l not in divisionChildren:
                text = "mark appearance for track " + str(l)
                markAppearance[text] = l
                menu.addAction(text)

            if isDisappearance:
                text = "remove disappearance from track " + str(l)
                removeDisappearance[text] = l
                menu.addAction(text)
            elif opTracking._type(t,l)[0] in ["LAST","SINGLETON(FIRST_LAST)"] and t < maxTime-1 and l not in delDivision.values():
                text = "mark disappearance for track " + str(l)
                markDisappearance[text] = l
                menu.addAction(text)

            menu.addSeparator()
        
        action = menu.exec_(globalWindowCoordiante)
        if action is None:
            return

        selection = str(action.text())

        if selection in list(markAppearance.keys()):
            self._markAppearance(t,oid, markAppearance[selection])
            self._onSaveAppearances()
            self._setDirty(self.mainOperator.Appearances, [t])

        elif selection in list(markDisappearance.keys()):
            self._markDisappearance(t,oid, markDisappearance[selection])
            self._onSaveDisappearances()
            self._setDirty(self.mainOperator.Disappearances, [t])

        elif selection in list(removeAppearance.keys()):
            self._removeAppearance(t,oid, removeAppearance[selection])
            self._onSaveAppearances()
            self._setDirty(self.mainOperator.Appearances, [t])

        elif selection in list(removeDisappearance.keys()):
            self._removeDisappearance(t,oid, removeDisappearance[selection])
            self._onSaveDisappearances()
            self._setDirty(self.mainOperator.Disappearances, [t])

        elif selection in list(delLabel.keys()):
            self._delLabel(t, oid, delLabel[selection])
            
            self._setDirty(self.mainOperator.TrackImage, [t])
            self._setDirty(self.mainOperator.UntrackedImage, [t])
            self._setDirty(self.mainOperator.Labels, [t])
            self._onSaveAnnotations(time_interval=[t,t+1],label=oid,track=delLabel[selection],delete=True)
            self._onSaveAppearances()
            self._onSaveDisappearances()

        elif selection in list(delSubtrackToEnd.keys()):
            track2remove = delSubtrackToEnd[selection]
            maxt = self.mainOperator.LabelImage.meta.shape[0]
            for time in range(t,maxt):
                for oid in list(self.mainOperator.labels[time].keys()):
                    if track2remove in self.mainOperator.labels[time][oid]:
                        self._delLabel(time, oid, track2remove)
            
            self._setDirty(self.mainOperator.TrackImage, list(range(t,maxt)))
            self._setDirty(self.mainOperator.UntrackedImage, list(range(t, maxt)))
            self._setDirty(self.mainOperator.Labels, list(range(t,maxt)))
            self._onSaveAnnotations(time_interval=[t,maxt],label=oid,track=track2remove,delete=True)
            self._onSaveAppearances()
            self._onSaveDisappearances()

        elif selection in list(delSubtrackToStart.keys()):
            track2remove = delSubtrackToStart[selection]
            for time in range(0,t+1):
                for oid in list(self.mainOperator.labels[time].keys()):
                    if track2remove in self.mainOperator.labels[time][oid]:
                        self._delLabel(time, oid, track2remove)
            
            self._setDirty(self.mainOperator.TrackImage, list(range(0,t+1)))
            self._setDirty(self.mainOperator.UntrackedImage, list(range(0,t+1)))
            self._setDirty(self.mainOperator.Labels, list(range(0,t+1)))
            self._onSaveAnnotations(time_interval=[0,t+1],label=oid,track=track2remove,delete=True)
            self._onSaveAppearances()
            self._onSaveDisappearances()

        elif selection in list(runTracking.keys()):
            self._runSubtracking(position5d, oid, runTracking[selection])
            self._onSaveAnnotations(time_interval=[t,maxTime],label=oid,track=activeTrack)

        elif selection in list(delDivision.keys()):
            self._delDivisionEvent(delDivision[selection])
            self._onSaveAnnotations()
            self._onSaveAppearances()
            self._onSaveDisappearances()

        elif selection in list(setActiveTrack.keys()):
            for i in range(self._drawer.activeTrackBox.count()):
                if int(self._drawer.activeTrackBox.itemText(i)) == setActiveTrack[selection]:
                    self._drawer.activeTrackBox.setCurrentIndex(i)

        else:
            assert False, "cannot reach this"

        opTrackingTmp = self.mainOperator.parent.parent.trackingApplet.topLevelOperator[0]

    def handleEditorToolTip(self, position5d, globalWindowCoordiante):
        oid = self._getObject(self.mainOperator.LabelImage, position5d)
        trackids = []
        t = position5d[0]
        if t in list(self.mainOperator.labels.keys()) and oid in list(self.mainOperator.labels[t].keys()):
            for l in self.mainOperator.labels[t][oid]:
                trackids.append(l)

        if self.divLock:
            if len(self.divs)==0:
                self.setToolTip("Left click on a parent, then left click on each of the children to annotate a division.")
            elif len(self.divs)==1:
                self.setToolTip("Left click on a child.")
            if len(self.divs)==2:
                self.setToolTip("Left click on the second child.")
        elif oid == 0:
            self.setToolTip("Move your mouse to an object you would like to label!")
        elif trackids == []:
            self.setToolTip("Left click to add the active track to this unlabelled object. Right click for more options.")
        else:
            self.setToolTip("Left click to add the active track to this object. Right click for more options.")
        return


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

        self._onSaveAnnotations()
        self._onSaveAppearances()
        self._onSaveDisappearances()

    def _currentActiveTrackChanged(self):
        self.mainOperator.ActiveTrack.setValue(self._getActiveTrack())

    def _getActiveTrack(self):
        if self._drawer.activeTrackBox.count() > 0:
            return int(self._drawer.activeTrackBox.currentText())
        else:
            return 0
        
    def _addNewTrack(self):
        activeTrackBox = self._drawer.activeTrackBox
        allTracks = [int(activeTrackBox.itemText(i)) for i in range(activeTrackBox.count())]
        if len(allTracks) == 0:
            activeTrackBox.addItem(str(1), self.ct[1])
        else:
            # lowest id of a real track should be at least 1
            # there could be already only negative or zero ids in the list
            # (negative track ids are use for special cases like misdetections)
            newTrack = max(allTracks + [0,])+1
            
            # avoid these track ids due to inappropriate colors 
            if newTrack % 255 == 0:
                newTrack += 2
            elif newTrack % 256 == 0:
                newTrack += 1
            pm = QPixmap(16,16)
            pm.fill(QColor(self.ct[newTrack]))
            activeTrackBox.insertItem(newTrack, QIcon(pm), str(newTrack))
        activeTrackBox.setCurrentIndex(activeTrackBox.count()-1)
        return self._getActiveTrack()
        
    def _onNewTrackPressed(self):
        self._addNewTrack()
    
    def _delLabel(self, t, oid, track2remove, errorMessage=True):
        if t in list(self.labelsWithDivisions.keys()) and track2remove in self.labelsWithDivisions[t] and errorMessage:
            self._criticalMessage("Error: Cannot remove label " + str(track2remove) +
                                       " at t=" + str(t) + ", since it is involved in a division event." + 
                                       " Remove division event first by right clicking on the parent.")
            self._gotoObject(oid, t)
            return False
        
        self.mainOperator.labels[t][oid].remove(track2remove)
        if len(self.mainOperator.labels[t][oid])==0:
            res = self.mainOperator.labels
            del res[t][oid]
            self.mainOperator.labels = res
        self._setDirty(self.mainOperator.Labels, [t])
        self._setDirty(self.mainOperator.TrackImage, [t])
        self._setDirty(self.mainOperator.UntrackedImage, [t])

        return True

    def _markAppearance(self,t,oid,track):
        if t not in self.mainOperator.appearances.keys():
            self.mainOperator.appearances[t] = {}
        if oid not in self.mainOperator.appearances[t].keys():
            self.mainOperator.appearances[t][oid] ={}
        if track not in self.mainOperator.appearances[t][oid].keys():
            self.mainOperator.appearances[t][oid][track] = True
        self._setDirty(self.mainOperator.Appearances, [t])

    def _removeAppearance(self,t,oid,track):
        if t in self.mainOperator.appearances.keys() and oid in self.mainOperator.appearances[t].keys() and track in self.mainOperator.appearances[t][oid].keys():
            del self.mainOperator.appearances[t][oid][track]

            if self.mainOperator.appearances[t][oid] == {}:
                del self.mainOperator.appearances[t][oid]

                if self.mainOperator.appearances[t] == {}:
                    del self.mainOperator.appearances[t]

        self._setDirty(self.mainOperator.Appearances, [t])

    def _markDisappearance(self,t,oid,track):
        if t not in self.mainOperator.disappearances.keys():
            self.mainOperator.disappearances[t] = {}
        if oid not in self.mainOperator.disappearances[t].keys():
            self.mainOperator.disappearances[t][oid] ={}
        if track not in self.mainOperator.disappearances[t][oid].keys():
            self.mainOperator.disappearances[t][oid][track] = True
        self._setDirty(self.mainOperator.Disappearances, [t])

    def _removeDisappearance(self,t,oid,track):
        if t in self.mainOperator.disappearances.keys() and oid in self.mainOperator.disappearances[t].keys() and track in self.mainOperator.disappearances[t][oid].keys():
            del self.mainOperator.disappearances[t][oid][track]

            if self.mainOperator.disappearances[t][oid] == {}:
                del self.mainOperator.disappearances[t][oid]

                if self.mainOperator.disappearances[t] == {}:
                    del self.mainOperator.disappearances[t]

        self._setDirty(self.mainOperator.Disappearances, [t])

    def _isAppearance(self,time,oid,label):
        if time in self.mainOperator.appearances.keys() and oid in self.mainOperator.appearances[time].keys() and label in self.mainOperator.appearances[time][oid].keys():
            return self.mainOperator.appearances[time][oid][label]
        else:
            return False

    def _isDisappearance(self,time,oid,label):
        if time in self.mainOperator.disappearances.keys() and oid in self.mainOperator.disappearances[time].keys() and label in self.mainOperator.disappearances[time][oid].keys():
            return self.mainOperator.disappearances[time][oid][label]
        else:
            return False

    def _onDelTrackPressed(self):
        activeTrackBox = self._drawer.activeTrackBox
        if activeTrackBox.count() == 0:            
            return 
        
        track2remove = self._getActiveTrack()
        idx2remove = activeTrackBox.currentIndex()

        affectedT = []
        success = True
        for t in list(self.mainOperator.labels.keys()):
            for oid in list(self.mainOperator.labels[t].keys()):
                if track2remove in self.mainOperator.labels[t][oid]:
                    if self._delLabel(t,oid,track2remove):                    
                        affectedT.append(t)
                    else:
                        success = False
        
        if success:
            activeTrackBox.removeItem(idx2remove)
          
        if len(affectedT) > 0:
            self._setDirty(self.mainOperator.TrackImage, affectedT)
            self._setDirty(self.mainOperator.UntrackedImage, affectedT)
            self._setDirty(self.mainOperator.Labels, affectedT)

        self._onSaveAnnotations()
        self._onSaveAppearances()
        self._onSaveDisappearances()

    def _addObjectToTrack(self, activeTrack, oid, t):

        maxTime = self.topLevelOperatorView.LabelImage.meta.shape[0]
        if t not in self.mainOperator.labels.keys():
            self.mainOperator.labels[t] = {}
        if oid not in list(self.mainOperator.labels[t].keys()):
            self.mainOperator.labels[t][oid] = set()
        if activeTrack == self.misdetIdx:
            if len(self.mainOperator.labels[t][oid]) > 0:
                if self.misdetIdx not in self.mainOperator.labels[t][oid]:
                    self._informationMessage("Info: This object is already marked as part of a track, cannot mark it as a misdetection.")
                self._onMarkMisdetectionPressed()
                return -1
        else:
            for tracklist in list(self.mainOperator.labels[t].values()):
                if activeTrack in tracklist:
                    if activeTrack not in self.mainOperator.labels[t][oid]:
                        self._informationMessage("Info: There is already an object with this track id in this time step.")
                        return -1
                    elif t == maxTime:
                        self._informationMessage("Info: You have reached the last time frame.")
                        return -1
                    else:
                        return -2
        
        if self.misdetIdx in self.mainOperator.labels[t][oid]:
            self._criticalMessage("Error: This object is already marked as a misdetection. Cannot mark it as part of a track.")
            if self.misdetLock:
                self._onMarkMisdetectionPressed()
            return -1
        
        self.mainOperator.labels[t][oid].add(activeTrack)  
        self._setDirty(self.mainOperator.Labels, [t])
        self._log('(t,object_id,track_id) = ' + str((t,oid, activeTrack)) + ' added.')

        if self.misdetLock:
            self._onMarkMisdetectionPressed()

    def _runSubtracking(self, position5d, oid, track):

        def _subtracking():
            window = [self._drawer.windowXBox.value(), self._drawer.windowYBox.value(), self._drawer.windowZBox.value()]
            
            t_start = position5d[0]
            activeTrack = self._getActiveTrack()
            if activeTrack == 0:
                self._criticalMessage("Error: There is no active track.")
                return 
            
            res = self._addObjectToTrack(self._getActiveTrack(), oid, t_start)
            if res == -99 or res == -98:
                self._informationMessage("Info: Object " + str(oid) + " in time frame " + str(t_start) + " is outside the current crop. " + \
                                         "Stopping automatic tracking at crop boundary.")
                return
            elif res == -1:
                return
                    
            sroi = [slice(0,1),]
            for idx,p in enumerate(position5d[1:-1]):
                begin = max(0,p-window[idx]//2)
                end = min(begin+window[idx], self.mainOperator.LabelImage.meta.shape[idx+1])
                sroi += [ slice(begin,end), ]
            
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
                
                li_prev_oid = (li_prev == oid_prev)
                li_product = li_prev_oid * li_cur
                uniqueLabels = list(numpy.sort(vigra.analysis.unique(li_product)))
                if 0 in uniqueLabels:
                    uniqueLabels.remove(0)
                if len(uniqueLabels) != 1:
                    self._log('tracking candidates at t = ' + str(t) + ': ' + str(uniqueLabels))
                    self._gotoObject(oid_prev, t-1, keepXYZ=True)
                    t_end = t-1
                    break            
                if numpy.count_nonzero(li_product) < 0.2 * numpy.count_nonzero(li_prev_oid):
                    self._log('too little overlap at t = ' + str(t))
                    self._gotoObject(oid_prev, t-1, keepXYZ=True)
                    t_end = t-1
                    break

                res = self._addObjectToTrack(activeTrack, uniqueLabels[0], t)
                if res == -1:
                    self._gotoObject(uniqueLabels[0], t, keepXYZ=True)
                    return
                
                oid_prev = uniqueLabels[0]
                li_prev = li_cur        
            
            if t_end == self.mainOperator.LabelImage.meta.shape[0] - 1:
                self._log('tracking reached last time step.')
                
            self._setDirty(self.mainOperator.TrackImage, list(range(t_start, max(t_start+1,t_end-1))))
            self._setDirty(self.mainOperator.UntrackedImage, list(range(t_start, max(t_start+1,t_end-1))))
            self._setDirty(self.mainOperator.Labels, list(range(t_start, max(t_start+1,t_end-1))))

            if t_end > 0:
                self._setPosModel(time=t_end)
        
        def _handle_finished(*args):
            self._enableButtons(enable=True)
            self.applet.busy = False
            self.applet.appletStateUpdateRequested()

        def _handle_failure( exc, exc_info ):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested()
            msg = "Exception raised during tracking.  See traceback above.\n"
            log_exception( logger, msg, exc_info )
        
        for i in range(self._drawer.activeTrackBox.count()):
            if int(self._drawer.activeTrackBox.itemText(i)) == track:
                self._drawer.activeTrackBox.setCurrentIndex(i)

        self.applet.busy = True
        self.applet.appletStateUpdateRequested()
        self._enableButtons(enable=False)
        req = Request( _subtracking )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.wait()

    @threadRouted
    def _setPosModel(self, time=None, slicingPos=None, cursorPos=None):        
        if slicingPos:
            self.editor.posModel.slicingPos = slicingPos
        if cursorPos:
            self.editor.posModel.cursorPos = cursorPos
        if time is not None:
            self.editor.posModel.time = time
            
    def _onDivEventPressed(self):
        if self._getActiveTrack() == self.misdetIdx:
            self._criticalMessage("Error: Cannot add a division event for misdetections. Release misdetection button first.")
            return

        if self.divLock:
            self._drawer.divEvent.setText("Division Event")
            for imageView in self.editor.imageViews:
                imageView._croppingMarkers.setVisible(False)
        else:
            self._drawer.divEvent.setText("Stop Division Event")

        self.divLock = not self.divLock             
        self._drawer.divEvent.setChecked(not self.divLock)
        self.divs = []
        
        self._enableButtons(exceptButtons=[self._drawer.divEvent], enable=(not self.divLock))                      

        self._onSaveAnnotations()
        self._onSaveAppearances()
        self._onSaveDisappearances()

    def _setStyleSheet(self, widget, qcolor, qType="QComboBox"):
        values = "{r}, {g}, {b}, {a}".format(r = qcolor.red(),
                                     g = qcolor.green(),
                                     b = qcolor.blue(),
                                     a = qcolor.alpha()
                                     )
        widget.setStyleSheet(qType+" { background-color: rgba("+values+"); }")
    

    def _onDivisionsListActivated(self):        
        parent = int(str(self._drawer.divisionsList.currentItem().text()).split(':')[0])
        t = self.mainOperator.divisions[parent][1]        
                
        found = False
        for oid in list(self.mainOperator.labels[t].keys()):
            if parent in self.mainOperator.labels[t][oid]:
                found = True
                break
        
        if not found:
            self._criticalMessage("Error: Cannot find the division label.")
            return
        
        self._gotoObject(oid, t)
    

    def _onMarkMisdetectionPressed(self):
        self.misdetLock = not self.misdetLock             
        self._drawer.markMisdetection.setChecked(not self.misdetLock)
                
        activeTrackBox = self._drawer.activeTrackBox
        
        if self.misdetLock:            
            self.lastActiveTrackIdx = activeTrackBox.currentIndex()
            self._drawer.markMisdetection.setText("Mark as False Detection (Turn Off)")
            self._enableButtons(exceptButtons=[self._drawer.markMisdetection], enable=False)
                    
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
            if self.lastActiveTrackIdx is not None and self.lastActiveTrackIdx >= 0:
                activeTrackBox.setCurrentIndex(self.lastActiveTrackIdx)
                self._currentActiveTrackChanged()
            
            self._drawer.markMisdetection.setText("Mark as False Detection")
            self._enableButtons(exceptButtons=[self._drawer.markMisdetection], enable=True)
        
        self._onSaveAnnotations()
        self._onSaveAppearances()
        self._onSaveDisappearances()

    @staticmethod
    def _appendUnique(lst, obj):
        if obj not in lst:
            lst.append(obj)
            
            
    def _getEvents(self):
        maxt = self.topLevelOperatorView.LabelImage.meta.shape[0]
        time_range = [0, maxt]
        oid2tids, alltids = self.mainOperator._getObjects(time_range, self.misdetIdx)
        if self.misdetIdx in alltids:
            alltids.remove(self.misdetIdx)
        divisions = self.mainOperator.divisions
                
        moves = {}
        divs = {}
        mergers = {}
        apps = {}
        disapps = {}
        multiMoves = {}
        for t in list(oid2tids.keys()):
            moves[t] = []
            divs[t] = []
            mergers[t] = []
            apps[t] = []
            disapps[t] = []
            multiMoves[t] = []
        
        t_start = time_range[0]
        
        tracks_starting_in_div = {}
        for d in list(divisions.keys()):
            [tid_child1, tid_child2], t_div = divisions[d]
            tracks_starting_in_div[tid_child1] = t_div + 1
            tracks_starting_in_div[tid_child2] = t_div + 1
            
                            
        for tid in sorted(list(alltids)):
            oid_prev = None            
            
            for t in sorted(oid2tids.keys()):  
                oid_cur = None                
                for o in list(oid2tids[t].keys()):
                    if tid in oid2tids[t][o]:
                        oid_cur = o
                        break
                       
                if (oid_prev is not None) and (oid_cur is None): # track ends
                    if tid in list(divisions.keys()): # division
                        [tid_child1, tid_child2], t_div = divisions[tid]
                        
                        if t == t_div+1:                    
                            oid_child1 = None
                            oid_child2 = None
                            for o in list(oid2tids[t].keys()):
                                if tid_child1 in oid2tids[t][o]:
                                    oid_child1 = o
                                    if oid_child2:
                                        break
                                if tid_child2 in oid2tids[t][o]:
                                    oid_child2 = o
                                    if oid_child1:
                                        break
                                          
                            if (oid_child1 is not None) and (oid_child2 is not None):
                                # check if both children can be found in the current frame                            
                                child1_exists = (oid_child1 in list(oid2tids[t].keys()))
                                child2_exists = (oid_child2 in list(oid2tids[t].keys()))
                                if child1_exists and child2_exists:
                                    self._appendUnique(divs[t], (oid_prev,oid_child1,oid_child2,0.))
                                elif child1_exists:
                                    self._appendUnique(moves[t], (oid_prev,oid_child1,0.))
                                elif child2_exists:
                                    self._appendUnique(moves[t], (oid_prev,oid_child2,0.))                                
                                break
                                    
                    # else: disappearance
                    self._appendUnique(disapps[t], (oid_prev, 0.))        
                    # do not break, maybe the track starts somewhere else again (due to the size/fov filter)
                
                elif (oid_prev is None) and (t != t_start) and (oid_cur is not None): # track starts
                    if tid in list(tracks_starting_in_div.keys()) and tracks_starting_in_div[tid] != t:
                        self._appendUnique(apps[t], (oid_cur, 0.))
                
                elif (oid_prev is not None) and (oid_cur is not None): # move
                    self._appendUnique(moves[t], (oid_prev, oid_cur, 0.))
                    
                    if len(oid2tids[t][oid_cur]) == 1 and len(oid2tids[t-1][oid_prev]) > 1:
                        t_multiprev = None
                        oid_multiprev = None
                        
                        found = False            
                        for tt in reversed(list(range(t))):
                            for o in list(oid2tids[tt].keys()):
                                if (tid in oid2tids[tt][o]) and (len(oid2tids[tt][o]) == 1):
                                    found = True
                                    oid_multiprev = o
                                    t_multiprev = tt                                    
                                    break
                            if found:
                                break
                            
                        if t_multiprev is not None and oid_multiprev is not None:
                            self._appendUnique(multiMoves[t],(oid_multiprev, oid_cur, t_multiprev, 0.)) 
                
                oid_prev = oid_cur
        
        merger_sizes = {}
        for t in list(oid2tids.keys()):
            for oid in list(oid2tids[t].keys()):
                if len(oid2tids[t][oid]) > 1:
                    mergers[t].append((oid, len(oid2tids[t][oid]), 0.))                    
                    m_size = len(oid2tids[t][oid])
                    if m_size not in list(merger_sizes.keys()):
                        merger_sizes[m_size] = 0
                    merger_sizes[m_size] += 1
        
        logging.info( 'Merger-Sizes: {}'.format(merger_sizes) )
        
        return oid2tids, disapps, apps, divs, moves, mergers, multiMoves
        
    def _onExportDivisionsButtonPressed(self):
        options = QtWidgets.QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QtWidgets.QFileDialog.DontUseNativeDialog

        out_fn, _filter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Mergers',os.path.expanduser("~") + "/divisions.csv", options=options)
        
        if out_fn is None or str(out_fn) == '':            
            return
        if out_fn.split(".")[-1] != "csv":
            out_fn += ".csv"
        
        self.applet.busy = True
        self.applet.appletStateUpdateRequested()
        try:
            import csv
            with open(out_fn, 'w') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['timestep_parent','track_id_parent','track_id_child1','track_id_child2'])
                for tid in list(self.mainOperator.divisions.keys()):
                    children, t_parent = self.mainOperator.divisions[tid]
                    writer.writerow([t_parent, tid, children[0], children[1]])
                
        finally:
            self.applet.busy = False
            self.applet.appletStateUpdateRequested()
    
    def _onExportMergersButtonPressed(self):        
        options = QtWidgets.QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QtWidgets.QFileDialog.DontUseNativeDialog

        out_fn, _filter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Mergers',os.path.expanduser("~") + "/mergers.csv", options=options)
        
        if out_fn is None or str(out_fn) == '':            
            return
        if out_fn.split(".")[-1] != "csv":
            out_fn += ".csv"
        
        self.applet.busy = True
        self.applet.appletStateUpdateRequested()
        try:
            import csv
            with open(out_fn, 'w') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['timestep','object_id','track_ids'])
                for t in list(self.mainOperator.labels.keys()):
                    for oid in list(self.mainOperator.labels[t].keys()):
                        if len(self.mainOperator.labels[t][oid]) > 1:
                            writer.writerow([t,oid,";".join(list(str(x) for x in self.mainOperator.labels[t][oid]))])
                
        finally:
            self.applet.busy = False
            self.applet.appletStateUpdateRequested()

    def _onExportButtonPressed(self):
        import h5py        
        options = QtWidgets.QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QtWidgets.QFileDialog.DontUseNativeDialog

        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory',os.path.expanduser("~"), options=options)
        
        if directory is None or str(directory) == '':            
            return
        directory = str(directory)
        
        def _handle_progress(x):       
            self.applet.progressSignal(x)
            
        def _export():
            self.applet.busy = True
            self.applet.appletStateUpdateRequested()
            oid2tids, disapps, apps, divs, moves, mergers, multiMoves = self._getEvents()
            
            num_files = float(len(list(oid2tids.keys())))
            
            for t in sorted(oid2tids.keys()):
                fn =  directory + "/" + str(t).zfill(5)  + ".h5"
                self._log('Writing file ' + str(fn))
                
                roi = SubRegion(self.mainOperator.LabelImage, start=[t,0,0,0,0], stop=[t+1,] + list(self.mainOperator.LabelImage.meta.shape[1:]))        
                labelImage = self.mainOperator.LabelImage.get(roi).wait()
                labelImage = labelImage[0,...,0]
                 
                dis_at = numpy.asarray(disapps[t])
                app_at = numpy.asarray(apps[t])
                div_at = numpy.asarray(divs[t])
                mov_at = numpy.asarray(moves[t])
                merger_at = numpy.asarray(mergers[t])
                multiMoves_at = numpy.asarray(multiMoves[t])
                        
    
                try:
                    with h5py.File(fn, 'w-') as f_curr:
                        # delete old label image
                        if "segmentation" in list(f_curr.keys()):
                            del f_curr["segmentation"]
                        
                        seg = f_curr.create_group("segmentation")            
                        # write label image
                        seg.create_dataset("labels", data = labelImage, dtype=numpy.uint32, compression=1)
                        
                        oids_meta = numpy.sort(vigra.analysis.unique(labelImage)).astype(numpy.uint32)[1:]  
                        ones = numpy.ones(oids_meta.shape, dtype=numpy.uint8)
                        if 'objects' in list(f_curr.keys()): del f_curr['objects']
                        f_meta = f_curr.create_group('objects').create_group('meta')
                        f_meta.create_dataset('id', data=oids_meta, compression=1)
                        f_meta.create_dataset('valid', data=ones, compression=1)
        
                        # delete old tracking
                        if "tracking" in list(f_curr.keys()):
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
                    
                except IOError:                    
                    self._criticalMessage("File " + str(fn) + " exists already. Please choose a different folder or delete the file(s).")
                    return
                _handle_progress(t/num_files * 100)
            self._log("-> tracking successfully exported")
        
        def _handle_finished(*args):            
            self.applet.progressSignal(100)
            self.applet.busy = False
            self.applet.appletStateUpdateRequested()

        def _handle_failure( exc, exc_info ):
            msg = "Exception raised during export.  See traceback above.\n"
            log_exception( logger, msg, exc_info )
            self.applet.busy = False
            self.applet.appletStateUpdateRequested()
            self.applet.progressSignal(100)

        self.applet.progressSignal(0)
        req = Request( _export )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()

    def _onExportTifButtonPressed(self):
        import vigra        
        
        options = QtWidgets.QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QtWidgets.QFileDialog.DontUseNativeDialog

        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory',os.path.expanduser("~"), options=options)
        if directory is None or len(str(directory)) == 0:
            return
        
        def _handle_progress(x):       
            self.applet.progressSignal(x)
            
        def _export():
            self.applet.busy = True
            self.applet.appletStateUpdateRequested()
            divisions = self.mainOperator.divisions
            inverseDivisions = {}
            for k, vals in list(divisions.items()):
                for v in vals[0]:
                    inverseDivisions[v] = k
            replace = {}
            activeTrackBox = self._drawer.activeTrackBox
            tids = set()
            for idx in range(activeTrackBox.count()):
                tids.add(int(activeTrackBox.itemText(idx)))
            if len(tids) == 0 or max(tids) == -1 or max(tids) == 0:
                self._criticalMessage("There are no tracks to export.")
                return
            
            if 0 in tids:
                tids.remove(0)
            if -1 in tids:
                tids.remove(-1)
            for tid in tids:
                replace[tid] = [tid] # identity
                
            for tid in list(inverseDivisions.keys()):
                rootTid = inverseDivisions[tid]
                while rootTid in list(inverseDivisions.keys()):
                    rootTid = inverseDivisions[rootTid]
                replace[tid] = [rootTid]
                    
            shape = list(self.mainOperator.TrackImage.meta.shape)
            num_files = float(shape[0]-1)
            for t in range(shape[0]):
                self._log('exporting tiffs for t = ' + str(t))            
                
                roi = SubRegion(self.mainOperator.TrackImage, start=[t,] + 4*[0,], stop=[t+1,] + list(shape[1:]))
                trackImage = self.mainOperator.TrackImage.get(roi).wait()
                relabeled = self.mainOperator._relabel(trackImage[0,...,0], replace)
                for i in range(relabeled.shape[2]):
                    out_im = relabeled[:,:,i]
                    out_fn = str(directory) + '/vis_t' + str(t).zfill(4) + '_z' + str(i).zfill(4) + '.tif'
                    vigra.impex.writeImage(numpy.asarray(out_im,dtype=numpy.uint32), out_fn)
            
                _handle_progress(t/num_files * 100)
            self._log("-> tracking successfully exported")

        def _handle_finished(*args):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested()
            self.applet.progressSignal(100)

        def _handle_failure( exc, exc_info ):
            msg = "Exception raised during export.  See traceback above.\n"
            log_exception( logger, msg, exc_info )
            self.applet.busy = False
            self.applet.appletStateUpdateRequested()
            self.applet.progressSignal(100)

        self.applet.progressSignal(0)
        req = Request( _export )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()
        
        
    
    def _gotoObject(self, oid, t, keepZ=False, keepXYZ=False):
        roi = SubRegion(self.mainOperator.LabelImage, start=[t,0,0,0,0], stop=[t+1,] + list(self.mainOperator.LabelImage.meta.shape[1:]))
        li = self.mainOperator.LabelImage.get(roi).wait()
        coords = numpy.where(li == oid)
        mid = len(coords[1]) // 2
        cur_slicing_pos = self.editor.posModel.slicingPos
        new_slicing_pos = [coords[1][mid], coords[2][mid], coords[3][mid]]
         
        if keepZ:
            new_slicing_pos[2] = cur_slicing_pos[2]
        if keepXYZ:
            for i in range(3):
                new_slicing_pos[i] = cur_slicing_pos[i]
        self.editor.navCtrl.panSlicingViews(new_slicing_pos, [0,1,2])
        self._setPosModel(time=t, slicingPos=new_slicing_pos, cursorPos=new_slicing_pos)      


    def _onGotoLabel(self):
        t = self._drawer.timeBox.value()
        tid = self._drawer.tidBox.value()
        
        if t < 0 or t >= self.mainOperator.LabelImage.meta.shape[0]:
            self._criticalMessage("Error: Cannot access time step "  + str(t) + ".")
            return
        
        found = False
        for oid in list(self.mainOperator.labels[t].keys()):
            if tid in self.mainOperator.labels[t][oid]:
                found = True
                break
        
        if not found:
            self._criticalMessage("Error: Cannot find track id " + str(tid) + " at time " + str(t) + ".")
            return
          
        self._gotoObject(oid, t)


    @threadRouted
    def _log(self, prompt):
        self._drawer.logOutput.append(prompt)
        self._drawer.logOutput.moveCursor(QTextCursor.End)
        logger.info( prompt )

    #
    # These functions used to be pass-throughs to a signal,
    # but I don't see why that's necessary.
    # (They are always called from the main thread.)
    # So now we just call each target function directly.
    #
    def _criticalMessage(self, prompt):
        self.postCriticalMessage(prompt)

    def _questionMessage(self, prompt):
        self.postQuestionMessage(prompt)

    def _informationMessage(self, prompt):
        self.postInformationMessage(prompt)

    @threadRouted
    def postCriticalMessage(self, prompt):
        QtWidgets.QMessageBox.critical(self, "Error", prompt, QtWidgets.QMessageBox.Ok)
        
    @threadRouted
    def postQuestionMessage(self, prompt):
        qBox = QtWidgets.QMessageBox()
        qBox.setWindowTitle("Confirm")
        qBox.setText(prompt)
        qBox.setStandardButtons( QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        qBox.setDefaultButton( QtWidgets.QMessageBox.Cancel )
        retVal = qBox.exec_()
        if retVal == QtWidgets.QMessageBox.Ok:
            self.deleteAllTraining = True

    @threadRouted
    def postInformationMessage(self, prompt):
        QtWidgets.QMessageBox.information(self, "Info", prompt, QtWidgets.QMessageBox.Ok)

    @threadRouted
    def _enableButtons(self, exceptButtons=None, enable=True):
        buttons = [self._drawer.activeTrackBox, 
                   self._drawer.delTrack,
                   self._drawer.newTrack,
                   self._drawer.markMisdetection,
                   self._drawer.divEvent,
                   self._drawer.nextUnlabeledDivision,
                   self._drawer.nextUnlabeledMerger,
                   self._drawer.nextUnlabeledObject,
                   self._drawer.nextUnlabeledObjectFrame,
                   self._drawer.exportButton
                   ]
                
        for b in buttons:
            if exceptButtons is None or b not in exceptButtons:
                b.setEnabled(enable)
