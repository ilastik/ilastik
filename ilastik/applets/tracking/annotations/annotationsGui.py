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
from PyQt4 import uic, QtGui, QtCore
from PyQt4.QtGui import QColor, QPixmap, QIcon

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
from ilastik.widgets.cropListView import Crop
from ilastik.widgets.cropListModel import CropListModel
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
from ilastik.utility import bind

import volumina.colortables as colortables
from volumina.api import LazyflowSource, GrayscaleLayer, ColortableLayer
from volumina.utility import ShortcutManager

from ilastik.config import cfg as ilastik_config

from volumina.utility import encode_from_qstring
    

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
        self.editor.cropModel.mouseRelease.connect(bind(self._onSaveAnnotations))
        self._drawer.activeTrackBox.setToolTip("Active track label and colour.")

        self.editor.showCropLines(True)
        self.editor.cropModel.setEditable (False)

        self.editor.posModel.timeChanged.connect(self.updateTime)

        self._cropListViewInit()

        self.topLevelOperatorView.Labels.setValue(self.topLevelOperatorView.labels)
        self.topLevelOperatorView.Divisions.setValue(self.topLevelOperatorView.divisions)

        crop = self.getCurrentCrop()
        self.updateLabeledUnlabeledCount(crop)

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
        self._drawer.cropListView.setVisible(False)
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

        self._drawer.unlabeledObjectsCount.setToolTip(
            "Number of unlabeled objects in the current crop.")
        self._drawer.allObjectsCount.setToolTip(
            "Number of all objects in the current crop.")
        self._drawer.unlabeledObjectsCountFrame.setToolTip(
            "Number of unlabeled objects in the current time frame of the current crop.")
        self._drawer.allObjectsCountFrame.setToolTip(
            "Number of all objects in the current time frame of the current crop.")

        self._drawer.unlabeledDivisionsCount.setToolTip(
            "Number of unlabeled divisions in the current crop.")
        self._drawer.allDivisionsCount.setToolTip(
            "Number of all suggested divisions in the current crop for a cut-off probability "+ \
            str(self.divisionProbabilityCutOff)+".")

        self._drawer.unlabeledMergersCount.setToolTip(
            "Number of unlabeled mergers in the current crop.")
        self._drawer.allMergersCount.setToolTip(
            "Number of all suggested mergers in the current crop for a cut-off probability "+ \
            str(self.mergerProbabilityCutOff)+".")

        self.topLevelOperatorView.MaxNumObj.notifyDirty(bind(self.updateMergerButtons))
        self.updateMergerButtons()

    def updateMergerButtons(self):
        flag = self.topLevelOperatorView.MaxNumObj.value > 1
        self._drawer.nextUnlabeledMerger.setVisible(flag)
        self._drawer.unlabeledMergersCount.setVisible(flag)
        self._drawer.allMergersCount.setVisible(flag)
        self._drawer.mergersSlash.setVisible(flag)

    def getNumberOfUnlabeledDivisions(self):
        self.divFeatures = self.topLevelOperatorView.DivisionProbabilities(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        labels = self.topLevelOperatorView.labels
        divisions = self.topLevelOperatorView.divisions
        crop = self.getCurrentCrop()

        time_start = crop["time"][0]
        time_stop = crop["time"][1]

        divisionCandidates = []
        for t in range(time_start, time_stop):
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                                stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                divFlag = False
                if ul in labels[t].keys():
                    trackIDs = list(labels[t][ul])
                    for trackID in trackIDs:
                        if trackID in divisions.keys():
                            divFlag = True
                if not divFlag and ul > 0 and self.divFeatures[t][ul][1]>self.divisionProbabilityCutOff:
                    divisionCandidates.append([t,ul,self.divFeatures[t][ul][1]])

        return len(divisionCandidates)

    def getNumberOfDivisions(self):
        self.divFeatures = self.topLevelOperatorView.DivisionProbabilities(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        crop = self.getCurrentCrop()

        time_start = crop["time"][0]
        time_stop = crop["time"][1]

        divisionCandidates = []
        for t in range(time_start, time_stop):
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                                stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                if ul > 0 and self.divFeatures[t][ul][1]>self.divisionProbabilityCutOff:
                    divisionCandidates.append([t,ul,self.divFeatures[t][ul][1]])

        return len(divisionCandidates)

    def goToNextUnlabeledDivision(self):
        self.divFeatures = self.topLevelOperatorView.DivisionProbabilities(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        labels = self.topLevelOperatorView.labels
        divisions = self.topLevelOperatorView.divisions
        crop = self.getCurrentCrop()

        time_start = crop["time"][0]
        time_stop = crop["time"][1]

        divisionCandidates = []
        for t in range(time_start, time_stop):
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                                stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                divFlag = False
                if ul in labels[t].keys():
                    trackIDs = list(labels[t][ul])
                    for trackID in trackIDs:
                        if trackID in divisions.keys():
                            divFlag = True
                if not divFlag and ul > 0 and self.divFeatures[t][ul][1]>self.divisionProbabilityCutOff:
                    divisionCandidates.append([t,ul,self.divFeatures[t][ul][1]])

        if divisionCandidates == []:
            self._informationMessage("No more DIVISIONS found for the division probability cut-off {}!".format(self.divisionProbabilityCutOff))
        else:
            sorted(divisionCandidates,key=lambda x:x[2])
            minIndex = 0
            t = divisionCandidates[minIndex][0]
            ul = divisionCandidates[minIndex][1]
            self._gotoObject(ul,t, keepXYZ=False)

            if ul in labels[t].keys() and len(labels[t][ul]) > 0:
                for track in labels[t][ul]:
                    for i in range(self._drawer.activeTrackBox.count()):
                        if int(self._drawer.activeTrackBox.itemText(i)) == track:
                            self._drawer.activeTrackBox.setCurrentIndex(i)
                            break
            return ul, t

        return None, None

    def getNumberOfMergers(self):
        self.mergerFeatures = self.topLevelOperatorView.DetectionProbabilities(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        crop = self.getCurrentCrop()

        time_start = crop["time"][0]
        time_stop = crop["time"][1]

        mergerCandidates = []
        for t in range(time_start, time_stop+1):
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                                stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                if ul > 0:
                    mergerIndex = 0
                    maxValue = max(self.mergerFeatures[t][ul])
                    index = list(self.mergerFeatures[t][ul]).index(maxValue)
                    if maxValue > self.mergerProbabilityCutOff:
                        mergerIndex = index
                    if mergerIndex >1:
                        mergerCandidates.append([t,ul,maxValue])
        return len(mergerCandidates)

    def getNumberOfUnlabeledMergers(self):
        self.mergerFeatures = self.topLevelOperatorView.DetectionProbabilities(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        labels = self.topLevelOperatorView.labels
        crop = self.getCurrentCrop()

        time_start = crop["time"][0]
        time_stop = crop["time"][1]

        mergerCandidates = []
        for t in range(time_start, time_stop+1):
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                                stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                if ul > 0:
                    mergerIndex = 0
                    maxValue = max(self.mergerFeatures[t][ul])
                    index = list(self.mergerFeatures[t][ul]).index(maxValue)
                    if maxValue > self.mergerProbabilityCutOff:
                        mergerIndex = index
                    if mergerIndex >1:
                        if (not ul in labels[t].keys()) or( ul in labels[t].keys() and mergerIndex > len(labels[t][ul])):
                            mergerCandidates.append([t,ul,maxValue])
        return len(mergerCandidates)

    def goToNextUnlabeledMerger(self):
        self.mergerFeatures = self.topLevelOperatorView.DetectionProbabilities(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        labels = self.mainOperator.labels
        crop = self.getCurrentCrop()

        time_start = crop["time"][0]
        time_stop = crop["time"][1]

        mergerCandidates = []
        for t in range(time_start, time_stop+1):
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                                stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
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
                        if (not ul in labels[t].keys()) or( ul in labels[t].keys() and mergerIndex > len(labels[t][ul])):
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
        crop = self.getCurrentCrop()

        time_start = crop["time"][0]
        time_stop = crop["time"][1]

        for t in range(time_start, time_stop):
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                                stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

            for ul in uniqueLabels:
                if ul > 0 and not ul in labels[t].keys():
                    self._gotoObject(ul, t, keepXYZ=False)
                    return ul, t

        return None, None

    def goToNextUnlabeledObjectFrame(self):
        labels = self.mainOperator.labels
        crop = self.getCurrentCrop()
        t = self.editor.posModel.time

        roi = SubRegion(self.topLevelOperatorView.LabelImage,
                            start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                            stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
        li = self.topLevelOperatorView.LabelImage.get(roi).wait()
        uniqueLabels = list(numpy.sort(vigra.analysis.unique(li)))

        for ul in uniqueLabels:
            if ul > 0 and not ul in labels[t].keys():
                self._gotoObject(ul, t, keepXYZ=False)
                return ul, t

        return None, None

    def getNumberOfAllObjects(self, crop):
        num = 0
        for t in range(crop["time"][0],crop["time"][1]+1):
            roi = SubRegion(self.topLevelOperatorView.LabelImage,
                                start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                                stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
            li = self.topLevelOperatorView.LabelImage.get(roi).wait()
            uniqueLabels = numpy.unique(li)
            if uniqueLabels[0] == 0:
                num += len (uniqueLabels) - 1
            else:
                num += len (uniqueLabels)

        return num

    def getNumberOfAllObjectsFrame(self, crop, t):
        num = 0
        roi = SubRegion(self.topLevelOperatorView.LabelImage,
                            start=[t,crop["starts"][0],crop["starts"][1],crop["starts"][2],0],
                            stop=[t+1,crop["stops"][0],crop["stops"][1],crop["stops"][2],1])
        li = self.topLevelOperatorView.LabelImage.get(roi).wait()
        uniqueLabels = numpy.unique(li)
        if uniqueLabels[0] == 0:
            num += len (uniqueLabels) - 1
        else:
            num += len (uniqueLabels)

        return num

    def getNumberOfLabeledObjects(self, crop):
        num = 0
        self.features = self.topLevelOperatorView.ObjectFeatures(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()

        for time in range(crop["time"][0],crop["time"][1]+1):
            if time in self.topLevelOperatorView.labels.keys():
                for label in self.topLevelOperatorView.labels[time].keys():
                    lower = self.features[time][default_features_key]['Coord<Minimum>'][label]
                    upper = self.features[time][default_features_key]['Coord<Maximum>'][label]

                    addAnnotation = False
                    if len(self.topLevelOperatorView.labels[time][label]) > 0:
                        if len(lower) == 2:
                            if  crop["starts"][0] <= upper[0] and lower[0] <= crop["stops"][0] and \
                                crop["starts"][1] <= upper[1] and lower[1] <= crop["stops"][1]:
                                addAnnotation = True
                        else:
                            if  crop["starts"][0] <= upper[0] and lower[0] <= crop["stops"][0] and \
                                crop["starts"][1] <= upper[1] and lower[1] <= crop["stops"][1] and \
                                crop["starts"][2] <= upper[2] and lower[2] <= crop["stops"][2]:
                                addAnnotation = True

                    if addAnnotation:
                        num += 1
        return num

    def getNumberOfLabeledObjectsFrame(self, crop, time):
        num = 0
        self.features = self.topLevelOperatorView.ObjectFeatures([time]).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()

        if time in self.topLevelOperatorView.labels.keys():
            for label in self.topLevelOperatorView.labels[time].keys():
                lower = self.features[time][default_features_key]['Coord<Minimum>'][label]
                upper = self.features[time][default_features_key]['Coord<Maximum>'][label]

                addAnnotation = False
                if len(self.topLevelOperatorView.labels[time][label]) > 0:
                    if len(lower) == 2:
                        if  crop["starts"][0] <= upper[0] and lower[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upper[1] and lower[1] <= crop["stops"][1]:
                            addAnnotation = True
                    else:
                        if  crop["starts"][0] <= upper[0] and lower[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upper[1] and lower[1] <= crop["stops"][1] and \
                            crop["starts"][2] <= upper[2] and lower[2] <= crop["stops"][2]:
                            addAnnotation = True

                if addAnnotation:
                    num += 1
        return num

    def updateTime(self):
        delta = self.topLevelOperatorView.Crops[self._drawer.cropListModel[self._drawer.cropListModel.selectedRow()].name][0][0] - self.editor.posModel.time
        if delta > 0:
            self.editor.navCtrl.changeTimeRelative(delta)
        else:
            delta = self.topLevelOperatorView.Crops[self._drawer.cropListModel[self._drawer.cropListModel.selectedRow()].name][0][1] - self.editor.posModel.time
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
        self._previousCrop = -1
        self._currentCrop = -1
        self._currentCropName = ""
        self.divisionProbabilityCutOff = 0.5
        self.mergerProbabilityCutOff = 1/self.topLevelOperatorView.MaxNumObj.value

        super(AnnotationsGui, self).__init__(parentApplet, topLevelOperatorView)
        
        self.editor.cropModel.setEditable(False)
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
        
        self.connect( self, QtCore.SIGNAL('postCriticalMessage(QString)'), self.postCriticalMessage)
        self.connect( self, QtCore.SIGNAL('postInformationMessage(QString)'), self.postInformationMessage)
        self.connect( self, QtCore.SIGNAL('postQuestionMessage(QString)'), self.postQuestionMessage)

        self._initShortcuts()
        self.editor.posModel.timeChanged.connect(self.updateTime)
        try:
            self.editor.navCtrl.changeTimeRelative(self.topLevelOperatorView.Crops.value[self._drawer.cropListModel[0].name]["time"][0] - self.editor.posModel.time)
        except:
            pass

        self.features = self.topLevelOperatorView.ObjectFeatures(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        self._initAnnotations()

        self.__cleanup_fns = []
        self.topLevelOperatorView.Labels.notifyDirty( bind(self._updateLabels) )
        self.topLevelOperatorView.Crops.notifyDirty( bind(self._cropListViewInit) )
        self.__cleanup_fns.append( partial( self.topLevelOperatorView.Labels.unregisterDirty, bind(self._updateLabels) ) )
        self.__cleanup_fns.append( partial( self.topLevelOperatorView.Crops.unregisterDirty, bind(self._cropListViewInit) ) )
        self._drawer.cropBoxView.currentIndexChanged.connect(self._currentCropBoxChanged)

        self.volumeEditorWidget.quadViewStatusBar.setToolTipTimeButtonsCrop(True)
        self.volumeEditorWidget.quadViewStatusBar.setToolTipTimeSliderCrop(True)
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

        self._cropListViewInit()
        roi = {}
        roi["start"]=(0,0,0,0,0)
        roi["stop"]=self.mainOperator.TrackImage.meta.shape

        self.divLock = False
        self.misdetLock = False
        self.misdetIdx = -1

        self.mainOperator.initOutputs()

        self._reset()

        self._setDirty(self.mainOperator.LabelImage, range(self.mainOperator.TrackImage.meta.shape[0]))
        self._setDirty(self.mainOperator.Labels, range(self.mainOperator.TrackImage.meta.shape[0]))
        self._setDirty(self.mainOperator.Divisions, range(self.mainOperator.TrackImage.meta.shape[0]))
        self._setDirty(self.mainOperator.TrackImage, range(self.mainOperator.TrackImage.meta.shape[0]))
        self._setDirty(self.mainOperator.UntrackedImage, range(self.mainOperator.TrackImage.meta.shape[0]))

        self.setupLayers()
        self._onCropSelected(0)

    def stopAndCleanUp(self):
        super(AnnotationsGui, self).stopAndCleanUp()

        for fn in self.__cleanup_fns:
            fn()

    def _updateLabels(self):
        pass


    def _cropListViewInit(self):
        if self.topLevelOperatorView.Crops.value != {}:
            self._drawer.cropListModel=CropListModel()
            self._drawer.cropBoxView.clear()
            crops = self.topLevelOperatorView.Crops.value
            count = 0
            for key in sorted(crops):
                newRow = self._drawer.cropListModel.rowCount()

                pmapColor = QColor(crops[key]["pmapColor"][0],crops[key]["pmapColor"][1],crops[key]["pmapColor"][2])
                crop = Crop(
                        key,
                        [(crops[key]["time"][0],crops[key]["starts"][0],crops[key]["starts"][1],crops[key]["starts"][2]),(crops[key]["time"][1],crops[key]["stops"][0],crops[key]["stops"][1],crops[key]["stops"][2])],
                        QColor(crops[key]["cropColor"][0],crops[key]["cropColor"][1],crops[key]["cropColor"][2]),
                        pmapColor=pmapColor
                )

                self._drawer.cropListModel.insertRow( newRow, crop )

                pm = QPixmap(16,16)
                pm.fill(QColor(pmapColor))
                self._drawer.cropBoxView.insertItem(newRow, QIcon(pm), str(key))

                if count == 0:
                    self._currentCropName = key

                count =+ 1

            self._drawer.cropListView.setModel(self._drawer.cropListModel)
            self._drawer.cropListView.updateGeometry()
            self._drawer.cropListView.update()
            self._drawer.cropListView.allowDelete = False
            self._drawer.cropListView.selectRow(0)
            self._drawer.cropBoxView.setCurrentIndex(0)
            self._onCropSelected(0)
            self._selectedRow = 0
            self._previousCrop = -1
            self._currentCrop = 0

            rawImageSlot = self.topLevelOperatorView.RawImage
            tagged_shape = rawImageSlot.meta.getTaggedShape()
            self.editor.posModel.shape5D = [tagged_shape['t'],tagged_shape['x'],tagged_shape['y'],tagged_shape['z'],tagged_shape['c']]
            self.editor.navCtrl.changeTimeRelative(self.topLevelOperatorView.Crops.value[self._drawer.cropListModel[0].name]["time"][0] - self.editor.posModel.time)

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
        self.topLevelOperatorView.Labels.setValue(self.topLevelOperatorView.labels)
        self.topLevelOperatorView.Divisions.setValue(self.topLevelOperatorView.divisions)

    def _onSaveAnnotations(self):
        self.features = self.topLevelOperatorView.ObjectFeatures(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()#, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()
        for name in self.topLevelOperatorView.Crops.value.keys():
            crop = self.topLevelOperatorView.Crops.value[name]

            if name not in self.topLevelOperatorView.Annotations.value.keys():
                self.topLevelOperatorView.Annotations.value[name] = {}
            if "divisions" not in self.topLevelOperatorView.Annotations.value[name].keys():
                self.topLevelOperatorView.Annotations.value[name]["divisions"] = {}
            for parentTrack in self.topLevelOperatorView.divisions.keys():
                time = self.topLevelOperatorView.divisions[parentTrack][1]
                child1Track = self.topLevelOperatorView.divisions[parentTrack][0][0]
                child2Track = self.topLevelOperatorView.divisions[parentTrack][0][1]

                parent = self.getLabel(time, parentTrack)
                child1 = self.getLabel(time+1, child1Track)
                child2 = self.getLabel(time+1, child2Track)

                if not (parent and child1 and child2):
                    logger.info("WARNING:Your divisions and labels do not match for time {} and parent track {} with label {}!".format(time,parentTrack,parent))
                    pass
                else:
                    lowerParent = self.features[time][default_features_key]['Coord<Minimum>'][parent]
                    upperParent = self.features[time][default_features_key]['Coord<Maximum>'][parent]

                    lowerChild1 = self.features[time+1][default_features_key]['Coord<Minimum>'][child1]
                    upperChild1 = self.features[time+1][default_features_key]['Coord<Maximum>'][child1]

                    lowerChild2 = self.features[time+1][default_features_key]['Coord<Minimum>'][child2]
                    upperChild2 = self.features[time+1][default_features_key]['Coord<Maximum>'][child2]

                    addAnnotation = False
                    if len(lowerParent) == 2:
                        if (crop["time"][0] <= time <= crop["time"][1]) and \
                            ((crop["starts"][0] <= upperParent[0] and lowerParent[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperParent[1] and lowerParent[1] <= crop["stops"][1]) and \
                            ( crop["starts"][0] <= upperChild1[0] and lowerChild1[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperChild1[1] and lowerChild1[1] <= crop["stops"][1]) and \
                            ( crop["starts"][0] <= upperChild2[0] and lowerChild2[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperChild2[1] and lowerChild2[1] <= crop["stops"][1])):
                            addAnnotation = True
                    else:
                        if (crop["time"][0] <= time <= crop["time"][1]) and \
                            ((crop["starts"][0] <= upperParent[0] and lowerParent[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperParent[1] and lowerParent[1] <= crop["stops"][1] and \
                            crop["starts"][2] <= upperParent[2] and lowerParent[2] <= crop["stops"][2]) and \
                            ( crop["starts"][0] <= upperChild1[0] and lowerChild1[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperChild1[1] and lowerChild1[1] <= crop["stops"][1] and \
                            crop["starts"][2] <= upperChild1[2] and lowerChild1[2] <= crop["stops"][2]) and \
                            ( crop["starts"][0] <= upperChild2[0] and lowerChild2[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperChild2[1] and lowerChild2[1] <= crop["stops"][1] and \
                            crop["starts"][2] <= upperChild2[2] and lowerChild2[2] <= crop["stops"][2])):
                            addAnnotation = True
                    if addAnnotation:
                        if parentTrack not in self.topLevelOperatorView.Annotations.value[name]["divisions"].keys():
                            self.topLevelOperatorView.Annotations.value[name]["divisions"][parentTrack] = {}
                        self.topLevelOperatorView.Annotations.value[name]["divisions"][parentTrack] = self.topLevelOperatorView.divisions[parentTrack]
                    else:
                        annotations = self.topLevelOperatorView.Annotations.value
                        if parentTrack in annotations[name]["divisions"].keys():
                            del annotations[name]["divisions"][parentTrack]
                        self.topLevelOperatorView.Annotations.setValue(annotations)

            if name not in self.topLevelOperatorView.Annotations.value.keys():
                self.topLevelOperatorView.Annotations.value[name] = {}
            if "labels" not in self.topLevelOperatorView.Annotations.value[name].keys():
                self.topLevelOperatorView.Annotations.value[name]["labels"] = {}

            for time in self.topLevelOperatorView.labels.keys():
                for label in self.topLevelOperatorView.labels[time].keys():
                    lower = self.features[time][default_features_key]['Coord<Minimum>'][label]
                    upper = self.features[time][default_features_key]['Coord<Maximum>'][label]

                    addAnnotation = False
                    if len(lower) == 2:
                        if  crop["time"][0] <= time <= crop["time"][1] and \
                            crop["starts"][0] <= upper[0] and lower[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upper[1] and lower[1] <= crop["stops"][1]:
                            addAnnotation = True
                    else:
                        if  crop["time"][0] <= time <= crop["time"][1] and \
                            crop["starts"][0] <= upper[0] and lower[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upper[1] and lower[1] <= crop["stops"][1] and \
                            crop["starts"][2] <= upper[2] and lower[2] <= crop["stops"][2]:
                            addAnnotation = True

                    if addAnnotation:
                        if time not in self.topLevelOperatorView.Annotations.value[name]["labels"].keys():
                            self.topLevelOperatorView.Annotations.value[name]["labels"][time] = {}
                        self.topLevelOperatorView.Annotations.value[name]["labels"][time][label] = self.topLevelOperatorView.labels[time][label]
                    else:
                        annotations = self.topLevelOperatorView.Annotations.value
                        if time in annotations[name]["labels"].keys() and \
                                label in annotations[name]["labels"][time].keys():
                            del annotations[name]["labels"][time][label]
                        if time in annotations[name]["labels"].keys() and \
                                annotations[name]["labels"][time] == {}:
                            del annotations[name]["labels"][time]
                        self.topLevelOperatorView.Annotations.setValue(annotations)

        for name in self.topLevelOperatorView.Annotations.value.keys():
            if self.topLevelOperatorView.Annotations.value[name]["divisions"] == {} and \
                    self.topLevelOperatorView.Annotations.value[name]["labels"] == {}:
                annotations = self.topLevelOperatorView.Annotations.value
                del annotations[name]["labels"]
                del annotations[name]["divisions"]
                del annotations[name]
                self.topLevelOperatorView.Annotations.setValue(annotations)

        for time in self.topLevelOperatorView.labels.keys():
            for label in self.topLevelOperatorView.labels[time].keys():
                labelFound = False
                for name in self.topLevelOperatorView.Annotations.value.keys():
                    if label in self.topLevelOperatorView.Annotations.value[name]["labels"][time].keys():
                        labelFound = True
                if not labelFound:
                    del self.topLevelOperatorView.labels[time][label]

        self._setDirty(self.mainOperator.Annotations, range(self.mainOperator.TrackImage.meta.shape[0]))
        self._setDirty(self.mainOperator.Labels, range(self.mainOperator.TrackImage.meta.shape[0]))
        self._setDirty(self.mainOperator.Divisions, range(self.mainOperator.TrackImage.meta.shape[0]))

    def getLabel(self, time, track):
        for label in self.mainOperator.labels[time].keys():
            if self.mainOperator.labels[time][label] == set([track]):
                return label
        return False

    def getCurrentCrop(self):
        row = self._drawer.cropBoxView.currentIndex()
        name = self._drawer.cropBoxView.itemText(row)
        crop = self.topLevelOperatorView.Crops.value[str(name)]
        return crop

    def _onCropSelected(self, row):

        self._selectedRow = row
        currentName = str(self._drawer.cropBoxView.itemText(row))
        self.editor.brushingModel.setDrawnNumber(row+1)
        brushColor = self._drawer.cropListModel[row].brushColor()
        self.editor.brushingModel.setBrushColor( brushColor )
        ce = self.editor.cropModel._crop_extents
        starts = self.topLevelOperatorView.Crops.value[self._drawer.cropListModel[row].name]["starts"]
        stops = self.topLevelOperatorView.Crops.value[self._drawer.cropListModel[row].name]["stops"]

        # croppingMarkers.onExtentsChanged works correctly only if called on start OR stop coordinates
        self.editor.cropModel.set_crop_extents([[starts[0], ce[0][1]],[starts[1], ce[1][1]],[starts[2], ce[2][1]]])
        self.editor.cropModel.set_crop_extents([[starts[0],stops[0]],[starts[1],stops[1]],[starts[2],stops[2]]])
        if not (self.editor.cropModel._crop_extents[0][0]  == None or self.editor.cropModel.cropZero()):
            cropMidPos = [(b+a)/2 for [a,b] in self.editor.cropModel._crop_extents]
            for i in range(3):
                self.editor.navCtrl.changeSliceAbsolute(cropMidPos[i],i)
        self.editor.navCtrl.panSlicingViews(cropMidPos,[0,1,2])

        times = self.topLevelOperatorView.Crops.value[self._drawer.cropListModel[row].name]["time"]
        self.editor.cropModel.set_crop_times(times)
        self.editor.cropModel.set_scroll_time_outside_crop(False)
        self.editor.navCtrl.changeTimeRelative(times[0] - self.editor.posModel.time)

        self.editor.cropModel.colorChanged.emit(brushColor)
        self._currentCrop = row
        self._currentCropName = currentName
        self.updateLabeledUnlabeledCount(self.topLevelOperatorView.Crops.value[currentName])

    def updateLabeledUnlabeledCount(self, crop):
        labeledObjects = self.getNumberOfLabeledObjects(crop)
        allObjects = self.getNumberOfAllObjects(crop)
        unlabeledObjects = allObjects - labeledObjects
        if unlabeledObjects > 0:
            unlabeledColor = 'red'
        else:
            unlabeledColor = 'green'
        allObjectsColor = 'black'
        self._drawer.unlabeledObjectsCount.setText("<font color="+unlabeledColor+">"+str(int(unlabeledObjects))+"</font>")
        self._drawer.allObjectsCount.setText("<font color="+allObjectsColor+">"+str(int(allObjects))+"</font>")

        time = self.editor.posModel.time
        labeledObjectsFrame = self.getNumberOfLabeledObjectsFrame(crop,time)
        allObjectsFrame = self.getNumberOfAllObjectsFrame(crop,time)
        unlabeledObjectsFrame = allObjectsFrame - labeledObjectsFrame
        if unlabeledObjectsFrame > 0:
            unlabeledColorFrame = 'red'
        else:
            unlabeledColorFrame = 'green'
        self._drawer.unlabeledObjectsCountFrame.setText("<font color="+unlabeledColorFrame+">"+str(int(unlabeledObjectsFrame))+"</font>")
        self._drawer.allObjectsCountFrame.setText("<font color="+allObjectsColor+">"+str(int(allObjectsFrame))+"</font>")

        unlabeledDivisions = self.getNumberOfUnlabeledDivisions()
        if unlabeledDivisions > 0:
            unlabeledDivisionsColor = 'red'
        else:
            unlabeledDivisionsColor = 'green'
        allDivisions = self.getNumberOfDivisions()
        self._drawer.unlabeledDivisionsCount.setText("<font color="+unlabeledDivisionsColor+">"+str(int(unlabeledDivisions))+"</font>")
        self._drawer.allDivisionsCount.setText("<font color="+allObjectsColor+">"+str(int(allDivisions))+"</font>")

        unlabeledMergers = self.getNumberOfUnlabeledMergers()
        if unlabeledMergers > 0:
            unlabeledMergersColor = 'red'
        else:
            unlabeledMergersColor = 'green'
        allMergers = self.getNumberOfMergers()
        self._drawer.unlabeledMergersCount.setText("<font color="+unlabeledMergersColor+">"+str(int(unlabeledMergers))+"</font>")
        self._drawer.allMergersCount.setText("<font color="+allObjectsColor+">"+str(int(allMergers))+"</font>")

    def updateTime(self):
        crop = self.topLevelOperatorView.Crops.value[self._drawer.cropListModel[self._drawer.cropListModel.selectedRow()].name]
        delta = crop["time"][0] - self.editor.posModel.time
        if delta > 0:
            self.editor.navCtrl.changeTimeRelative(delta)
        else:
            delta = self.topLevelOperatorView.Crops.value[self._drawer.cropListModel[self._drawer.cropListModel.selectedRow()].name]["time"][1] - self.editor.posModel.time
            if delta < 0:
                self.editor.navCtrl.changeTimeRelative(delta)

        self.updateLabeledUnlabeledCount(crop)

    def setupLayers( self ):
        layers = []
 
        self.ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent        
        self.ct[255] = QColor(0,0,0,255).rgba() # make -1 black
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
        divItem = QtGui.QListWidgetItem("%d: %d, %d" % (trackid, child1, child2))
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

    @threadRouted
    def _setDivisionsList(self):
        self._drawer.divisionsList.clear()

        for trackid in self.mainOperator.divisions.keys():
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
        for t in self.mainOperator.labels.keys():            
            for oid in self.mainOperator.labels[t].keys():
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
        elif slot is self.mainOperator.Divisions:
            self.mainOperator.Divisions.setDirty([])
        elif slot is self.mainOperator.UntrackedImage:
            roi = SubRegion(self.mainOperator.UntrackedImage, start=[min(timesteps),] + 4*[0,], stop=[max(timesteps)+1,] + list(self.mainOperator.TrackImage.meta.shape[1:]))
            self.mainOperator.UntrackedImage.setDirty(roi)

    def handleEditorLeftClick(self, position5d, globalWindowCoordiante):

        crop = self.getCurrentCrop()
        unlabeledObjectsCount = self.getNumberOfAllObjects(crop)-self.getNumberOfLabeledObjects(crop)

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
                    self._enableButtons(exceptButtons=[self._drawer.divEvent], enable=True)
        else:
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

        self.updateLabeledUnlabeledCount(crop)

        newUnlabeledObjectsCount = self.getNumberOfAllObjects(crop)-self.getNumberOfLabeledObjects(crop)

        if newUnlabeledObjectsCount == 0 and not unlabeledObjectsCount == 0:
            self._informationMessage("Info: All objects in the current crop have been assigned a track label.")

        self._onSaveAnnotations

    def handleEditorRightClick(self, position5d, globalWindowCoordiante):
        crop = self.getCurrentCrop()
        unlabeledObjectsCount = self.getNumberOfAllObjects(crop)-self.getNumberOfLabeledObjects(crop)

        if self.divLock:
            return
                
        oid = self._getObject(self.mainOperator.LabelImage, position5d)
        if oid == 0:
            return
        
        t = position5d[0]
        activeTrack = self._getActiveTrack()
        
        trackids = []
        if t in self.mainOperator.labels.keys() and oid in self.mainOperator.labels[t].keys():
            for l in self.mainOperator.labels[t][oid]:
                trackids.append(l)
        
        title = "Object " + str(oid)
        if len(trackids) == 0:
            title += " contains no track ids."
        elif len(trackids) == 1:
            title += " contains track id " + str(trackids[0]) + "."
        else:
            title += " contains track ids " + str(trackids) + "."
        menu = QtGui.QMenu( self )
        
        menuTitle = QtGui.QAction(title, menu)
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
        for l in trackids:
            if activeTrack != self.misdetIdx and t < crop["time"][1]:
                text = "run automatic tracking for object " + str(oid) + " with track label " + str(l)
                runTracking[text] = l
                menu.addAction(text)

            text = "set active track to label " + str(l)
            setActiveTrack[text] = l
            menu.addAction(text)

            text = "remove label " + str(l)
            delLabel[text] = l
            menu.addAction(text)
            
            if l != self.misdetIdx:
                if t < crop["time"][1]:
                    text = "remove label " + str(l) + " from here to end"
                    delSubtrackToEnd[text] = l
                    menu.addAction(text)

                if t > crop["time"][0]:
                    text = "remove label " + str(l) + " from here to start"
                    delSubtrackToStart[text] = l
                    menu.addAction(text)
            
            menu.addSeparator()
        
        delDivision = {}
        if activeTrack != self.misdetIdx:
            for trackid in trackids:
                if trackid in self.mainOperator.divisions.keys() and self.mainOperator.divisions[trackid][1] == t:
                    text = "remove division event from label " + str(trackid)
                    delDivision[text] = trackid
                    menu.addSeparator()
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

        elif selection in delSubtrackToEnd.keys():
            track2remove = delSubtrackToEnd[selection]
            maxt = self.mainOperator.LabelImage.meta.shape[0]
            for time in range(t,maxt):
                for oid in self.mainOperator.labels[time].keys():
                    if track2remove in self.mainOperator.labels[time][oid]:
                        self._delLabel(time, oid, track2remove)
            
            self._setDirty(self.mainOperator.TrackImage, range(t,maxt))
            self._setDirty(self.mainOperator.UntrackedImage, range(t, maxt))
            self._setDirty(self.mainOperator.Labels, range(t,maxt))

        elif selection in delSubtrackToStart.keys():
            track2remove = delSubtrackToStart[selection]
            for time in range(0,t+1):
                for oid in self.mainOperator.labels[time].keys():
                    if track2remove in self.mainOperator.labels[time][oid]:
                        self._delLabel(time, oid, track2remove)
            
            self._setDirty(self.mainOperator.TrackImage, range(0,t+1))
            self._setDirty(self.mainOperator.UntrackedImage, range(0,t+1))
            self._setDirty(self.mainOperator.Labels, range(0,t+1))
            
        elif selection in runTracking.keys():
            self._runSubtracking(position5d, oid, runTracking[selection])
        
        elif selection in delDivision.keys():
            self._delDivisionEvent(delDivision[selection])

        elif selection in setActiveTrack.keys():
            for i in range(self._drawer.activeTrackBox.count()):
                if int(self._drawer.activeTrackBox.itemText(i)) == setActiveTrack[selection]:
                    self._drawer.activeTrackBox.setCurrentIndex(i)

        else:
            assert False, "cannot reach this"

        self.updateLabeledUnlabeledCount(crop)
        newUnlabeledObjectsCount = self.getNumberOfAllObjects(crop)-self.getNumberOfLabeledObjects(crop)

        if newUnlabeledObjectsCount == 0 and not unlabeledObjectsCount == 0:
            self._informationMessage("Info: All objects in the current crop have been assigned a track label.")

        self._onSaveAnnotations

    def handleEditorToolTip(self, position5d, globalWindowCoordiante):
        oid = self._getObject(self.mainOperator.LabelImage, position5d)
        trackids = []
        t = position5d[0]
        if t in self.mainOperator.labels.keys() and oid in self.mainOperator.labels[t].keys():
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

        self._onSaveAnnotations

    def _currentActiveTrackChanged(self):
        self.mainOperator.ActiveTrack.setValue(self._getActiveTrack())

    def _currentCropBoxChanged(self):
        self._currentCrop = self._drawer.cropBoxView.currentIndex()
        if self._currentCrop >= 0:
            self._currentCropName = str(self._drawer.cropBoxView.itemText(self._currentCrop))
            self._drawer.cropListModel.select(self._currentCrop)
            self._onCropSelected(self._currentCrop)

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
        if t in self.labelsWithDivisions.keys() and track2remove in self.labelsWithDivisions[t] and errorMessage:
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

        self._onSaveAnnotations
        return True
        
    def _onDelTrackPressed(self):        
        activeTrackBox = self._drawer.activeTrackBox
        if activeTrackBox.count() == 0:            
            return 
        
        track2remove = self._getActiveTrack()
        idx2remove = activeTrackBox.currentIndex()

        affectedT = []
        success = True
        for t in self.mainOperator.labels.keys():
            for oid in self.mainOperator.labels[t].keys():
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

        self._onSaveAnnotations

    def _addObjectToTrack(self, activeTrack, oid, t):

        crop = self.getCurrentCrop()

        if t not in range(crop["time"][0],crop["time"][1]+1):
            return -98

        lower = self.features[t][default_features_key]['Coord<Minimum>'][oid]
        upper = self.features[t][default_features_key]['Coord<Maximum>'][oid]
        addAnnotation = False
        if len(lower) == 2:
            if  crop["starts"][0] <= upper[0] and lower[0] <= crop["stops"][0] and \
                crop["starts"][1] <= upper[1] and lower[1] <= crop["stops"][1]:
                addAnnotation = True
        else:
            if  crop["starts"][0] <= upper[0] and lower[0] <= crop["stops"][0] and \
                crop["starts"][1] <= upper[1] and lower[1] <= crop["stops"][1] and \
                crop["starts"][2] <= upper[2] and lower[2] <= crop["stops"][2]:
                addAnnotation = True

        if not addAnnotation:
            return -99 # info message depends on the caller: rightClick/runAutomaticTracking or leftClick(addObjectToTrack)

        if t not in self.mainOperator.labels.keys():
            self.mainOperator.labels[t] = {}
        if oid not in self.mainOperator.labels[t].keys():
            self.mainOperator.labels[t][oid] = set()
        if activeTrack == self.misdetIdx:
            if len(self.mainOperator.labels[t][oid]) > 0:
                if self.misdetIdx not in self.mainOperator.labels[t][oid]:
                    self._criticalMessage("Error: This object is already marked as part of a track, cannot mark it as a misdetection.")
                self._onMarkMisdetectionPressed()
                return -1
        else:
            for tracklist in self.mainOperator.labels[t].values():
                if activeTrack in tracklist:
                    if activeTrack not in self.mainOperator.labels[t][oid]:
                        self._criticalMessage("Error: There is already an object with this track id in this time step.")
                        return -1
                    elif t == self.topLevelOperatorView.Crops.value[self._currentCropName]["time"][1]:
                        self._criticalMessage("Error: You have reached the last time frame in this crop.")
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
                if res == -98:
                    self._informationMessage("Info: Object " + str(oid) + " in time frame " + str(t) + " left the current crop time boundary. " + \
                                         "Stopping automatic tracking at crop boundary.")
                    self._gotoObject(uniqueLabels[0], t, keepXYZ=True)
                    break
                elif res == -99:
                    self._informationMessage("Info: Object " + str(oid) + " in time frame " + str(t) + " left the current crop spatial boundary. " + \
                                         "Stopping automatic tracking at crop boundary.")
                    self._gotoObject(uniqueLabels[0], t, keepXYZ=True)
                    break
                elif res == -1:
                    self._gotoObject(uniqueLabels[0], t, keepXYZ=True)
                    return
                
                oid_prev = uniqueLabels[0]
                li_prev = li_cur        
            
            if t_end == self.mainOperator.LabelImage.meta.shape[0] - 1:
                self._log('tracking reached last time step.')
                
            self._setDirty(self.mainOperator.TrackImage, range(t_start, max(t_start+1,t_end-1)))
            self._setDirty(self.mainOperator.UntrackedImage, range(t_start, max(t_start+1,t_end-1)))
            self._setDirty(self.mainOperator.Labels, range(t_start, max(t_start+1,t_end-1)))

            if t_end > 0:
                self._setPosModel(time=t_end)
        
        def _handle_finished(*args):
            self._enableButtons(enable=True)
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            
        def _handle_failure( exc, exc_info ):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            msg = "Exception raised during tracking.  See traceback above.\n"
            log_exception( logger, msg, exc_info )
        
        for i in range(self._drawer.activeTrackBox.count()):
            if int(self._drawer.activeTrackBox.itemText(i)) == track:
                self._drawer.activeTrackBox.setCurrentIndex(i)

        crop = self.getCurrentCrop()
        unlabeledObjectsCount = self.getNumberOfAllObjects(crop)-self.getNumberOfLabeledObjects(crop)

        self.applet.busy = True
        self.applet.appletStateUpdateRequested.emit()
        self._enableButtons(enable=False)
        req = Request( _subtracking )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()

        self.updateLabeledUnlabeledCount(crop)
        newUnlabeledObjectsCount = self.getNumberOfAllObjects(crop)-self.getNumberOfLabeledObjects(crop)

        if newUnlabeledObjectsCount == 0 and not unlabeledObjectsCount == 0:
            self._informationMessage("Info: All objects in the current crop have been assigned a track label.")

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
        self.divLock = not self.divLock             
        self._drawer.divEvent.setChecked(not self.divLock)
        self.divs = []
        
        self._enableButtons(exceptButtons=[self._drawer.divEvent], enable=(not self.divLock))                      

        self._onSaveAnnotations

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
        for oid in self.mainOperator.labels[t].keys():
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
        
        self._onSaveAnnotations

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
        for t in oid2tids.keys():
            moves[t] = []
            divs[t] = []
            mergers[t] = []
            apps[t] = []
            disapps[t] = []
            multiMoves[t] = []
        
        t_start = time_range[0]
        
        tracks_starting_in_div = {}
        for d in divisions.keys():
            [tid_child1, tid_child2], t_div = divisions[d]
            tracks_starting_in_div[tid_child1] = t_div + 1
            tracks_starting_in_div[tid_child2] = t_div + 1
            
                            
        for tid in sorted(list(alltids)):
            oid_prev = None            
            
            for t in sorted(oid2tids.keys()):  
                oid_cur = None                
                for o in oid2tids[t].keys():
                    if tid in oid2tids[t][o]:
                        oid_cur = o
                        break
                       
                if (oid_prev is not None) and (oid_cur is None): # track ends
                    if tid in divisions.keys(): # division
                        [tid_child1, tid_child2], t_div = divisions[tid]
                        
                        if t == t_div+1:                    
                            oid_child1 = None
                            oid_child2 = None
                            for o in oid2tids[t].keys():
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
                                child1_exists = (oid_child1 in oid2tids[t].keys())
                                child2_exists = (oid_child2 in oid2tids[t].keys())
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
                    if tid in tracks_starting_in_div.keys() and tracks_starting_in_div[tid] != t:
                        self._appendUnique(apps[t], (oid_cur, 0.))
                
                elif (oid_prev is not None) and (oid_cur is not None): # move
                    self._appendUnique(moves[t], (oid_prev, oid_cur, 0.))
                    
                    if len(oid2tids[t][oid_cur]) == 1 and len(oid2tids[t-1][oid_prev]) > 1:
                        t_multiprev = None
                        oid_multiprev = None
                        
                        found = False            
                        for tt in reversed(range(t)):
                            for o in oid2tids[tt].keys():
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
        for t in oid2tids.keys():
            for oid in oid2tids[t].keys():
                if len(oid2tids[t][oid]) > 1:
                    mergers[t].append((oid, len(oid2tids[t][oid]), 0.))                    
                    m_size = len(oid2tids[t][oid])
                    if m_size not in merger_sizes.keys():
                        merger_sizes[m_size] = 0
                    merger_sizes[m_size] += 1
        
        logging.info( 'Merger-Sizes: {}'.format(merger_sizes) )
        
        return oid2tids, disapps, apps, divs, moves, mergers, multiMoves
        
    def _onExportDivisionsButtonPressed(self):
        options = QtGui.QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QtGui.QFileDialog.DontUseNativeDialog

        out_fn = encode_from_qstring(QtGui.QFileDialog.getSaveFileName(self, 'Save Mergers',os.path.expanduser("~") + "/divisions.csv", options=options))
        
        if out_fn is None or str(out_fn) == '':            
            return
        if out_fn.split(".")[-1] != "csv":
            out_fn += ".csv"
        
        self.applet.busy = True
        self.applet.appletStateUpdateRequested.emit()
        try:            
            import csv
            with open(out_fn, 'w') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['timestep_parent','track_id_parent','track_id_child1','track_id_child2'])
                for tid in self.mainOperator.divisions.keys():
                    children, t_parent = self.mainOperator.divisions[tid]
                    writer.writerow([t_parent, tid, children[0], children[1]])
                
        finally:
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()  
    
    def _onExportMergersButtonPressed(self):        
        options = QtGui.QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QtGui.QFileDialog.DontUseNativeDialog

        out_fn = encode_from_qstring(QtGui.QFileDialog.getSaveFileName(self, 'Save Mergers',os.path.expanduser("~") + "/mergers.csv", options=options))
        
        if out_fn is None or str(out_fn) == '':            
            return
        if out_fn.split(".")[-1] != "csv":
            out_fn += ".csv"
        
        self.applet.busy = True
        self.applet.appletStateUpdateRequested.emit()
        try:            
            import csv
            with open(out_fn, 'w') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['timestep','object_id','track_ids'])
                for t in self.mainOperator.labels.keys():
                    for oid in self.mainOperator.labels[t].keys():
                        if len(self.mainOperator.labels[t][oid]) > 1:
                            writer.writerow([t,oid,";".join(list(str(x) for x in self.mainOperator.labels[t][oid]))])
                
        finally:
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()            
            
            
    def _onExportButtonPressed(self):
        import h5py        
        options = QtGui.QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QtGui.QFileDialog.DontUseNativeDialog

        directory = encode_from_qstring(QtGui.QFileDialog.getExistingDirectory(self, 'Select Directory',os.path.expanduser("~"), options=options))      
        
        if directory is None or str(directory) == '':            
            return
        directory = str(directory)
        
        def _handle_progress(x):       
            self.applet.progressSignal.emit(x)
            
        def _export():
            self.applet.busy = True
            self.applet.appletStateUpdateRequested.emit()    
            oid2tids, disapps, apps, divs, moves, mergers, multiMoves = self._getEvents()
            
            num_files = float(len(oid2tids.keys()))
            
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
                        if "segmentation" in f_curr.keys():
                            del f_curr["segmentation"]
                        
                        seg = f_curr.create_group("segmentation")            
                        # write label image
                        seg.create_dataset("labels", data = labelImage, dtype=numpy.uint32, compression=1)
                        
                        oids_meta = numpy.sort(vigra.analysis.unique(labelImage)).astype(numpy.uint32)[1:]  
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
                    
                except IOError:                    
                    self._criticalMessage("File " + str(fn) + " exists already. Please choose a different folder or delete the file(s).")
                    return
                _handle_progress(t/num_files * 100)
            self._log("-> tracking successfully exported")
        
        def _handle_finished(*args):            
            self.applet.progressSignal.emit(100)
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
               
        def _handle_failure( exc, exc_info ):
            msg = "Exception raised during export.  See traceback above.\n"
            log_exception( logger, msg, exc_info )
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            self.applet.progressSignal.emit(100)
        
        self.applet.progressSignal.emit(0)  
        req = Request( _export )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()

    def _onExportTifButtonPressed(self):
        import vigra        
        
        options = QtGui.QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QtGui.QFileDialog.DontUseNativeDialog

        directory = encode_from_qstring(QtGui.QFileDialog.getExistingDirectory(self, 'Select Directory',os.path.expanduser("~"), options=options))    
        if directory is None or len(str(directory)) == 0:
            return
        
        def _handle_progress(x):       
            self.applet.progressSignal.emit(x)
            
        def _export():
            self.applet.busy = True
            self.applet.appletStateUpdateRequested.emit()
            divisions = self.mainOperator.divisions
            inverseDivisions = {}
            for k, vals in divisions.items():
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
                
            for tid in inverseDivisions.keys():
                rootTid = inverseDivisions[tid]
                while rootTid in inverseDivisions.keys():
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
            self.applet.appletStateUpdateRequested.emit()
            self.applet.progressSignal.emit(100)
               
        def _handle_failure( exc, exc_info ):
            msg = "Exception raised during export.  See traceback above.\n"
            log_exception( logger, msg, exc_info )
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            self.applet.progressSignal.emit(100)       
                
        self.applet.progressSignal.emit(0)
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
        for oid in self.mainOperator.labels[t].keys():
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
        self._drawer.logOutput.moveCursor(QtGui.QTextCursor.End)
        logger.info( prompt )

    def _criticalMessage(self, prompt):
        self.emit( QtCore.SIGNAL('postCriticalMessage(QString)'), prompt)

    def _questionMessage(self, prompt):
        self.emit( QtCore.SIGNAL('postQuestionMessage(QString)'), prompt)

    def _informationMessage(self, prompt):
        self.emit( QtCore.SIGNAL('postInformationMessage(QString)'), prompt)

    @threadRouted
    def postCriticalMessage(self, prompt):
        QtGui.QMessageBox.critical(self, "Error", prompt, QtGui.QMessageBox.Ok)
        
    @threadRouted
    def postQuestionMessage(self, prompt):
        qBox = QtGui.QMessageBox()
        qBox.setWindowTitle("Confirm")
        qBox.setText(prompt)
        qBox.setStandardButtons( QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        qBox.setDefaultButton( QtGui.QMessageBox.Cancel )
        retVal = qBox.exec_()
        if retVal == QtGui.QMessageBox.Ok:
            self.deleteAllTraining = True

    @threadRouted
    def postInformationMessage(self, prompt):
        QtGui.QMessageBox.information(self, "Info", prompt, QtGui.QMessageBox.Ok)

    @threadRouted
    def _enableButtons(self, exceptButtons=None, enable=True):
        buttons = [self._drawer.activeTrackBox, 
                   self._drawer.delTrack,
                   self._drawer.newTrack,
                   self._drawer.markMisdetection,
                   self._drawer.divEvent,
                   ]
                
        for b in buttons:
            if exceptButtons is None or b not in exceptButtons:
                b.setEnabled(enable)
