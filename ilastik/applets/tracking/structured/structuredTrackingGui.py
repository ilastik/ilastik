from PyQt5 import uic, QtWidgets, QtCore

import os
import logging
import sys
import re
import traceback
import math
import random

import pgmlink

from ilastik.applets.base.applet import DatasetConstraintError
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
        param = self.topLevelOperatorView.Parameters.value
        if 'withMergerResolution' in param.keys():
            if param['withMergerResolution']:
                selection = 1
        elif self._drawer.mergerResolutionBox.isChecked():
            selection = 1

        for i in range(2,len(labels)+1):
            if i <= selection:
                labels[i-1].setVisible(True)
            else:
                labels[i-1].setVisible(False)

        # hide merger legend if selection < 2
        self._drawer.label_4.setVisible(selection > 1)
        labels[0].setVisible(selection > 1)

    def __init__(self, parentApplet, topLevelOperatorView):
        """
        """
        self._initColors()

        self.topLevelOperatorView = topLevelOperatorView
        super(TrackingBaseGui, self).__init__(parentApplet, topLevelOperatorView)
        self.mainOperator = topLevelOperatorView
        if self.mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = self.mainOperator.LabelImage.meta.shape

        self.applet = self.mainOperator.parent.parent.trackingApplet
        self._drawer.mergerResolutionBox.setChecked(True)
        self.connect( self, QtCore.SIGNAL('postInformationMessage(QString)'), self.postInformationMessage)

    def _loadUiFile(self):
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
        self._maxNearestNeighbors = 1

        super(StructuredTrackingGui, self).initAppletDrawerUi()

        self.realOperator = self.topLevelOperatorView.Labels.getRealOperator()
        for i, op in enumerate(self.realOperator.innerOperators):
            self.operator = op

        self._allowedTimeoutInputRegEx = re.compile('^[0-9]*$')
        self._drawer.timeoutBox.textChanged.connect(self._onTimeoutBoxChanged)

        if not ilastik_config.getboolean("ilastik", "debug"):
            def checkboxAssertHandler(checkbox, assertEnabled=True):
                if checkbox.isChecked() == assertEnabled:
                    checkbox.hide()
                else:
                    checkbox.setEnabled(False)

            checkboxAssertHandler(self._drawer.trackletsBox, True)

            if self._drawer.classifierPriorBox.isChecked():
                self._drawer.hardPriorBox.hide()
                self._drawer.classifierPriorBox.hide()
                self._drawer.sizeDepBox.hide()
            else:
                self._drawer.hardPriorBox.setEnabled(False)
                self._drawer.classifierPriorBox.setEnabled(False)
                self._drawer.sizeDepBox.setEnabled(False)

            checkboxAssertHandler(self._drawer.opticalBox, False)
            checkboxAssertHandler(self._drawer.mergerResolutionBox, True)

            self._drawer.maxDistBox.hide()
            self._drawer.label_2.hide()
            self._drawer.label_5.hide()
            self._drawer.divThreshBox.hide()
            self._drawer.label_25.hide()
            self._drawer.avgSizeBox.hide()
          
        self.mergerLabels = [
            self._drawer.merg1,
            self._drawer.merg2,
            self._drawer.merg3,
            self._drawer.merg4,
            self._drawer.merg5,
            self._drawer.merg6,
            self._drawer.merg7]

        for i in range(len(self.mergerLabels)):
            self._labelSetStyleSheet(self.mergerLabels[i], self.mergerColors[i+1])
        
        self._drawer.maxObjectsBox.valueChanged.connect(self._onMaxObjectsBoxChanged)
        self._drawer.mergerResolutionBox.stateChanged.connect(self._onMaxObjectsBoxChanged)

        self._drawer.StructuredLearningButton.clicked.connect(self._onRunStructuredLearningButtonPressed)
        self.features = self.topLevelOperatorView.ObjectFeatures(range(0,self.topLevelOperatorView.LabelImage.meta.shape[0])).wait()

        self._drawer.divWeightBox.valueChanged.connect(self._onDivisionWeightBoxChanged)                
        self._drawer.detWeightBox.valueChanged.connect(self._onDetectionWeightBoxChanged)                
        self._drawer.transWeightBox.valueChanged.connect(self._onTransitionWeightBoxChanged)                
        self._drawer.appearanceBox.valueChanged.connect(self._onAppearanceWeightBoxChanged)                
        self._drawer.disappearanceBox.valueChanged.connect(self._onDisappearanceWeightBoxChanged)                
        self._drawer.maxNearestNeighborsSpinBox.valueChanged.connect(self._onMaxNearestNeighborsSpinBoxChanged)

        self._drawer.OnesButton.clicked.connect(self._onOnesButtonPressed)
        self._drawer.ZerosButton.clicked.connect(self._onZerosButtonPressed)
        self._drawer.RandomButton.clicked.connect(self._onRandomButtonPressed)

        self._divisionWeight = self.topLevelOperatorView.DivisionWeight.value
        self._detectionWeight = self.topLevelOperatorView.DetectionWeight.value
        self._transitionWeight = self.topLevelOperatorView.TransitionWeight.value
        self._appearanceWeight = self.topLevelOperatorView.AppearanceWeight.value
        self._disappearanceWeight = self.topLevelOperatorView.DisappearanceWeight.value

        self._drawer.detWeightBox.setValue(self._detectionWeight)
        self._drawer.divWeightBox.setValue(self._divisionWeight)
        self._drawer.transWeightBox.setValue(self._transitionWeight)
        self._drawer.appearanceBox.setValue(self._appearanceWeight)
        self._drawer.disappearanceBox.setValue(self._disappearanceWeight)

        self._maxNumObj = self.topLevelOperatorView.MaxNumObj.value
        self._drawer.maxObjectsBox.setValue(self.topLevelOperatorView.MaxNumObj.value)
        self._onMaxObjectsBoxChanged()
        self._drawer.maxObjectsBox.setReadOnly(True)

        self.topLevelOperatorView.Labels.notifyReady( bind(self._updateLabelsFromOperator) )
        self.topLevelOperatorView.Divisions.notifyReady( bind(self._updateDivisionsFromOperator) )
        self.topLevelOperatorView.Crops.notifyReady( bind(self._updateCropsFromOperator) )

        self.operator.labels = self.operator.Labels.value
        self.initializeAnnotations()

        self._drawer.trainingToHardConstraints.setChecked(False)
        self._drawer.trainingToHardConstraints.setVisible(False) # will be used when we can handle sparse annotations
        self._drawer.exportButton.setVisible(True)
        self._drawer.exportTifButton.setVisible(False)

        self.topLevelOperatorView._detectionWeight = self._detectionWeight
        self.topLevelOperatorView._divisionWeight = self._divisionWeight
        self.topLevelOperatorView._transitionWeight = self._transitionWeight
        self.topLevelOperatorView._appearanceWeight = self._appearanceWeight
        self.topLevelOperatorView._disappearanceWeight = self._disappearanceWeight


    def _onOnesButtonPressed(self):
        val = math.sqrt(1.0/5)
        self.topLevelOperatorView.DivisionWeight.setValue(val)
        self.topLevelOperatorView.DetectionWeight.setValue(val)
        self.topLevelOperatorView.TransitionWeight.setValue(val)
        self.topLevelOperatorView.AppearanceWeight.setValue(val)
        self.topLevelOperatorView.DisappearanceWeight.setValue(val)

        self._divisionWeight = self.topLevelOperatorView.DivisionWeight.value
        self._detectionWeight = self.topLevelOperatorView.DetectionWeight.value
        self._transitionWeight = self.topLevelOperatorView.TransitionWeight.value
        self._appearanceWeight = self.topLevelOperatorView.AppearanceWeight.value
        self._disappearanceWeight = self.topLevelOperatorView.DisappearanceWeight.value

        self._drawer.detWeightBox.setValue(self._detectionWeight)
        self._drawer.divWeightBox.setValue(self._divisionWeight)
        self._drawer.transWeightBox.setValue(self._transitionWeight)
        self._drawer.appearanceBox.setValue(self._appearanceWeight)
        self._drawer.disappearanceBox.setValue(self._disappearanceWeight)

    def _onRandomButtonPressed(self):
        weights = []
        for i in range(5):
            weights.append(random.random())
        sltWeightNorm = 0
        for i in range(5):
           sltWeightNorm += weights[i] * weights[i]
        sltWeightNorm = math.sqrt(sltWeightNorm)
        self.topLevelOperatorView.DivisionWeight.setValue(weights[0]/sltWeightNorm)
        self.topLevelOperatorView.DetectionWeight.setValue(weights[1]/sltWeightNorm)
        self.topLevelOperatorView.TransitionWeight.setValue(weights[2]/sltWeightNorm)
        self.topLevelOperatorView.AppearanceWeight.setValue(weights[3]/sltWeightNorm)
        self.topLevelOperatorView.DisappearanceWeight.setValue(weights[4]/sltWeightNorm)

        self._divisionWeight = self.topLevelOperatorView.DivisionWeight.value
        self._detectionWeight = self.topLevelOperatorView.DetectionWeight.value
        self._transitionWeight = self.topLevelOperatorView.TransitionWeight.value
        self._appearanceWeight = self.topLevelOperatorView.AppearanceWeight.value
        self._disappearanceWeight = self.topLevelOperatorView.DisappearanceWeight.value

        self._drawer.detWeightBox.setValue(self._detectionWeight)
        self._drawer.divWeightBox.setValue(self._divisionWeight)
        self._drawer.transWeightBox.setValue(self._transitionWeight)
        self._drawer.appearanceBox.setValue(self._appearanceWeight)
        self._drawer.disappearanceBox.setValue(self._disappearanceWeight)

    def _onZerosButtonPressed(self):
        self.topLevelOperatorView.DivisionWeight.setValue(0)
        self.topLevelOperatorView.DetectionWeight.setValue(0)
        self.topLevelOperatorView.TransitionWeight.setValue(0)
        self.topLevelOperatorView.AppearanceWeight.setValue(0)
        self.topLevelOperatorView.DisappearanceWeight.setValue(0)

        self._divisionWeight = self.topLevelOperatorView.DivisionWeight.value
        self._detectionWeight = self.topLevelOperatorView.DetectionWeight.value
        self._transitionWeight = self.topLevelOperatorView.TransitionWeight.value
        self._appearanceWeight = self.topLevelOperatorView.AppearanceWeight.value
        self._disappearanceWeight = self.topLevelOperatorView.DisappearanceWeight.value

        self._drawer.detWeightBox.setValue(self._detectionWeight)
        self._drawer.divWeightBox.setValue(self._divisionWeight)
        self._drawer.transWeightBox.setValue(self._transitionWeight)
        self._drawer.appearanceBox.setValue(self._appearanceWeight)
        self._drawer.disappearanceBox.setValue(self._disappearanceWeight)

    @threadRouted
    def _onTimeoutBoxChanged(self, *args):
        inString = str(self._drawer.timeoutBox.text())
        if self._allowedTimeoutInputRegEx.match(inString) is None:
            self._drawer.timeoutBox.setText(inString.decode("utf8").encode("ascii", "replace")[:-1])

    def _onMaxNumObjChanged(self):
        self._maxNumObj = self.topLevelOperatorView.MaxNumObj.value
        self._setMergerLegend(self.mergerLabels, self._maxNumObj)
        self._drawer.maxObjectsBox.setValue(self._maxNumObj)

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

    @threadRouted
    def _onMaxNearestNeighborsSpinBoxChanged(self, *args):
        self._maxNearestNeighbors = self._drawer.maxNearestNeighborsSpinBox.value()

    def _setRanges(self, *args):
        super(StructuredTrackingGui, self)._setRanges()
        maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
        maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
        maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1
        
        maxBorder = min(maxx, maxy)
        if maxz != 0:
            maxBorder = min(maxBorder, maxz)
        self._drawer.bordWidthBox.setRange(0, maxBorder/2)
        
    def _onMaxObjectsBoxChanged(self):
        self._setMergerLegend(self.mergerLabels, self._drawer.maxObjectsBox.value())
        self._maxNumObj = self._drawer.maxObjectsBox.value()
        self.topLevelOperatorView.MaxNumObjOut.setValue(self._maxNumObj)

    @threadRouted
    def _updateLabelsFromOperator(self):
        self.operator.labels = self.topLevelOperatorView.Labels.wait()

    @threadRouted
    def _updateDivisionsFromOperator(self):
        self.operator.divisions = self.topLevelOperatorView.Divisions.wait()

    @threadRouted
    def _updateCropsFromOperator(self):
        self._crops = self.topLevelOperatorView.Crops.wait()

    def initializeAnnotations(self):

        self._crops = self.topLevelOperatorView.Crops.value

    def getLabel(self, time, track):
        for label in self.operator.labels[time].keys():
            if self.operator.labels[time][label] == set([track]):
                return label
        return False

    def _onRunStructuredLearningButtonPressed(self):
        if self.topLevelOperatorView.Annotations.value == {}:
            self._criticalMessage("Error: Weights can not be calculated because there are no training annotations. " +\
                                  "Go back to Training applet and Save your training for each crop.")
            return

        self.initializeAnnotations()
        median_obj_size = [0]

        from_z = self._drawer.from_z.value()
        to_z = self._drawer.to_z.value()
        ndim=3
        if (to_z - from_z == 0):
            ndim=2

        maxObj=self._maxNumObj

        fieldOfView = pgmlink.FieldOfView(
            float(0),
            float(0),
            float(0),
            float(0),
            float(self.topLevelOperatorView.LabelImage.meta.shape[0]),
            float(self.topLevelOperatorView.LabelImage.meta.shape[1]),
            float(self.topLevelOperatorView.LabelImage.meta.shape[2]),
            float(self.topLevelOperatorView.LabelImage.meta.shape[3]))

        foundAllArcs = False;
        new_max_nearest_neighbors = self._maxNearestNeighbors-1
        maxObjOK = True
        while not foundAllArcs and maxObjOK:
            new_max_nearest_neighbors += 1
            withDivisions = self._drawer.divisionsBox.isChecked()
            consTracker = pgmlink.ConsTracking(
                maxObj, # max_number_objects
                True, # size_dependent_detection_prob
                float(median_obj_size[0]), # avg_obj_size
                float(200), # max_neighbor_distance
                withDivisions, # with_divisions
                float(0.5), # division_threshold
                "none", # random_forest_filename
                fieldOfView,
                "none", # event_vector_dump_filename
                pgmlink.ConsTrackingSolverType.CplexSolver,
                ndim)

            time_range = range (0,self.topLevelOperatorView.LabelImage.meta.shape[0])
            featureStore, traxelStore, empty_frame, max_traxel_id_at = self.mainOperator._generate_traxelstore(
                time_range,
                (0,self.topLevelOperatorView.LabelImage.meta.shape[1]),#x_range
                (0,self.topLevelOperatorView.LabelImage.meta.shape[2]),#y_range
                (0,self.topLevelOperatorView.LabelImage.meta.shape[3]),#z_range,
                (0, 100000),#size_range
                1.0,# x_scale
                1.0,# y_scale
                1.0,# z_scale,
                median_object_size=median_obj_size,
                with_div=withDivisions,
                with_opt_correction=False,
                with_classifier_prior=True)

            if empty_frame:
                raise DatasetConstraintError('Structured Learning', 'Can not track frames with 0 objects, abort.')
            hypothesesGraph = consTracker.buildGraph(traxelStore, new_max_nearest_neighbors)

            maxDist = 200
            sizeDependent = False
            divThreshold = float(0.5)

            structuredLearningTracker = pgmlink.StructuredLearningTracking(
                hypothesesGraph,
                maxObj,
                sizeDependent,
                float(median_obj_size[0]),
                maxDist,
                withDivisions,
                divThreshold,
                "none",  # detection_rf_filename
                fieldOfView,
                "none", # dump traxelstore,
                pgmlink.ConsTrackingSolverType.CplexSolver,
                ndim)

            logger.info("Structured Learning: Adding Training Annotations to Hypotheses Graph")

            # could be merged with code in opStructuredTracking
            structuredLearningTracker.addLabels()

            mergeMsgStr = "Your tracking annotations contradict this model assumptions! All tracks must be continuous, tracks of length one are not allowed, and mergers may merge or split but all tracks in a merger appear/disappear together."
            foundAllArcs = True;
            numAllAnnotatedDivisions = 0
            for cropKey in self.mainOperator.Crops.value.keys():
                if foundAllArcs:

                    if not cropKey in self.mainOperator.Annotations.value.keys():
                        self._criticalMessage("You have not trained or saved your training for " + str(cropKey) + \
                                              ". \nGo back to the Training applet and save all your training!")
                        return

                    crop = self.mainOperator.Annotations.value[cropKey]

                    if "labels" in crop.keys():

                        labels = crop["labels"]

                        for time in labels.keys():

                            if not foundAllArcs:
                                break

                            for label in labels[time].keys():

                                if not foundAllArcs:
                                    break

                                trackSet = labels[time][label]
                                center = self.features[time]['Default features']['RegionCenter'][label]
                                trackCount = len(trackSet)

                                if trackCount > maxObj:
                                    logger.info("Your track count for object {} in time frame {} is {} =| {} |, which is greater than maximum object number {} defined by object count classifier!".format(label,time,trackCount,trackSet,maxObj))
                                    logger.info("Either remove track(s) from this object or train the object count classifier with more labels!")
                                    maxObjOK = False
                                    raise DatasetConstraintError('Structured Learning', "Your track count for object "+str(label)+" in time frame " +str(time)+ " equals "+str(trackCount)+"=|"+str(trackSet)+"|," + \
                                            " which is greater than the maximum object number "+str(maxObj)+" defined by object count classifier! " + \
                                            "Either remove track(s) from this object or train the object count classifier with more labels!")

                                for track in trackSet:

                                    if not foundAllArcs:
                                        logger.info("[structuredTrackingGui] Increasing max nearest neighbors!")
                                        break

                                    # is this a FIRST, INTERMEDIATE, LAST, SINGLETON(FIRST_LAST) object of a track (or FALSE_DETECTION)
                                    type = self._type(cropKey, time, track) # returns [type, previous_label] if type=="LAST" or "INTERMEDIATE" (else [type])
                                    if type == None:
                                        raise DatasetConstraintError('Structured Learning', mergeMsgStr)

                                    elif type[0] == "LAST" or type[0] == "INTERMEDIATE":
                                        previous_label = int(type[1])
                                        previousTrackSet = labels[time-1][previous_label]
                                        intersectionSet = trackSet.intersection(previousTrackSet)
                                        trackCountIntersection = len(intersectionSet)

                                        if trackCountIntersection > maxObj:
                                            logger.info("Your track count for transition ( {},{} ) ---> ( {},{} ) is {} =| {} |, which is greater than maximum object number {} defined by object count classifier!".format(previous_label,time-1,label,time,trackCountIntersection,intersectionSet,maxObj))
                                            logger.info("Either remove track(s) from these objects or train the object count classifier with more labels!")
                                            maxObjOK = False
                                            raise DatasetConstraintError('Structured Learning', "Your track count for transition ("+str(previous_label)+","+str(time-1)+") ---> ("+str(label)+","+str(time)+") is "+str(trackCountIntersection)+"=|"+str(intersectionSet)+"|, " + \
                                                    "which is greater than maximum object number "+str(maxObj)+" defined by object count classifier!" + \
                                                    "Either remove track(s) from these objects or train the object count classifier with more labels!")


                                        foundAllArcs &= structuredLearningTracker.addArcLabel(time-1, int(previous_label), int(label), float(trackCountIntersection))
                                        if not foundAllArcs:
                                            logger.info("[structuredTrackingGui] Increasing max nearest neighbors!")
                                            break

                                if type == None:
                                    raise DatasetConstraintError('Structured Learning', mergeMsgStr)

                                elif type[0] == "FIRST":
                                    structuredLearningTracker.addFirstLabels(time, int(label), float(trackCount))
                                    if time > self.mainOperator.Crops.value[cropKey]["time"][0]:
                                        structuredLearningTracker.addDisappearanceLabel(time, int(label), 0.0)

                                elif type[0] == "LAST":
                                    structuredLearningTracker.addLastLabels(time, int(label), float(trackCount))
                                    if time < self.mainOperator.Crops.value[cropKey]["time"][1]:
                                        structuredLearningTracker.addAppearanceLabel(time, int(label), 0.0)

                                elif type[0] == "INTERMEDIATE":
                                    structuredLearningTracker.addIntermediateLabels(time, int(label), float(trackCount))

                    if foundAllArcs and "divisions" in crop.keys():
                        divisions = crop["divisions"]

                        numAllAnnotatedDivisions = numAllAnnotatedDivisions + len(divisions)
                        for track in divisions.keys():
                            if not foundAllArcs:
                                break

                            division = divisions[track]
                            time = int(division[1])

                            parent = int(self.getLabelInCrop(cropKey, time, track))

                            if parent >=0:
                                structuredLearningTracker.addDivisionLabel(time, parent, 1.0)
                                structuredLearningTracker.addAppearanceLabel(time, parent, 1.0)
                                structuredLearningTracker.addDisappearanceLabel(time, parent, 1.0)

                                child0 = int(self.getLabelInCrop(cropKey, time+1, division[0][0]))
                                structuredLearningTracker.addDisappearanceLabel(time+1, child0, 1.0)
                                structuredLearningTracker.addAppearanceLabel(time+1, child0, 1.0)
                                foundAllArcs &= structuredLearningTracker.addArcLabel(time, parent, child0, 1.0)
                                if not foundAllArcs:
                                    logger.info("[structuredTrackingGui] Increasing max nearest neighbors!")
                                    break

                                child1 = int(self.getLabelInCrop(cropKey, time+1, division[0][1]))
                                structuredLearningTracker.addDisappearanceLabel(time+1, child1, 1.0)
                                structuredLearningTracker.addAppearanceLabel(time+1, child1, 1.0)
                                foundAllArcs &= structuredLearningTracker.addArcLabel(time, parent, child1, 1.0)
                                if not foundAllArcs:
                                    logger.info("[structuredTrackingGui] Increasing max nearest neighbors!")
                                    break
        logger.info("max nearest neighbors=".format(new_max_nearest_neighbors))

        if new_max_nearest_neighbors > self._maxNearestNeighbors:
            self._maxNearestNeighbors = new_max_nearest_neighbors
            self._drawer.maxNearestNeighborsSpinBox.setValue(self._maxNearestNeighbors)

        forbidden_cost = 0.0
        ep_gap = 0.005
        withTracklets=False
        withMergerResolution=True
        transition_parameter = 5.0
        borderAwareWidth = self._drawer.bordWidthBox.value()
        sigmas = pgmlink.VectorOfDouble()
        for i in range(5):
            sigmas.append(0.0)
        uncertaintyParams = pgmlink.UncertaintyParameter(1, pgmlink.DistrId.PerturbAndMAP, sigmas)

        cplex_timeout=float(1000.0)
        transitionClassifier = None

        detectionWeight = self._detectionWeight
        divisionWeight = self._divisionWeight
        transitionWeight = self._transitionWeight
        disappearanceWeight = self._disappearanceWeight
        appearanceWeight = self._appearanceWeight

        for key in self._crops.keys():
            crop = self._crops[key]
            fieldOfView = pgmlink.FieldOfView(
                float(crop["time"][0]),float(crop["starts"][0]),float(crop["starts"][1]),float(crop["starts"][2]),
                float(crop["time"][1]),float(crop["stops"][0]),float(crop["stops"][1]),float(crop["stops"][2]))

            structuredLearningTracker.exportCrop(fieldOfView)

        with_constraints = True
        training_to_hard_constraints = False
        num_threads = 8
        withNormalization = True
        withClassifierPrior = self._drawer.classifierPriorBox.isChecked()
        verbose = False
        withNonNegativeWeights = False
        structuredLearningTrackerParameters = structuredLearningTracker.getStructuredLearningTrackingParameters(
            float(forbidden_cost),
            float(ep_gap),
            withTracklets,
            detectionWeight,
            divisionWeight,
            transitionWeight,
            disappearanceWeight,
            appearanceWeight,
            withMergerResolution,
            ndim,
            transition_parameter,
            borderAwareWidth,
            with_constraints,
            uncertaintyParams,
            cplex_timeout,
            transitionClassifier,
            pgmlink.ConsTrackingSolverType.CplexSolver,
            training_to_hard_constraints,
            num_threads,
            withNormalization,
            withClassifierPrior,
            verbose,
            withNonNegativeWeights
        )

        # will be needed for python defined TRANSITION function
        #structuredLearningTrackerParameters.register_transition_func(self.mainOperator.track_transition_func_no_weight)
        structuredLearningTracker.structuredLearning(structuredLearningTrackerParameters)
        if withDivisions and numAllAnnotatedDivisions == 0 and not structuredLearningTracker.weight(1) == 0.0:
            self._informationMessage ("Divisible objects are checked, but you did not annotate any divisions in your tracking training. " + \
                                 "The resulting division weight might be arbitrarily high and if there are divisions present in the dataset, " +\
                                 "they might not be present in the tracking solution.")

        norm = 0
        for i in range(5):
            norm += structuredLearningTracker.weight(i)*structuredLearningTracker.weight(i)
        norm = math.sqrt(norm)

        if norm > 0.0000001:
            self._detectionWeight = structuredLearningTracker.weight(0)/norm
            self._divisionWeight = structuredLearningTracker.weight(1)/norm
            self._transitionWeight = structuredLearningTracker.weight(2)/norm
            self._appearanceWeight = structuredLearningTracker.weight(3)/norm
            self._disappearanceWeight = structuredLearningTracker.weight(4)/norm

        self._drawer.detWeightBox.setValue(self._detectionWeight);
        self._drawer.divWeightBox.setValue(self._divisionWeight);
        self._drawer.transWeightBox.setValue(self._transitionWeight);
        self._drawer.appearanceBox.setValue(self._appearanceWeight);
        self._drawer.disappearanceBox.setValue(self._disappearanceWeight);

        epsZero = 0.01
        if self._detectionWeight < 0.0:
            self._informationMessage ("Detection weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                "Furthermore, you should add more training and recalculate the learning weights in order to improve your tracking solution.")
            #self._detectionWeight = epsZero
        elif self._divisionWeight < 0.0:
            self._informationMessage ("Division weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                "Furthermore, you should add more division cells to your training and recalculate the learning weights in order to improve your tracking solution.")
            #self._divisionWeight = epsZero
        elif self._transitionWeight < 0.0:
            self._informationMessage ("Transition weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                "Furthermore, you should add more transitions to your training and recalculate the learning weights in order to improve your tracking solution.")
            #self._transitionWeight = epsZero
        elif self._appearanceWeight < 0.0:
            self._informationMessage ("Appearance weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                "Furthermore, you should add more appearances to your training and recalculate the learning weights in order to improve your tracking solution.")
            #self._appearanceWeight = epsZero
        elif self._disappearanceWeight < 0.0:
            self._informationMessage ("Disappearance weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                "Furthermore, you should add more disappearances to your training and recalculate the learning weights in order to improve your tracking solution.")
            #self._disappearanceWeight = epsZero

        if self._detectionWeight < 0.0 or self._divisionWeight < 0.0 or self._transitionWeight < 0.0 or self._appearanceWeight < 0.0 or self._disappearanceWeight < 0.0:
            structuredLearningTrackerParameters.setWithNonNegativeWeights(True)
            structuredLearningTracker.structuredLearning(structuredLearningTrackerParameters)
            norm = 0
            for i in range(5):
                norm += structuredLearningTracker.weight(i)*structuredLearningTracker.weight(i)
            norm = math.sqrt(norm)

            if norm > 0.0000001:
                self._detectionWeight = structuredLearningTracker.weight(0)/norm
                self._divisionWeight = structuredLearningTracker.weight(1)/norm
                self._transitionWeight = structuredLearningTracker.weight(2)/norm
                self._appearanceWeight = structuredLearningTracker.weight(3)/norm
                self._disappearanceWeight = structuredLearningTracker.weight(4)/norm

            self._drawer.detWeightBox.setValue(self._detectionWeight);
            self._drawer.divWeightBox.setValue(self._divisionWeight);
            self._drawer.transWeightBox.setValue(self._transitionWeight);
            self._drawer.appearanceBox.setValue(self._appearanceWeight);
            self._drawer.disappearanceBox.setValue(self._disappearanceWeight);


        self.mainOperator.detectionWeight = self._detectionWeight
        self.mainOperator.divisionWeight = self._divisionWeight
        self.mainOperator.transitionWeight = self._transitionWeight
        self.mainOperator.appearanceWeight = self._appearanceWeight
        self.mainOperator.disappearanceWeight = self._disappearanceWeight

        self._drawer.detWeightBox.setValue(self._detectionWeight);
        self._drawer.divWeightBox.setValue(self._divisionWeight);
        self._drawer.transWeightBox.setValue(self._transitionWeight);
        self._drawer.appearanceBox.setValue(self._appearanceWeight);
        self._drawer.disappearanceBox.setValue(self._disappearanceWeight);

        logger.info("Structured Learning Tracking Weights (normalized):")
        logger.info("   detection weight     = {}".format(self._detectionWeight))
        logger.info("   detection weight     = {}".format(self._divisionWeight))
        logger.info("   detection weight     = {}".format(self._transitionWeight))
        logger.info("   detection weight     = {}".format(self._appearanceWeight))
        logger.info("   detection weight     = {}".format(self._disappearanceWeight))

    def getLabelInCrop(self, cropKey, time, track):
        labels = self.mainOperator.Annotations.value[cropKey]["labels"][time]
        for label in labels.keys():
            if self.mainOperator.Annotations.value[cropKey]["labels"][time][label] == set([track]):
                return label
        return -1

    def _type(self, cropKey, time, track):
        # returns [type, previous_label] (if type=="LAST" or "INTERMEDIATE" else [type])
        type = None
        if track == -1:
            return ["FALSE_DETECTION"]
        elif time == 0:
            type = "FIRST"

        labels = self.mainOperator.Annotations.value[cropKey]["labels"]
        crop = self._crops[cropKey]
        lastTime = -1
        lastLabel = -1
        for t in range(crop["time"][0],time):
            for label in labels[t]:
                if track in labels[t][label]:
                    lastTime = t
                    lastLabel = label
        if lastTime == -1:
            type = "FIRST"
        elif lastTime < time-1:
            logger.info("ERROR: Your annotations are not complete. See time frame {}.".format(time-1))
        elif lastTime == time-1:
            type =  "INTERMEDIATE"

        firstTime = -1
        for t in range(crop["time"][1],time,-1):
            if t in labels.keys():
                for label in labels[t]:
                    if track in labels[t][label]:
                        firstTime = t
        if firstTime == -1:
            if type == "FIRST":
                return ["SINGLETON(FIRST_LAST)"]
            else:
                return ["LAST", lastLabel]
        elif firstTime > time+1:
            logger.info("ERROR: Your annotations are not complete. See time frame {}.".format(time+1))
        elif firstTime == time+1:
            if type ==  "INTERMEDIATE":
                return ["INTERMEDIATE",lastLabel]
            elif type != None:
                return [type]

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

            withTracklets = True
            sizeDependent = self._drawer.sizeDepBox.isChecked()
            hardPrior = self._drawer.hardPriorBox.isChecked()
            classifierPrior = self._drawer.classifierPriorBox.isChecked()
            detWeight = self._drawer.detWeightBox.value()
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
                if True:
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
                        detWeight=detWeight,
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
                        graph_building_parameter_changed = True,
                        trainingToHardConstraints = self._drawer.trainingToHardConstraints.isChecked(),
                        max_nearest_neighbors = self._maxNearestNeighbors
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
        m = QtWidgets.QMenu("&Export", self.volumeEditorWidget)
        m.addAction("Export Tracking Information").triggered.connect(self.show_export_dialog)

        return [m]

    def get_raw_shape(self):
        return self.topLevelOperatorView.RawImage.meta.shape

    def get_feature_names(self):
        return self.topLevelOperatorView.ComputedFeatureNames([]).wait()

    def get_color(self, pos5d):
        slicing = tuple(slice(i, i+1) for i in pos5d)
        color = self.mainOperator.CachedOutput(slicing).wait()
        return color.flat[0]

    def get_object(self, pos5d):
        slicing = tuple(slice(i, i+1) for i in pos5d)
        label = self.mainOperator.RelabeledImage(slicing).wait()
        return label.flat[0], pos5d[0]

    @property
    def gui_applet(self):
        return self.applet

    def get_export_dialog_title(self):
        return "Export Tracking Information"

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
            extra = self.mainOperator.extra_track_ids
        except (IndexError, KeyError):
            extra = {}

        # if this is a resolved merger, find which of the merged IDs we actually clicked on
        if time in extra and obj in extra[time]:
            colors = [self.mainOperator.label2color[time][t] for t in extra[time][obj]]
            tracks = [self.mainOperator.track_id[time][t] for t in extra[time][obj]]
            selected_track = self.get_color(position5d)
            idx = colors.index(selected_track)
            color = colors[idx]
            track = tracks[idx]
        else:
            try:
                color = self.mainOperator.label2color[time][obj]
                track = [self.mainOperator.track_id[time][obj]][0]
            except (IndexError, KeyError):
                color = None
                track = []

        if track:
            children, parents = self.mainOperator.track_family(track)
        else:
            children, parents = None, None

        menu = TitledMenu([
            "Object {} of lineage id {}".format(obj, color),
            "Track id: " + (str(track) or "None"),
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

    def _informationMessage(self, prompt):
        self.emit( QtCore.SIGNAL('postInformationMessage(QString)'), prompt)

    @threadRouted
    def postInformationMessage(self, prompt):
        QtWidgets.QMessageBox.information(self, "Info:", prompt, QtWidgets.QMessageBox.Ok)

