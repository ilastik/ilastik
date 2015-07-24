from PyQt4 import uic, QtGui
from PyQt4.QtGui import *
import os
import logging
import sys
import re
import traceback
import math
from PyQt4.QtCore import pyqtSignal

import pgmlink

from ilastik.applets.tracking.base.trackingBaseGui import TrackingBaseGui
from ilastik.utility.exportingOperator import ExportingGui
from ilastik.utility.gui.threadRouter import threadRouted
from ilastik.utility.gui.titledMenu import TitledMenu
from ilastik.utility.ipcProtocol import Protocol
from ilastik.shell.gui.ipcManager import IPCFacade
from ilastik.config import cfg as ilastik_config
from ilastik.utility import bind

from lazyflow.request.request import Request

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class StructuredTrackingGui(TrackingBaseGui, ExportingGui):
    
    withMergers = True
    @threadRouted
    def _setMergerLegend(self, labels, selection):   
        for i in range(1,len(labels)+1):
            if i <= selection:
                labels[i-1].setVisible(True)
            else:
                labels[i-1].setVisible(False)
    
    def _loadUiFile(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        parameters = self.topLevelOperatorView.Parameters.value        
        if 'maxDist' in parameters.keys():
            self._drawer.maxDistBox.setValue(parameters['maxDist'])
        if 'maxObj' in parameters.keys():
            self._drawer.maxObjectsBox.setValue(parameters['maxObj'])
        if 'divThreshold' in parameters.keys():
            self._drawer.divThreshBox.setValue(parameters['divThreshold'])
        if 'avgSize' in parameters.keys():
            self._drawer.avgSizeBox.setValue(parameters['avgSize'][0])
        if 'withTracklets' in parameters.keys():
            self._drawer.trackletsBox.setChecked(parameters['withTracklets'])
        if 'sizeDependent' in parameters.keys():
            self._drawer.sizeDepBox.setChecked(parameters['sizeDependent'])
        if 'divWeight' in parameters.keys():
            self._drawer.divWeightBox.setValue(parameters['divWeight'])
        if 'transWeight' in parameters.keys():
            self._drawer.transWeightBox.setValue(parameters['transWeight'])
        if 'withDivisions' in parameters.keys():
            self._drawer.divisionsBox.setChecked(parameters['withDivisions'])
        if 'withOpticalCorrection' in parameters.keys():
            self._drawer.opticalBox.setChecked(parameters['withOpticalCorrection'])
        if 'withClassifierPrior' in parameters.keys():
            self._drawer.classifierPriorBox.setChecked(parameters['withClassifierPrior'])
        if 'withMergerResolution' in parameters.keys():
            self._drawer.mergerResolutionBox.setChecked(parameters['withMergerResolution'])
        if 'borderAwareWidth' in parameters.keys():
            self._drawer.bordWidthBox.setValue(parameters['borderAwareWidth'])
        if 'cplex_timeout' in parameters.keys():
            self._drawer.timeoutBox.setText(str(parameters['cplex_timeout']))
        if 'appearanceCost' in parameters.keys():
            self._drawer.appearanceBox.setValue(parameters['appearanceCost'])
        if 'disappearanceCost' in parameters.keys():
            self._drawer.disappearanceBox.setValue(parameters['disappearanceCost'])
        
        return self._drawer

    def initAppletDrawerUi(self):
        self._previousCrop = -1
        self._currentCrop = -1
        self._currentCropName = ""

        super(StructuredTrackingGui, self).initAppletDrawerUi()

        self._allowedTimeoutInputRegEx = re.compile('^[0-9]*$')
        self._drawer.timeoutBox.textChanged.connect(self._onTimeoutBoxChanged)

        if not ilastik_config.getboolean("ilastik", "debug"):
            assert self._drawer.trackletsBox.isChecked()
            self._drawer.trackletsBox.hide()
            
            assert not self._drawer.hardPriorBox.isChecked()
            self._drawer.hardPriorBox.hide()

            assert not self._drawer.opticalBox.isChecked()
            self._drawer.opticalBox.hide()

            self._drawer.maxDistBox.hide() # hide the maximal distance box
            self._drawer.label_2.hide() # hide the maximal distance label
            self._drawer.label_5.hide() # hide division threshold label
            self._drawer.divThreshBox.hide()
            self._drawer.label_25.hide() # hide avg. obj size label
            self._drawer.avgSizeBox.hide()
          
        self.mergerLabels = [self._drawer.merg1,
                             self._drawer.merg2,
                             self._drawer.merg3,
                             self._drawer.merg4,
                             self._drawer.merg5,
                             self._drawer.merg6,
                             self._drawer.merg7]
        for i in range(len(self.mergerLabels)):
            self._labelSetStyleSheet(self.mergerLabels[i], self.mergerColors[i+1])
        
        self._onMaxObjectsBoxChanged()
        self._drawer.maxObjectsBox.valueChanged.connect(self._onMaxObjectsBoxChanged)                
        #self._drawer.ImportAnnotationsButton.clicked.connect(self._onImportAnnotationsButtonPressed)
        self._drawer.StructuredLearningButton.clicked.connect(self._onRunStructuredLearningButtonPressed)
        self.features = self.topLevelOperatorView.ObjectFeatures(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()
        #, {'RegionCenter','Coord<Minimum>','Coord<Maximum>'}).wait()

        self._drawer.divWeightBox.valueChanged.connect(self._onDivisionWeightBoxChanged)                
        self._drawer.detWeightBox.valueChanged.connect(self._onDetectionWeightBoxChanged)                
        self._drawer.transWeightBox.valueChanged.connect(self._onTransitionWeightBoxChanged)                
        self._drawer.appearanceBox.valueChanged.connect(self._onAppearanceWeightBoxChanged)                
        self._drawer.disappearanceBox.valueChanged.connect(self._onDisappearanceWeightBoxChanged)                
        self._drawer.maxObjectsBox.valueChanged.connect(self._onMaxObjectsBoxChanged)

        self._divisionWeight = self.topLevelOperatorView.DivisionWeight.value
        self._detectionWeight = self.topLevelOperatorView.DetectionWeight.value
        self._transitionWeight =self.topLevelOperatorView.TransitionWeight.value
        self._appearanceWeight = self.topLevelOperatorView.AppearanceWeight.value
        self._disappearanceWeight = self.topLevelOperatorView.DisappearanceWeight.value

        self._drawer.detWeightBox.setValue(self._detectionWeight)
        self._drawer.divWeightBox.setValue(self._divisionWeight)
        self._drawer.transWeightBox.setValue(self._transitionWeight)
        self._drawer.appearanceBox.setValue(self._appearanceWeight)
        self._drawer.disappearanceBox.setValue(self._disappearanceWeight)

        self._maxNumObj = self.topLevelOperatorView.MaxNumObjOut.value
        self._drawer.maxObjectsBox.setValue(self.topLevelOperatorView.MaxNumObjOut.value)

        #self.topLevelOperatorView.Annotations.notifyReady( bind(self._updateAnnotationsFromOperator) )
        #self.topLevelOperatorView.Labels.notifyReady( bind(self._updateLabelsFromOperator) )
        #self.topLevelOperatorView.Divisions.notifyReady( bind(self._updateDivisionsFromOperator) )
        
    @threadRouted
    def _onTimeoutBoxChanged(self, *args):
        inString = str(self._drawer.timeoutBox.text())
        if self._allowedTimeoutInputRegEx.match(inString) is None:
            self._drawer.timeoutBox.setText(inString.decode("utf8").encode("ascii", "replace")[:-1])

#    @threadRouted
#    def _onMaxObjectsBoxChanged(self, *args):
#        self._maxNumObj = self._drawer.maxObjectsBox.value()

    @threadRouted
    def _onDivisionWeightBoxChanged(self, *args):
        self._divisionWeight = self._drawer.divWeightBox.value()
        self.topLevelOperatorView.DivisionWeight.setValue(self._divisionWeight)

    @threadRouted
    def _onDetectionWeightBoxChanged(self, *args):
        self._detectionWeight = self._drawer.detWeightBox.value()
        self.topLevelOperatorView.DetectionWeight.setValue(self._detectionWeight)

    @threadRouted
    def _onTransitionWeightBoxChanged(self, *args):
        self._transitionWeight = self._drawer.transWeightBox.value()
        self.topLevelOperatorView.TransitionWeight.setValue(self._transitionWeight)

    @threadRouted
    def _onAppearanceWeightBoxChanged(self, *args):
        self._appearanceWeight = self._drawer.appearanceBox.value()
        self.topLevelOperatorView.AppearanceWeight.setValue(self._appearanceWeight)

    @threadRouted
    def _onDisappearanceWeightBoxChanged(self, *args):
        self._disappearanceWeight = self._drawer.disappearanceBox.value()
        self.topLevelOperatorView.DisappearanceWeight.setValue(self._disappearanceWeight)
        
    def _setRanges(self, *args):
        super(StructuredTrackingGui, self)._setRanges()
        maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
        maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
        maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1
        
        maxBorder = min(maxx, maxy)
        if maxz != 0:
            maxBorder = min(maxBorder, maxz)
        self._drawer.bordWidthBox.setRange(0, maxBorder/2)
        
    @threadRouted
    def _onMaxObjectsBoxChanged(self, *args):
        self._setMergerLegend(self.mergerLabels, self._drawer.maxObjectsBox.value())
        self._maxNumObj = self._drawer.maxObjectsBox.value()
        print "-----------------0-----------self.topLevelOperatorView.MaxNumObjOut---------------------->",self.topLevelOperatorView.MaxNumObjOut.value
        #self.topLevelOperatorView.MaxNumObjOut.setValue(self._maxNumObj)
        #print "-----------------1-----------self.topLevelOperatorView.MaxNumObjOut---------------------->",self.topLevelOperatorView.MaxNumObjOut.value

    #def _updateAnnotationsFromOperator(self):
    #    self.annotations = self.topLevelOperatorView.Annotations.value

#    def _updateLabelsFromOperator(self):
#        self.labels = self.topLevelOperatorView.Labels.wait()

#    def _updateDivisionsFromOperator(self):
#        self.divisions = self.topLevelOperatorView.Divisions.wait()

    def initializeAnnotations(self):

        #print " -------LABELS--slot----->",self.topLevelOperatorView.Labels.value
        #print " -----DIVISIONS-slot----->",self.topLevelOperatorView.Divisions.value
        #print " -------labels------->",self.topLevelOperatorView.labels
        #print " -----divisions------>",self.topLevelOperatorView.divisions

        #print " -------LABELS--slot----->",self.mainOperator.Labels.value
        #print " -----DIVISIONS-slot----->",self.mainOperator.Divisions.value
        #print " -------labels------->",self.mainOperator.labels
        #print " -----divisions------>",self.mainOperator.divisions

        for name in self.topLevelOperatorView.Crops.value.keys():
            crop = self.topLevelOperatorView.Crops.value[name]

            for time in range(crop["time"][0],crop["time"][1]+1):
                if time in self.topLevelOperatorView.labels.keys():
                    for label in self.topLevelOperatorView.labels[time].keys():
                        lower = self.features[time][default_features_key]['Coord<Minimum>'][label]
                        upper = self.features[time][default_features_key]['Coord<Maximum>'][label]

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

                        # timeUnicodeStr = unicode(str(time))
                        # labelUnicodeStr = unicode(str(label))
                        if addAnnotation:
                            if name not in self.topLevelOperatorView.Annotations.value.keys():
                                self.topLevelOperatorView.Annotations.value[name] = {}
                            if "labels" not in self.topLevelOperatorView.Annotations.value[name].keys():
                                self.topLevelOperatorView.Annotations.value[name]["labels"] = {}
                            if time not in self.topLevelOperatorView.Annotations.value[name]["labels"].keys():
                                self.topLevelOperatorView.Annotations.value[name]["labels"][time] = {}
                            self.topLevelOperatorView.Annotations.value[name]["labels"][time][label] = self.topLevelOperatorView.labels[time][label]
                            # if timeUnicodeStr not in self.topLevelOperatorView.Annotations.value[name]["labels"].keys():
                            #     self.topLevelOperatorView.Annotations.value[name]["labels"][timeUnicodeStr] = {}
                            # self.topLevelOperatorView.Annotations.value[name]["labels"][timeUnicodeStr][labelUnicodeStr] = self.topLevelOperatorView.labels[time][label]

            for parentTrack in self.topLevelOperatorView.divisions.keys():
                time = self.topLevelOperatorView.divisions[parentTrack][1]
                child1Track = self.topLevelOperatorView.divisions[parentTrack][0][0]
                child2Track = self.topLevelOperatorView.divisions[parentTrack][0][1]

                parent = self.getLabel(time, parentTrack)
                child1 = self.getLabel(time+1, child1Track)
                child2 = self.getLabel(time+1, child2Track)

                #if not (parent and child1 and child2):
                #    print "WARNING:Your divisons and labels do not match for time ",time, " and parent track ", parentTrack,"(label ",parent," )!"
                #else:
                if (parent and child1 and child2):
                    lowerParent = self.features[time][default_features_key]['Coord<Minimum>'][parent]
                    upperParent = self.features[time][default_features_key]['Coord<Maximum>'][parent]

                    lowerChild1 = self.features[time][default_features_key]['Coord<Minimum>'][child1]
                    upperChild1 = self.features[time][default_features_key]['Coord<Maximum>'][child1]

                    lowerChild2 = self.features[time][default_features_key]['Coord<Minimum>'][child2]
                    upperChild2 = self.features[time][default_features_key]['Coord<Maximum>'][child2]

                    addAnnotation = False
                    if len(lowerParent) == 2:
                        if (crop["time"][0] <= time and time <= crop["time"][1]+1) and \
                            ((crop["starts"][0] <= upperParent[0] and lowerParent[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperParent[1] and lowerParent[1] <= crop["stops"][1]) or \
                            ( crop["starts"][0] <= upperChild1[0] and lowerChild1[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperChild1[1] and lowerChild1[1] <= crop["stops"][1]) or \
                            ( crop["starts"][0] <= upperChild2[0] and lowerChild2[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperChild2[1] and lowerChild2[1] <= crop["stops"][1])):
                            addAnnotation = True
                    else:
                        if (crop["time"][0] <= time and time <= crop["time"][1]+1) and \
                            ((crop["starts"][0] <= upperParent[0] and lowerParent[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperParent[1] and lowerParent[1] <= crop["stops"][1] and \
                            crop["starts"][2] <= upperParent[2] and lowerParent[2] <= crop["stops"][2]) or \
                            ( crop["starts"][0] <= upperChild1[0] and lowerChild1[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperChild1[1] and lowerChild1[1] <= crop["stops"][1] and \
                            crop["starts"][2] <= upperChild1[2] and lowerChild1[2] <= crop["stops"][2]) or \
                            ( crop["starts"][0] <= upperChild2[0] and lowerChild2[0] <= crop["stops"][0] and \
                            crop["starts"][1] <= upperChild2[1] and lowerChild2[1] <= crop["stops"][1] and \
                            crop["starts"][2] <= upperChild2[2] and lowerChild2[2] <= crop["stops"][2])):
                            addAnnotation = True
                    if addAnnotation:
                        if name not in self.topLevelOperatorView.Annotations.value.keys():
                            self.topLevelOperatorView.Annotations.value[name] = {}
                        if "divisions" not in self.topLevelOperatorView.Annotations.value[name].keys():
                            self.topLevelOperatorView.Annotations.value[name]["divisions"] = {}
                        if parentTrack not in self.topLevelOperatorView.Annotations.value[name]["divisions"].keys():
                            self.topLevelOperatorView.Annotations.value[name]["divisions"][parentTrack] = {}
                        self.topLevelOperatorView.Annotations.value[name]["divisions"][parentTrack] = self.topLevelOperatorView.divisions[parentTrack]

        #self._setDirty(self.topLevelOperatorView.Annotations, range(self.topLevelOperatorView.LabelImage.meta.shape[0]))

        self._annotations = self.mainOperator.Annotations.value
        #print "Annotations---> ", self.mainOperator.Annotations.value

    def getLabel(self, time, track):
        for label in self.mainOperator.labels[time].keys():
            if self.mainOperator.labels[time][label] == set([track]):
                return label
        return False

#    def _setDirty(self, slot, timesteps):
        #if slot is self.topLevelOperatorView.Annotations:
        #    self.topLevelOperatorView.Annotations.setDirty([])

    def _onRunStructuredLearningButtonPressed(self):

        #print "RunStructuredLearningButton PRESSED Crops Slot", self.mainOperator.Crops.value
        #print "RunStructuredLearningButton PRESSED Annotation Slot", self.mainOperator.Annotations.value


        self.initializeAnnotations()





        #print "RunStructuredLearningButton BEFORE Annotation Slot", self.mainOperator.Annotations.value
        self._annotations = self.mainOperator.Annotations.value
        #print "RunStructuredLearningButton AFTER Annotation Slot", self.mainOperator.Annotations.value
        



        #print "building consTracker"
        median_obj_size = [0]

        from_z = self._drawer.from_z.value()
        to_z = self._drawer.to_z.value()
        ndim=3
        if (to_z - from_z == 0):
            ndim=2

        maxObj=self._maxNumObj

        print "----maxObj--->", maxObj
        print "----ndim--->", ndim

        fieldOfView = pgmlink.FieldOfView(float(0),float(0),float(0),float(0),float(self.topLevelOperatorView.LabelImage.meta.shape[0]),float(self.topLevelOperatorView.LabelImage.meta.shape[1]),float(self.topLevelOperatorView.LabelImage.meta.shape[2]),float(self.topLevelOperatorView.LabelImage.meta.shape[3]))
        consTracker = pgmlink.ConsTracking(
            maxObj,
            True,#sizeDependent,   # size_dependent_detection_prob
            float(median_obj_size[0]), # median_object_size
            float(200),#maxDist),
            True,#withDivisions,
            float(0.5),#divThreshold),
            "none",  # detection_rf_filename
            fieldOfView,
            "none", # dump traxelstore,
            pgmlink.ConsTrackingSolverType.CplexSolver,
            ndim)

        #print "building traxelStore", self.topLevelOperatorView.LabelImage.meta.shape[0], self.topLevelOperatorView.LabelImage.meta.shape[1],self.topLevelOperatorView.LabelImage.meta.shape[2],self.topLevelOperatorView.LabelImage.meta.shape[3]

        time_range = range (0,self.topLevelOperatorView.LabelImage.meta.shape[0])
        traxelStore, empty_frame = self.mainOperator._generate_traxelstore(
            time_range,
            (0,self.topLevelOperatorView.LabelImage.meta.shape[1]),#x_range
            (0,self.topLevelOperatorView.LabelImage.meta.shape[2]),#y_range
            (0,self.topLevelOperatorView.LabelImage.meta.shape[3]),#z_range,
            (0, 100000),#size_range
            1.0,# x_scale
            1.0,# y_scale
            1.0,# z_scale,
            median_object_size=median_obj_size,
            with_div=True,#withDivisions,
            with_opt_correction=False,#withOpticalCorrection,
            with_classifier_prior=True)#withClassifierPrior)

        if empty_frame:
            raise Exception, 'cannot track frames with 0 objects, abort.'

        #print "building cons Hypotheses Graph"
        hypothesesGraph = consTracker.buildGraph(traxelStore)

        #print "building structuredLearningTracker"
        sizeDependent = False
        structuredLearningTracker = pgmlink.StructuredLearningTracking(
            hypothesesGraph,
            maxObj,
            sizeDependent,   # size_dependent_detection_prob
            float(median_obj_size[0]), # median_object_size
            200,#maxDist,
            True,#withDivisions,
            float(0.5),#divThreshold),
            "none",  # detection_rf_filename
            fieldOfView,
            "none", # dump traxelstore,
            pgmlink.ConsExplicitTrackingSolverType.CplexSolver,
            ndim)

        #print "update hypothesesGraph: labels"
        structuredLearningTracker.addLabels()

        #print "update hypothesesGraph: labels ---> adding APPEARANCE/TRANSITION/DISAPPEARANCE labels"
        #detectionProbabilities = self.mainOperator.DetectionProbabilities(time_range).wait()
        for cropKey in self.mainOperator.Annotations.value.keys():
            crop = self.mainOperator.Annotations.value[cropKey]
            #print "..........................................cropKey, crop",cropKey, crop

            if "labels" in crop.keys():
                labels = crop["labels"]
                #print "******** labels",labels
                for time in labels.keys():
                    #print "******** time, labels", time, labels[time]
                    for label in labels[time].keys():
                        trackSet = labels[time][label]
                        #print "===================================>",len(trackSet), trackSet
                        track = trackSet.pop() # This REMOVES an element of a set.
                        trackSet.add(track)
                        center = self.features[time]['Default features']['RegionCenter'][label]
                        trackCount = len(trackSet)

                        #print time, label, track, center

                        # is this a FIRST, INTERMEDIATE, LAST, SINGLETON(FIRST_LAST) object of a track (or FALSE_DETECTION)
                        type = self._type(cropKey, time, track) # returns [type, previous_label] if type=="LAST" or "INTERMEDIATE" (else [type])

                        #print type, label
                        if type[0] == "FIRST":
                            #print "LABELS.addFirstLabelS (time, label, cellCount)=", time, label, trackCount
                            structuredLearningTracker.addFirstLabels(time, int(label), float(trackCount))
                        elif type[0] == "LAST":
                            #print "LABELS.addLastLabelS (time, label, cellCount)=", time, label, trackCount
                            structuredLearningTracker.addLastLabels(time, int(label), float(trackCount))
                            #print "LABELS.addARCLabel (startTime, startLabel, endLabel, cellCount)=", time-1, type[1], label, 1
                            structuredLearningTracker.addArcLabel(time-1, int(type[1]), int(label), 1.0)
                        #elif type[0] == "SINGLETON":
                            #print "structuredLearningTracker.addSingletonLabelS <--- NOTHING TO DO"
                            # print "structuredLearningTracker.addSingletonLabelS (time, label, trackCount)=", time, label
                            # structuredLearningTracker.addSingletonLabels(hypothesesGraph, time, label, float(trackCount))
                        elif type[0] == "INTERMEDIATE":
                            #print "LABELS.addIntermediateLabelS (time, label, cellCount)=", time, label, trackCount
                            structuredLearningTracker.addIntermediateLabels(time, int(label), float(trackCount))
                            #print "LABELS.addARCLabel (startTime, startLabel, endLabel, cellCount)=", time-1, type[1], label, 1
                            structuredLearningTracker.addArcLabel(time-1, int(type[1]), int(label), 1.0)



            if "divisions" in crop.keys():
                divisions = crop["divisions"]
                #print "divisions", divisions
                for track in divisions.keys():
                    division = divisions[track]
                    time = int(division[1])

                    parent = int(self.getLabel(cropKey, time, track))
                    #print "DIVISIONS.addDivisionLabel (time, label, cellCount)", time, parent, 1
                    structuredLearningTracker.addDivisionLabel(time, parent, 1.0)
                    #print "DIVISIONS.addAppearanceLabel (time, label, cellCount)", time, parent, 1
                    structuredLearningTracker.addAppearanceLabel(time, parent, 1.0)

                    child0 = int(self.getLabel(cropKey, time+1, division[0][0]))
                    #print "DIVISIONS.addDisppearanceLabel (time, label, cellCount)", time+1, child0, 1
                    structuredLearningTracker.addDisappearanceLabel(time+1, child0, 1.0)
                    #print "DIVISIONS.addAppearanceLabel (time, label, cellCount)", time+1, child0, 1
                    structuredLearningTracker.addAppearanceLabel(time+1, child0, 1.0)
                    #print "LABELS.addARCLabel (startTime, startLabel, endLabel, cellCount)=", time, parent, child0, 1
                    structuredLearningTracker.addArcLabel(time, parent, child0, 1.0)

                    child1 = int(self.getLabel(cropKey, time+1, division[0][1]))
                    #print division[1],"      : ", track, self.getLabel(cropKey, time, track), "--->", division[0][1], self.getLabel(cropKey, time+1, division[0][1])
                    #print "DIVISIONS.addDisppearanceLabel (time, label, cellCount)", time+1, child1, 1
                    structuredLearningTracker.addDisappearanceLabel(time+1, child1, 1.0)
                    #print "DIVISIONS.addAppearanceLabel (time, label, cellCount)", time+1, child1, 1
                    structuredLearningTracker.addAppearanceLabel(time+1, child1, 1.0)
                    #print "LABELS.addARCLabel (startTime, startLabel, endLabel, cellCount)=", time, parent, child1, 1
                    structuredLearningTracker.addArcLabel(time, parent, child1, 1.0)

        forbidden_cost = 0.0
        ep_gap = 0.05
        withTracklets=False
        #detectionWeight=11.0
        #divWeight=12.0
        #transWeight=13.0
        #disappearance_cost = 555.0
        #appearance_cost = 333.0
        withMergerResolution=True
        ndim=2
        transition_parameter = 5.0
        borderAwareWidth = 0.0

        sigmas = pgmlink.VectorOfDouble()
        for i in range(5):
            sigmas.append(0.0)
        uncertaintyParams = pgmlink.UncertaintyParameter(1, pgmlink.DistrId.PerturbAndMAP, sigmas)

        cplex_timeout=float(1e75)
        transitionClassifier = None

        # print float(forbidden_cost),float(ep_gap),withTracklets,detectionWeight,divWeight,transWeight,disappearance_cost, appearance_cost, withMergerResolution,\
        #     ndim,transition_parameter,borderAwareWidth,True, uncertaintyParams,cplex_timeout,transitionClassifier
        #

        # print "building CONS Hypotheses Graph"
        # consHypothesesGraph = consTracker.buildGraph(traxelStore)

        detectionWeight = self._detectionWeight
        divWeight = self._divisionWeight
        transWeight = self._transitionWeight
        disappearance_cost = self._disappearanceWeight
        appearance_cost = self._appearanceWeight

        # print "test iterate through hypothesesGraph NODES (C++ side)"
        #structuredLearningTracker.hypothesesGraphTest(hypothesesGraph)

        #print "EXPORTING CROPS"
        for key in self.mainOperator.Crops.value.keys():
            crop = self.mainOperator.Crops.value[key]
            #print "PYTHON---->",crop
            fieldOfView = pgmlink.FieldOfView(
                float(crop["time"][0]),float(crop["starts"][0]),float(crop["starts"][1]),float(crop["starts"][2]),
                float(crop["time"][1]),float(crop["stops"][0]),float(crop["stops"][1]),float(crop["stops"][2]))

            #print "exporting Crop to C++"
            structuredLearningTracker.exportCrop(fieldOfView)

        #print "Structured Learning"
        structuredLearningTracker.structuredLearning(
            float(forbidden_cost),#0,       # forbidden_cost
            float(ep_gap), # ep_gap
            withTracklets,
            detectionWeight,#10.0, # detection weight
            divWeight,
            transWeight,
            disappearance_cost, # disappearance cost
            appearance_cost, # appearance cost
            withMergerResolution,
            ndim,
            transition_parameter,
            borderAwareWidth,
            True, #with_constraints
            uncertaintyParams,
            cplex_timeout,
            transitionClassifier
        )

        #print "DONE with structured learning:"

        sltWeightNorm = 0
        for i in range(5):
            sltWeightNorm += structuredLearningTracker.weight(i) * structuredLearningTracker.weight(i)
        sltWeightNorm = math.sqrt(sltWeightNorm);

        #for i in range(5):
            #print "tracking weights [",i,"]  = ", structuredLearningTracker.weight(i)

        self._detectionWeight = structuredLearningTracker.weight(0)
        self._divisionWeight = structuredLearningTracker.weight(1)
        self._transitionWeight = structuredLearningTracker.weight(2)
        self._appearanceWeight = structuredLearningTracker.weight(3)
        self._disappearanceWeight = structuredLearningTracker.weight(4)

        
        #print "opengm struct-max-margin: detection weight = ", self._detectionWeight
        #print "opengm struct-max-margin: division weight = ", self._divisionWeight
        #print "opengm struct-max-margin: transition weight = ", self._transitionWeight
        #print "opengm struct-max-margin: appearance weight = ", self._appearanceWeight
        #print "opengm struct-max-margin: disappearance weight = ", self._disappearanceWeight

        self._detectionWeight = math.exp(structuredLearningTracker.weight(0))
        self._divisionWeight = math.exp(structuredLearningTracker.weight(1))
        self._transitionWeight = math.exp(structuredLearningTracker.weight(2))
        self._appearanceWeight = math.exp(structuredLearningTracker.weight(3))
        self._disappearanceWeight = math.exp(structuredLearningTracker.weight(4))

        self._drawer.detWeightBox.setValue(self._detectionWeight);
        self._drawer.divWeightBox.setValue(self._divisionWeight);
        self._drawer.transWeightBox.setValue(self._transitionWeight);
        self._drawer.appearanceBox.setValue(self._appearanceWeight);
        self._drawer.disappearanceBox.setValue(self._disappearanceWeight);

        print "ilastik structured learning tracking"
        print "ilastik structured learning tracking: detection weight = ", self._detectionWeight
        print "ilastik structured learning tracking: division weight = ", self._divisionWeight
        print "ilastik structured learning tracking: transition weight = ", self._transitionWeight
        print "ilastik structured learning tracking: appearance weight = ", self._appearanceWeight
        print "ilastik structured learning tracking: disappearance weight = ", self._disappearanceWeight
        

        # print "______________________________________________________________________STRUCTURED LEARNING TRACKING INFERENCE MODEL"
        # structuredLearningTracker.track(
        #     float(forbidden_cost),#0,       # forbidden_cost
        #     float(ep_gap), # ep_gap
        #     withTracklets,
        #     detectionWeight,#10.0, # detection weight
        #     divWeight,
        #     transWeight,
        #     disappearance_cost, # disappearance cost
        #     appearance_cost, # appearance cost
        #     withMergerResolution,
        #     ndim,
        #     transition_parameter,
        #     borderAwareWidth,
        #     True, #with_constraints
        #     uncertaintyParams,
        #     cplex_timeout,
        #     transitionClassifier
        # )
        # print "______________________________________________________________________CONS TRACKING INFERENCE MODEL"
        # consTracker.track(
        #     float(forbidden_cost),#0,       # forbidden_cost
        #     float(ep_gap), # ep_gap
        #     withTracklets,
        #     detectionWeight,#10.0, # detection weight
        #     divWeight,
        #     transWeight,
        #     disappearance_cost, # disappearance cost
        #     appearance_cost, # appearance cost
        #     withMergerResolution,
        #     ndim,
        #     transition_parameter,
        #     borderAwareWidth,
        #     True, #with_constraints
        #     uncertaintyParams,
        #     cplex_timeout,
        #     transitionClassifier
        # )

    def getLabel(self, cropKey, time, track):
        labels = self.mainOperator.Annotations.value[cropKey]["labels"][time]
        for label in labels.keys():
            if self.mainOperator.Annotations.value[cropKey]["labels"][time][label] == set([track]):
                return label
        return False

    def _type(self, cropKey, time, track):

        type = None
        if track == -1:
            return ["FALSE_DETECTION"]
        elif time == 0:
            type = "FIRST"

        labels = self.mainOperator.Annotations.value[cropKey]["labels"]
        crop = self.mainOperator.Crops.value[cropKey]
        lastTime = -1
        lastLabel = -1
        #scan preceeding time frames for track
        for t in range(crop["time"][0],time):
            for label in labels[t]:
                if track in labels[t][label]:
                    lastTime = t
                    lastLabel = label

        if lastTime == -1:
            type = "FIRST"
        elif lastTime < time-1:
            print "ERROR: Your annotations are not complete. See time frame:", time-1
        elif lastTime == time-1:
            type =  "INTERMEDIATE"
        #else:
        #    print "ERROR: SHOULD NOT GET HERE!"

        firstTime = -1
        #scan following time frames for track
        for t in range(crop["time"][1],time,-1):
            for label in labels[t]:
                if track in labels[t][label]:
                    firstTime = t

        if firstTime == -1:
            if type == "FIRST":
                return ["SINGLETON(FIRST_LAST)"]
            else:
                return ["LAST", lastLabel]
        elif firstTime > time+1:
            print "ERROR: Your annotations are not complete. See time frame:", time+1
        elif firstTime == time+1:
            if type ==  "INTERMEDIATE":
                return ["INTERMEDIATE",lastLabel]
            elif type != None:
                return [type]
            #else:
            #    print "ERROR: SHOULD NOT GET HERE!"
        #else:
        #    print "ERROR: SHOULD NOT GET HERE!"

    def _onTrackButtonPressed( self ):
        if not self.mainOperator.ObjectFeatures.ready():
            self._criticalMessage("You have to compute object features first.")            
            return
        
        def _track():    
            self.applet.busy = True
            self.applet.appletStateUpdateRequested.emit()
            maxDist = self._drawer.maxDistBox.value()
            maxObj = self._drawer.maxObjectsBox.value()        
            divThreshold = self._drawer.divThreshBox.value()
            
            from_t = self._drawer.from_time.value()
            to_t = self._drawer.to_time.value()
            from_x = self._drawer.from_x.value()
            to_x = self._drawer.to_x.value()
            from_y = self._drawer.from_y.value()
            to_y = self._drawer.to_y.value()        
            from_z = self._drawer.from_z.value()
            to_z = self._drawer.to_z.value()        
            from_size = self._drawer.from_size.value()
            to_size = self._drawer.to_size.value()        
            
            self.time_range =  range(from_t, to_t + 1)
            avgSize = [self._drawer.avgSizeBox.value()]

            cplex_timeout = None
            if len(str(self._drawer.timeoutBox.text())):
                cplex_timeout = int(self._drawer.timeoutBox.text())

            withTracklets = self._drawer.trackletsBox.isChecked()
            sizeDependent = self._drawer.sizeDepBox.isChecked()
            hardPrior = self._drawer.hardPriorBox.isChecked()
            classifierPrior = self._drawer.classifierPriorBox.isChecked()
            divWeight = self._drawer.divWeightBox.value()
            transWeight = self._drawer.transWeightBox.value()
            withDivisions = self._drawer.divisionsBox.isChecked()        
            withOpticalCorrection = self._drawer.opticalBox.isChecked()
            withMergerResolution = self._drawer.mergerResolutionBox.isChecked()
            borderAwareWidth = self._drawer.bordWidthBox.value()
            withArmaCoordinates = True
            appearanceCost = self._drawer.appearanceBox.value()
            disappearanceCost = self._drawer.disappearanceBox.value()
    
            ndim=3
            if (to_z - from_z == 0):
                ndim=2
            
            try:
                self.mainOperator.track(
                    time_range = self.time_range,
                    x_range = (from_x, to_x + 1),
                    y_range = (from_y, to_y + 1),
                    z_range = (from_z, to_z + 1),
                    size_range = (from_size, to_size + 1),
                    x_scale = self._drawer.x_scale.value(),
                    y_scale = self._drawer.y_scale.value(),
                    z_scale = self._drawer.z_scale.value(),
                    maxDist=maxDist,         
                    maxObj = maxObj,               
                    divThreshold=divThreshold,
                    avgSize=avgSize,                
                    withTracklets=withTracklets,
                    sizeDependent=sizeDependent,
                    divWeight=divWeight,
                    transWeight=transWeight,
                    withDivisions=withDivisions,
                    withOpticalCorrection=withOpticalCorrection,
                    withClassifierPrior=classifierPrior,
                    ndim=ndim,
                    withMergerResolution=withMergerResolution,
                    borderAwareWidth = borderAwareWidth,
                    withArmaCoordinates = withArmaCoordinates,
                    cplex_timeout = cplex_timeout,
                    appearance_cost = appearanceCost,
                    disappearance_cost = disappearanceCost,
                    graph_building_parameter_changed = True
                    )
            except Exception:           
                ex_type, ex, tb = sys.exc_info()
                traceback.print_tb(tb)            
                self._criticalMessage("Exception(" + str(ex_type) + "): " + str(ex))       
                return                     
        
        def _handle_finished(*args):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            self.applet.progressSignal.emit(100)
            self._drawer.TrackButton.setEnabled(True)
            self._drawer.exportButton.setEnabled(True)
            self._drawer.exportTifButton.setEnabled(True)
            self._setLayerVisible("Objects", False) 
            
        def _handle_failure( exc, exc_info ):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            self.applet.progressSignal.emit(100)
            traceback.print_exception(*exc_info)
            sys.stderr.write("Exception raised during tracking.  See traceback above.\n")
            self._drawer.TrackButton.setEnabled(True)
        
        self.applet.progressSignal.emit(0)
        self.applet.progressSignal.emit(-1)
        req = Request( _track )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()

    def menus(self):
        m = QtGui.QMenu("&Export", self.volumeEditorWidget)
        m.addAction("Export Tracking Information").triggered.connect(self.show_export_dialog)

        return [m]

    def get_raw_shape(self):
        return self.topLevelOperatorView.RawImage.meta.shape

    def get_feature_names(self):
        return self.topLevelOperatorView.ComputedFeatureNames([]).wait()

    def handleEditorRightClick(self, position5d, win_coord):
        debug = ilastik_config.getboolean("ilastik", "debug")

        obj, time = self.get_object(position5d)
        if obj == 0:
            menu = TitledMenu(["Background"])
            if debug:
                menu.addAction("Clear Hilite", IPCFacade().broadcast(Protocol.cmd("clear")))
            menu.exec_(win_coord)
            return

        try:
            color = self.mainOperator.label2color[time][obj]
            tracks = [self.mainOperator.track_id[time][obj]]
            extra = self.mainOperator.extra_track_ids
        except (IndexError, KeyError):
            color = None
            tracks = []
            extra = {}

        if time in extra and obj in extra[time]:
            tracks.extend(extra[time][obj])
        if tracks:
            children, parents = self.mainOperator.track_family(tracks[0])
        else:
            children, parents = None, None

        menu = TitledMenu([
            "Object {} of lineage id {}".format(obj, color),
            "Track ids: " + (", ".join(map(str, set(tracks))) or "None"),
        ])

        if not debug:
            menu.exec_(win_coord)
            return

        if any(IPCFacade().sending):

            obj_sub_menu = menu.addMenu("Hilite Object")
            for mode in Protocol.ValidHiliteModes:
                where = Protocol.simple("and", ilastik_id=obj, time=time)
                cmd = Protocol.cmd(mode, where)
                obj_sub_menu.addAction(mode.capitalize(), IPCFacade().broadcast(cmd))

            sub_menus = [
                ("Tracks", Protocol.simple_in, tracks),
                ("Parents", Protocol.simple_in, parents),
                ("Children", Protocol.simple_in, children)
            ]
            for name, protocol, args in sub_menus:
                if args:
                    sub = menu.addMenu("Hilite {}".format(name))
                    for mode in Protocol.ValidHiliteModes[:-1]:
                        mode = mode.capitalize()
                        where = protocol("track_id*", args)
                        cmd = Protocol.cmd(mode, where)
                        sub.addAction(mode, IPCFacade().broadcast(cmd))
                else:
                    sub = menu.addAction("Hilite {}".format(name))
                    sub.setEnabled(False)

            menu.addAction("Clear Hilite", IPCFacade().broadcast(Protocol.cmd("clear")))
        else:
            menu.addAction("Open IPC Server Window", IPCFacade().show_info)
            menu.addAction("Start IPC Server", IPCFacade().start)

        menu.exec_(win_coord)
