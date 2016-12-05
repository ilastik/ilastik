import numpy as np
import math
from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.rtype import List
from lazyflow.stype import Opaque
import pgmlink
from ilastik.applets.tracking.base.opTrackingBase import OpTrackingBase
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
from ilastik.applets.tracking.base.trackingUtilities import relabel, highlightMergers
from ilastik.applets.tracking.base.trackingUtilities import get_events
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.roi import sliceToRoi
from ilastik.applets.tracking.conservation.opRelabeledMergerFeatureExtraction import OpRelabeledMergerFeatureExtraction
from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.utility import bind
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key

import sys


import logging
logger = logging.getLogger(__name__)


class OpStructuredTrackingPgmlink(OpTrackingBase):
    DivisionProbabilities = InputSlot(stype=Opaque, rtype=List)
    DetectionProbabilities = InputSlot(stype=Opaque, rtype=List)
    NumLabels = InputSlot()
    Crops = InputSlot()
    Labels = InputSlot(stype=Opaque, rtype=List)
    Divisions = InputSlot(stype=Opaque, rtype=List)
    Annotations = InputSlot(stype=Opaque)
    MaxNumObj = InputSlot()

    # compressed cache for merger output
    MergerInputHdf5 = InputSlot(optional=True)
    MergerCleanBlocks = OutputSlot()
    MergerOutputHdf5 = OutputSlot()
    MergerCachedOutput = OutputSlot() # For the GUI (blockwise access)
    MergerOutput = OutputSlot()

    CoordinateMap = OutputSlot()

    RelabeledInputHdf5 = InputSlot(optional=True)
    RelabeledCleanBlocks = OutputSlot()
    RelabeledOutputHdf5 = OutputSlot()
    RelabeledCachedOutput = OutputSlot() # For the GUI (blockwise access)
    RelabeledImage = OutputSlot()

    DivisionWeight = OutputSlot()
    DetectionWeight = OutputSlot()
    TransitionWeight = OutputSlot()
    AppearanceWeight = OutputSlot()
    DisappearanceWeight = OutputSlot()
    MaxNumObjOut = OutputSlot()

    def __init__(self, parent=None, graph=None):

        super(OpStructuredTrackingPgmlink, self).__init__(parent=parent, graph=graph)

        self.labels = {}
        self.divisions = {}
        self.Annotations.setValue({})

        self._mergerOpCache = OpCompressedCache( parent=self )
        self._mergerOpCache.InputHdf5.connect(self.MergerInputHdf5)
        self._mergerOpCache.Input.connect(self.MergerOutput)
        self.MergerCleanBlocks.connect(self._mergerOpCache.CleanBlocks)
        self.MergerOutputHdf5.connect(self._mergerOpCache.OutputHdf5)
        self.MergerCachedOutput.connect(self._mergerOpCache.Output)

        self._relabeledOpCache = OpCompressedCache( parent=self )
        self._relabeledOpCache.InputHdf5.connect(self.RelabeledInputHdf5)
        self._relabeledOpCache.Input.connect(self.RelabeledImage)
        self.RelabeledCleanBlocks.connect(self._relabeledOpCache.CleanBlocks)
        self.RelabeledOutputHdf5.connect(self._relabeledOpCache.OutputHdf5)
        self.RelabeledCachedOutput.connect(self._relabeledOpCache.Output)
        self._ndim = 3

        self.consTracker = None
        self._parent = parent

        self.DivisionWeight.setValue(0.6)
        self.DetectionWeight.setValue(0.6)
        self.TransitionWeight.setValue(0.01)
        self.AppearanceWeight.setValue(0.3)
        self.DisappearanceWeight.setValue(0.2)

        self.MaxNumObjOut.setValue(1)

        self.transition_parameter = 5
        self.detectionWeight = 1
        self.divisionWeight = 1
        self.transitionWeight = 1
        self.appearanceWeight = 1
        self.disappearanceWeight = 1
        self.Crops.notifyReady(bind(self._updateCropsFromOperator) )

    def setupOutputs(self):
        super(OpStructuredTrackingPgmlink, self).setupOutputs()
        self.MergerOutput.meta.assignFrom(self.LabelImage.meta)
        self.RelabeledImage.meta.assignFrom(self.LabelImage.meta)
        self._ndim = 2 if self.LabelImage.meta.shape[3] == 1 else 3

        self._mergerOpCache.BlockShape.setValue( self._blockshape )
        self._relabeledOpCache.BlockShape.setValue( self._blockshape )

        for t in range(self.LabelImage.meta.shape[0]):
            if t not in self.labels.keys():
                self.labels[t]={}

    def execute(self, slot, subindex, roi, result):
        
        if slot is self.Labels:
            result=self.Labels.wait()

        if slot is self.Divisions:
            result=self.Divisions.wait()

        if slot is self.Output:
            parameters = self.Parameters.value
            trange = range(roi.start[0], roi.stop[0])
            original = np.zeros(result.shape, dtype=slot.meta.dtype)
            super(OpStructuredTrackingPgmlink, self).execute(slot, subindex, roi, original)

            result[:] = self.LabelImage.get(roi).wait()
            pixel_offsets=roi.start[1:-1]  # offset only in pixels, not time and channel
            for t in trange:
                if ('time_range' in parameters
                        and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0]
                        and len(self.resolvedto) > t and len(self.resolvedto[t])):
                    result[t-roi.start[0],...,0] = self._relabelMergers(result[t-roi.start[0],...,0], t, pixel_offsets)
                else:
                    result[t-roi.start[0],...][:] = 0

            original[result != 0] = result[result != 0]
            result[:] = original
        elif slot is self.MergerOutput:
            result[:] = self.LabelImage.get(roi).wait()
            parameters = self.Parameters.value
            trange = range(roi.start[0], roi.stop[0])
            pixel_offsets=roi.start[1:-1]  # offset only in pixels, not time and channel
            for t in trange:
                if ('time_range' in parameters
                    and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0]
                    and len(self.mergers) > t and len(self.mergers[t])):
                    if 'withMergerResolution' in parameters.keys() and parameters['withMergerResolution']:
                        result[t-roi.start[0],...,0] = self._relabelMergers(result[t-roi.start[0],...,0], t, pixel_offsets, True)
                    else:
                        result[t-roi.start[0],...,0] = highlightMergers(result[t-roi.start[0],...,0], self.mergers[t])
                else:
                    result[t-roi.start[0],...][:] = 0
        elif slot is self.RelabeledImage:
            parameters = self.Parameters.value
            trange = range(roi.start[0], roi.stop[0])
            result[:] = self.LabelImage.get(roi).wait()
            pixel_offsets=roi.start[1:-1]  # offset only in pixels, not time and channel
            for t in trange:
                if ('time_range' in parameters
                        and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0]
                        and len(self.resolvedto) > t and len(self.resolvedto[t])
                        and 'withMergerResolution' in parameters.keys() and parameters['withMergerResolution']):
                        result[t-roi.start[0],...,0] = self._relabelMergers(result[t-roi.start[0],...,0], t, pixel_offsets, False, True)
        else:  # default bahaviour
            super(OpStructuredTrackingPgmlink, self).execute(slot, subindex, roi, result)

        return result     

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.InputHdf5 or slot == self.MergerInputHdf5, "Invalid slot for setInSlot(): {}".format( slot.name )

    def track(self,
            time_range,
            x_range,
            y_range,
            z_range,
            size_range=(0, 100000),
            x_scale=1.0,
            y_scale=1.0,
            z_scale=1.0,
            maxDist=30,     
            maxObj=2,       
            divThreshold=0.5,
            avgSize=[0],                        
            withTracklets=False,
            sizeDependent=True,
            detWeight=10.0,
            divWeight=10.0,
            transWeight=10.0,
            withDivisions=True,
            withOpticalCorrection=True,
            withClassifierPrior=False,
            ndim=3,
            cplex_timeout=None,
            withMergerResolution=True,
            borderAwareWidth = 0.0,
            withArmaCoordinates = True,
            appearance_cost = 500,
            disappearance_cost = 500,
            graph_building_parameter_changed = True,
            trainingToHardConstraints = False,
            max_nearest_neighbors = 1,
            force_build_hypotheses_graph = False,
            withBatchProcessing = False,
            solverName = 'ILP'
            ):
        
        if not self.Parameters.ready():
            raise Exception("Parameter slot is not ready")
        
        # it is assumed that the self.Parameters object is changed only at this
        # place (ugly assumption). Therefore we can track any changes in the
        # parameters as done in the following lines: If the same value for the
        # key is already written in the parameters dictionary, the
        # paramters_changed dictionary will get a "False" entry for this key,
        # otherwise it is set to "True"
        parameters = self.Parameters.value

        parameters['maxDist'] = maxDist
        parameters['maxObj'] = maxObj
        parameters['divThreshold'] = divThreshold
        parameters['avgSize'] = avgSize
        parameters['withTracklets'] = withTracklets
        parameters['sizeDependent'] = sizeDependent
        parameters['detWeight'] = detWeight
        parameters['divWeight'] = divWeight
        parameters['transWeight'] = transWeight
        parameters['withDivisions'] = withDivisions
        parameters['withOpticalCorrection'] = withOpticalCorrection
        parameters['withClassifierPrior'] = withClassifierPrior
        parameters['withMergerResolution'] = withMergerResolution
        parameters['borderAwareWidth'] = borderAwareWidth
        parameters['withArmaCoordinates'] = withArmaCoordinates
        parameters['appearanceCost'] = appearance_cost
        parameters['disappearanceCost'] = disappearance_cost
                
        do_build_hypotheses_graph = True

        if cplex_timeout:
            parameters['cplex_timeout'] = cplex_timeout
        else:
            parameters['cplex_timeout'] = ''
            cplex_timeout = float(1e75)
        
        if withClassifierPrior:
            if not self.DetectionProbabilities.ready() or len(self.DetectionProbabilities([0]).wait()[0]) == 0:
                raise DatasetConstraintError('Tracking', 'Classifier not ready yet. Did you forget to train the Object Count Classifier?')
            if not self.NumLabels.ready() or self.NumLabels.value != (maxObj + 1):
                raise DatasetConstraintError('Tracking', 'The max. number of objects must be consistent with the number of labels given in Object Count Classification.\n'+\
                    'Check whether you have (i) the correct number of label names specified in Object Count Classification, and (ii) provided at least' +\
                    'one training example for each class.')
            if len(self.DetectionProbabilities([0]).wait()[0][0]) != (maxObj + 1):
                raise DatasetConstraintError('Tracking', 'The max. number of objects must be consistent with the number of labels given in Object Count Classification.\n'+\
                    'Check whether you have (i) the correct number of label names specified in Object Count Classification, and (ii) provided at least' +\
                    'one training example for each class.')
        
        median_obj_size = [0]

        fs, ts, empty_frame, max_traxel_id_at = self._generate_traxelstore(
            time_range, x_range, y_range, z_range,
            size_range, x_scale, y_scale, z_scale,
            median_object_size=median_obj_size,
            with_div=withDivisions,
            with_opt_correction=withOpticalCorrection,
            with_classifier_prior=withClassifierPrior)
        
        if empty_frame:
            raise DatasetConstraintError('Tracking', 'Can not track frames with 0 objects, abort.')
              
        
        if avgSize[0] > 0:
            median_obj_size = avgSize
        
        logger.info( 'median_obj_size = {}'.format( median_obj_size ) )

        ep_gap = 0.05

        fov = pgmlink.FieldOfView(time_range[0] * 1.0,
                                      x_range[0] * x_scale,
                                      y_range[0] * y_scale,
                                      z_range[0] * z_scale,
                                      time_range[-1] * 1.0,
                                      (x_range[1]-1) * x_scale,
                                      (y_range[1]-1) * y_scale,
                                      (z_range[1]-1) * z_scale,)
        
        logger.info( 'fov = {},{},{},{},{},{},{},{}'.format( time_range[0] * 1.0,
                                      x_range[0] * x_scale,
                                      y_range[0] * y_scale,
                                      z_range[0] * z_scale,
                                      time_range[-1] * 1.0,
                                      (x_range[1]-1) * x_scale,
                                      (y_range[1]-1) * y_scale,
                                      (z_range[1]-1) * z_scale, ) )
        
        if ndim == 2:
            assert z_range[0] * z_scale == 0 and (z_range[1]-1) * z_scale == 0, "fov of z must be (0,0) if ndim==2"

        solverType = self.getPgmlinkSolverType(solverName)

        if(self.consTracker == None or graph_building_parameter_changed):# or do_build_hypotheses_graph):

            foundAllArcs = False;
            new_max_nearest_neighbors = max_nearest_neighbors-1

            while not foundAllArcs:
                new_max_nearest_neighbors += 1
                logger.info( '\033[94m' +"make new graph"+  '\033[0m' )

                self.consTracker = pgmlink.ConsTracking(
                    int(maxObj),
                    bool(sizeDependent),   # size_dependent_detection_prob
                    float(median_obj_size[0]), # median_object_size
                    float(maxDist),
                    bool(withDivisions),
                    float(divThreshold),
                    "none",  # detection_rf_filename
                    fov,
                    "none", # dump traxelstore,
                    solverType,
                    ndim)
                hypothesesGraph = self.consTracker.buildGraph(ts, new_max_nearest_neighbors)


                self.features = self.ObjectFeatures(range(0,self.LabelImage.meta.shape[0])).wait()

                foundAllArcs = True;
                if trainingToHardConstraints:

                    logger.info("Tracking: Adding Training Annotations to Hypotheses Graph")

                    # could be merged with code in structuredTrackingGui
                    self.consTracker.addLabels()

                    for cropKey in self.Annotations.value.keys():
                        if foundAllArcs:
                            crop = self.Annotations.value[cropKey]

                            if "labels" in crop.keys():
                                labels = crop["labels"]
                                for time in labels.keys():

                                    if not foundAllArcs:
                                        break

                                    for label in labels[time].keys():
                                        if not foundAllArcs:
                                            break

                                        trackSet = labels[time][label]
                                        center = self.features[time][default_features_key]['RegionCenter'][label]
                                        trackCount = len(trackSet)

                                        for track in trackSet:

                                            if not foundAllArcs:
                                                logger.info("[opStructuredTrackingPgmlink] Increasing max nearest neighbors!")
                                                break

                                            # is this a FIRST, INTERMEDIATE, LAST, SINGLETON(FIRST_LAST) object of a track (or FALSE_DETECTION)
                                            type = self._type(cropKey, time, track) # returns [type, previous_label] if type=="LAST" or "INTERMEDIATE" (else [type])

                                            if type[0] == "LAST" or type[0] == "INTERMEDIATE":
                                                previous_label = int(type[1])
                                                previousTrackSet = labels[time-1][previous_label]
                                                intersectionSet = trackSet.intersection(previousTrackSet)
                                                trackCountIntersection = len(intersectionSet)

                                                foundAllArcs &= self.consTracker.addArcLabel(time-1, int(previous_label), int(label), float(trackCountIntersection))
                                                if not foundAllArcs:
                                                    logger.info("[opStructuredTrackingPgmlink] Increasing max nearest neighbors!")
                                                    break

                                        if type[0] == "FIRST":
                                            self.consTracker.addFirstLabels(time, int(label), float(trackCount))
                                            if time > self.Crops.value[cropKey]["time"][0]:
                                                self.consTracker.addDisappearanceLabel(time, int(label), 0.0)

                                        elif type[0] == "LAST":
                                            self.consTracker.addLastLabels(time, int(label), float(trackCount))
                                            if time < self.Crops.value[cropKey]["time"][1]:
                                                self.consTracker.addAppearanceLabel(time, int(label), 0.0)

                                        elif type[0] == "INTERMEDIATE":
                                            self.consTracker.addIntermediateLabels(time, int(label), float(trackCount))

                            if "divisions" in crop.keys():
                                divisions = crop["divisions"]
                                for track in divisions.keys():
                                    if not foundAllArcs:
                                        logger.info("[opStructuredTrackingPgmlink] Increasing max nearest neighbors!")
                                        break
                                    division = divisions[track]
                                    time = int(division[1])
                                    parent = int(self.getLabelInCrop(cropKey, time, track))

                                    if parent >=0:
                                        self.consTracker.addDivisionLabel(time, parent, 1.0)
                                        self.consTracker.addAppearanceLabel(time, parent, 1.0)
                                        self.consTracker.addDisappearanceLabel(time, parent, 1.0)

                                        child0 = int(self.getLabelInCrop(cropKey, time+1, division[0][0]))
                                        self.consTracker.addDisappearanceLabel(time+1, child0, 1.0)
                                        self.consTracker.addAppearanceLabel(time+1, child0, 1.0)
                                        foundAllArcs &= self.consTracker.addArcLabel(time, parent, child0, 1.0)
                                        if not foundAllArcs:
                                            logger.info("[opStructuredTrackingPgmlink] Increasing max nearest neighbors!")
                                            break

                                        child1 = int(self.getLabelInCrop(cropKey, time+1, division[0][1]))
                                        self.consTracker.addDisappearanceLabel(time+1, child1, 1.0)
                                        self.consTracker.addAppearanceLabel(time+1, child1, 1.0)
                                        foundAllArcs &= self.consTracker.addArcLabel(time, parent, child1, 1.0)
                                        if not foundAllArcs:
                                            logger.info("[opStructuredTrackingPgmlink] Increasing max nearest neighbors!")
                                            break


                logger.info("max nearest neighbors={}".format(new_max_nearest_neighbors))

        if not withBatchProcessing:
            drawer = self.parent.parent.trackingApplet._gui.currentGui()._drawer
            if new_max_nearest_neighbors > max_nearest_neighbors:
                max_nearest_neighbors = new_max_nearest_neighbors
                drawer.maxNearestNeighborsSpinBox.setValue(max_nearest_neighbors)
                self.parent.parent.trackingApplet._gui.currentGui()._maxNearestNeighbors = max_nearest_neighbors

        # create dummy uncertainty parameter object with just one iteration, so no perturbations at all (iter=0 -> MAP)
        sigmas = pgmlink.VectorOfDouble()
        for i in range(5):
            sigmas.append(0.0)
        uncertaintyParams = pgmlink.UncertaintyParameter(1, pgmlink.DistrId.PerturbAndMAP, sigmas)

        if withBatchProcessing:
            self.divisionWeight = parameters['divWeight']
            self.transitionWeight = parameters['transWeight']
            self.appearanceWeight = parameters['appearanceCost']
            self.disappearanceWeight = parameters['disappearanceCost']
            self.detectionWeight = parameters['detWeight']
        else:
            self.detectionWeight = drawer.detWeightBox.value()
            self.divisionWeight = drawer.divWeightBox.value()
            self.transitionWeight = drawer.transWeightBox.value()
            self.appearanceWeight = drawer.appearanceBox.value()
            self.disappearanceWeight = drawer.disappearanceBox.value()

        logger.info("detectionWeight= {}".format(self.detectionWeight))
        logger.info("divisionWeight={}".format(self.divisionWeight))
        logger.info("transitionWeight={}".format(self.transitionWeight))
        logger.info("appearanceWeight={}".format(self.appearanceWeight))
        logger.info("disappearanceWeight={}".format(self.disappearanceWeight))

        consTrackerParameters = self.consTracker.get_conservation_tracking_parameters(
                                        0,# forbidden_cost
                                        float(ep_gap),
                                        bool(withTracklets),
                                        float(self.detectionWeight),
                                        float(self.divisionWeight),
                                        float(self.transitionWeight),
                                        float(self.disappearanceWeight),
                                        float(self.appearanceWeight),
                                        bool(withMergerResolution),
                                        int(ndim),
                                        float(self.transition_parameter),
                                        float(borderAwareWidth),
                                        True, #with_constraints
                                        uncertaintyParams,
                                        float(cplex_timeout),
                                        None, # TransitionClassifier
                                        solverType,
                                        trainingToHardConstraints,
                                        1) # num threads

        # will be needed for python defined TRANSITION function
        # consTrackerParameters.register_transition_func(self.track_transition_func)

        fixLabeledNodes = False

        try:
            eventsVector = self.consTracker.track(consTrackerParameters, fixLabeledNodes )

            eventsVector = eventsVector[0] # we have a vector such that we could get a vector per perturbation

            if withMergerResolution:
                coordinate_map = pgmlink.TimestepIdCoordinateMap()
                self._get_merger_coordinates(coordinate_map,
                                             time_range,
                                             eventsVector)
                self.CoordinateMap.setValue(coordinate_map)

                eventsVector = self.consTracker.resolve_mergers(
                    eventsVector,
                    consTrackerParameters,
                    coordinate_map.get(),
                    float(ep_gap),
                    float(transWeight),
                    bool(withTracklets),
                    ndim,
                    self.transition_parameter,
                    max_traxel_id_at,
                    True, # with_constraints
                    None) # TransitionClassifier

        except Exception as e:
            if trainingToHardConstraints:
                raise Exception, 'Tracking: Your training can not be extended to a feasible solution! ' + \
                                 'Turn training to hard constraints off or correct your tracking training. '
            else:
                raise Exception, 'Tracking terminated unsuccessfully: ' + str(e)

        if len(eventsVector) == 0:
            raise Exception, 'Tracking terminated unsuccessfully: Events vector has zero length.'
        
        events = get_events(eventsVector)
        self.Parameters.setValue(parameters, check_changed=False)
        self.EventsVector.setValue(events, check_changed=False)
        self.RelabeledImage.setDirty()

        if not withBatchProcessing:
            merger_layer_idx = self.parent.parent.trackingApplet._gui.currentGui().layerstack.findMatchingIndex(lambda x: x.name == "Merger")
            tracking_layer_idx = self.parent.parent.trackingApplet._gui.currentGui().layerstack.findMatchingIndex(lambda x: x.name == "Tracking")
            if 'withMergerResolution' in parameters.keys() and not parameters['withMergerResolution']:
                self.parent.parent.trackingApplet._gui.currentGui().layerstack[merger_layer_idx].colorTable = \
                    self.parent.parent.trackingApplet._gui.currentGui().merger_colortable
            else:
                self.parent.parent.trackingApplet._gui.currentGui().layerstack[merger_layer_idx].colorTable = \
                    self.parent.parent.trackingApplet._gui.currentGui().tracking_colortable

    @staticmethod
    def getPgmlinkSolverType(solverName):
        if solverName == "ILP":
            # select solver type
            if hasattr(pgmlink.ConsTrackingSolverType, "CplexSolver"):
                solver = pgmlink.ConsTrackingSolverType.CplexSolver
            else:
                raise AssertionError("Cannot select ILP solver if pgmlink was compiled without ILP support")
        elif solverName == "Magnusson":
            if hasattr(pgmlink.ConsTrackingSolverType, "DynProgSolver"):
                solver = pgmlink.ConsTrackingSolverType.DynProgSolver
            else:
                raise AssertionError("Cannot select Magnusson solver if pgmlink was compiled without Magnusson support")
        elif solverName == "Flow":
            if hasattr(pgmlink.ConsTrackingSolverType, "FlowSolver"):
                solver = pgmlink.ConsTrackingSolverType.FlowSolver
            else:
                raise AssertionError("Cannot select Flow solver if pgmlink was compiled without Flow support")
        else:
            raise ValueError("Unknown solver {} selected".format(solverName))
        return solver

    def track_transition_func(self, traxel_1, traxel_2, state):
        return self.transitionWeight * self.track_transition_func_no_weight(traxel_1, traxel_2, state)

    def track_transition_func_no_weight(self, traxel_1, traxel_2, state):
        distance = math.sqrt((traxel_1.X()-traxel_2.X())*(traxel_1.X()-traxel_2.X()) + (traxel_1.Y()-traxel_2.Y())*(traxel_1.Y()-traxel_2.Y()) + (traxel_1.Z()-traxel_2.Z())*(traxel_1.Z()-traxel_2.Z())  )
        alpha = self.transition_parameter

        if state == 0:
            arg = 1.0 - math.exp(-distance/alpha)
        else:
            arg = math.exp(-distance/alpha)

        if arg < 0.0000000001:
            arg = 0.0000000001

        result = - math.log(arg,math.exp(1))

        if result == -0:
            return 0.0
        else:
            return result

    def getLabelInCrop(self, cropKey, time, track):
        labels = self.Annotations.value[cropKey]["labels"][time]
        for label in labels.keys():
            if self.Annotations.value[cropKey]["labels"][time][label] == set([track]):
                return label
        return -1

    def _type(self, cropKey, time, track):
        # returns [type, previous_label] if type=="LAST" or "INTERMEDIATE" (else [type])
        type = None
        if track == -1:
            return ["FALSE_DETECTION"]
        elif time == 0:
            type = "FIRST"

        labels = self.Annotations.value[cropKey]["labels"]

        crop = self.Crops.value[cropKey]
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
            for label in labels[t]:
                if track in labels[t][label]:
                    firstTime = t

        if firstTime == -1:
            if type == "FIRST":
                return ["SINGLETON"] #(FIRST_LAST)
            else:
                return ["LAST", lastLabel]
        elif firstTime > time+1:
            logger.info("ERROR: Your annotations are not complete. See time frame {}.".format(time+1))
        elif firstTime == time+1:
            if type ==  "INTERMEDIATE":
                return ["INTERMEDIATE",lastLabel]
            elif type != None:
                return [type]

    def propagateDirty(self, slot, subindex, roi):
        super(OpStructuredTrackingPgmlink, self).propagateDirty(slot, subindex, roi)

        if slot == self.NumLabels:
            if self.parent.parent.trackingApplet._gui \
                    and self.parent.parent.trackingApplet._gui.currentGui() \
                    and self.NumLabels.ready() \
                    and self.NumLabels.value > 1:
                self.parent.parent.trackingApplet._gui.currentGui()._drawer.maxObjectsBox.setValue(self.NumLabels.value-1)

    def _get_merger_coordinates(self, coordinate_map, time_range, eventsVector):
        feats = self.ObjectFeatures(time_range).wait()
        for t in feats.keys():
            rc = feats[t][default_features_key]['RegionCenter']
            lower = feats[t][default_features_key]['Coord<Minimum>']
            upper = feats[t][default_features_key]['Coord<Maximum>']
            size = feats[t][default_features_key]['Count']
            for event in eventsVector[t]:
                if event.type == pgmlink.EventType.Merger:
                    idx = event.traxel_ids[0]
                    n_dim = len(rc[idx])
                    roi = [0]*5
                    roi[0] = slice(int(t), int(t+1))
                    roi[1] = slice(int(lower[idx][0]), int(upper[idx][0] + 1))
                    roi[2] = slice(int(lower[idx][1]), int(upper[idx][1] + 1))
                    if n_dim == 3:
                        roi[3] = slice(int(lower[idx][2]), int(upper[idx][2] + 1))
                    else:
                        assert n_dim == 2
                    image_excerpt = self.LabelImage[roi].wait()
                    if n_dim == 2:
                        image_excerpt = image_excerpt[0, ..., 0, 0]
                    elif n_dim ==3:
                        image_excerpt = image_excerpt[0, ..., 0]
                    else:
                        raise Exception, "n_dim = %s instead of 2 or 3"

                    pgmlink.extract_coord_by_timestep_id(coordinate_map,
                                                         image_excerpt,
                                                         lower[idx].astype(np.int64),
                                                         t,
                                                         idx,
                                                         int(size[idx,0]))

    def _relabelMergers(self, volume, time, pixel_offsets=[0, 0, 0], onlyMergers=False, noRelabeling=False):
        if self.CoordinateMap.value.size == 0:
            logger.info("Skipping merger relabeling because coordinate map is empty.")
            if onlyMergers:
                return np.zeros_like(volume)
            else:
                return volume
        if time >= len(self.resolvedto):
            if onlyMergers:
                return np.zeros_like(volume)
            else:
                return volume

        coordinate_map = self.CoordinateMap.value
        valid_ids = []
        for old_id, new_ids in self.resolvedto[time].iteritems():
            for new_id in new_ids:
                # TODO Reliable distinction between 2d and 3d?
                if self._ndim == 2:
                    # Assume we have 2d data: bind z to zero
                    relabel_volume = volume[..., 0]
                else:
                    # For 3d data use the whole volume
                    relabel_volume = volume
                # relabel
                pgmlink.update_labelimage(
                    coordinate_map,
                    relabel_volume,
                    np.array(pixel_offsets, dtype=np.int64),
                    int(time),
                    int(new_id))
                valid_ids.append(new_id)

        if onlyMergers:
            # find indices of merger ids, set everything else to zero
            idx = np.in1d(volume.ravel(), valid_ids).reshape(volume.shape)
            volume[-idx] = 0

        if noRelabeling:
            return volume
        else:
            return relabel(volume, self.label2color[time])

    def do_export(self, settings, selected_features, progress_slot, lane_index, filename_suffix=""):
        """
        Implements ExportOperator.do_export(settings, selected_features, progress_slot
        Most likely called from ExportOperator.export_object_data
        :param settings: the settings for the exporter, see
        :param selected_features:
        :param progress_slot:
        :param lane_index: Ignored. (This is a single-lane operator. It is the caller's responsibility to make sure he's calling the right lane.)
        :param filename_suffix: If provided, appended to the filename (before the extension).
        :return:
        """

        #assert lane_index == 0, "This has only been tested in tracking workflows with a single image."

        with_divisions = self.Parameters.value["withDivisions"] if self.Parameters.ready() else False
        with_merger_resolution = self.Parameters.value["withMergerResolution"] if self.Parameters.ready() else False

        if with_divisions:
            object_feature_slot = self.ObjectFeaturesWithDivFeatures
        else:
            object_feature_slot = self.ObjectFeatures

        if with_merger_resolution:
            label_image = self.RelabeledImage

            opRelabeledRegionFeatures = self._setupRelabeledFeatureSlot(object_feature_slot)
            object_feature_slot = opRelabeledRegionFeatures.RegionFeatures
        else:
            label_image = self.LabelImage

        self._do_export_impl(settings, selected_features, progress_slot, object_feature_slot, label_image, lane_index, filename_suffix)

        if with_merger_resolution:
            opRelabeledRegionFeatures.cleanUp()


    def _setupRelabeledFeatureSlot(self, original_feature_slot):
        from ilastik.applets.trackingFeatureExtraction import config
        # when exporting after merger resolving, the stored object features are not up to date for the relabeled objects
        opRelabeledRegionFeatures = OpRelabeledMergerFeatureExtraction(parent=self)
        opRelabeledRegionFeatures.RawImage.connect(self.RawImage)
        opRelabeledRegionFeatures.LabelImage.connect(self.LabelImage)
        opRelabeledRegionFeatures.RelabeledImage.connect(self.RelabeledImage)
        opRelabeledRegionFeatures.OriginalRegionFeatures.connect(original_feature_slot)
        opRelabeledRegionFeatures.ResolvedTo.setValue(self.resolvedto)

        vigra_features = list((set(config.vigra_features)).union(config.selected_features_objectcount[config.features_vigra_name]))
        feature_names_vigra = {}
        feature_names_vigra[config.features_vigra_name] = { name: {} for name in vigra_features }
        opRelabeledRegionFeatures.FeatureNames.setValue(feature_names_vigra)

        return opRelabeledRegionFeatures

    def _updateCropsFromOperator(self):
        self._crops = self.Crops.value

    def _runStructuredLearning(self,
            z_range,
            maxObj,
            maxNearestNeighbors,
            withDivisions,
            borderAwareWidth,
            withClassifierPrior,
            withBatchProcessing=False):

        if not withBatchProcessing:
            gui = self.parent.parent.trackingApplet._gui.currentGui()

        if self.Annotations.value == {}:
            if not withBatchProcessing:
                gui._criticalMessage("Error: Weights can not be calculated because there are no training annotations. " +\
                                  "Go back to Training applet and Save your training for each crop.")
            return

        print "in _runStructuredLearning  <============================================"
        self._updateCropsFromOperator()
        median_obj_size = [0]

        from_z = z_range[0]
        to_z = z_range[1]
        ndim=3
        if (to_z - from_z == 0):
            ndim=2

        fieldOfView = pgmlink.FieldOfView(
            float(0),
            float(0),
            float(0),
            float(0),
            float(self.LabelImage.meta.shape[0]),
            float(self.LabelImage.meta.shape[1]),
            float(self.LabelImage.meta.shape[2]),
            float(self.LabelImage.meta.shape[3]))

        parameters = self.Parameters.value

        parameters['maxObj'] = maxObj
        parameters['withDivisions'] = withDivisions
        parameters['withClassifierPrior'] = withClassifierPrior
        parameters['borderAwareWidth'] = borderAwareWidth

        foundAllArcs = False;
        new_max_nearest_neighbors = maxNearestNeighbors-1
        maxObjOK = True
        parameters['maxNearestNeighbors'] = maxNearestNeighbors
        while not foundAllArcs and maxObjOK:
            new_max_nearest_neighbors += 1
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

            time_range = range (0,self.LabelImage.meta.shape[0])
            featureStore, traxelStore, empty_frame, max_traxel_id_at = self._generate_traxelstore(
                time_range,
                (0,self.LabelImage.meta.shape[1]),#x_range
                (0,self.LabelImage.meta.shape[2]),#y_range
                (0,self.LabelImage.meta.shape[3]),#z_range,
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

            structuredLearningTracker.addLabels()

            mergeMsgStr = "Your tracking annotations contradict this model assumptions! All tracks must be continuous, tracks of length one are not allowed, and mergers may merge or split but all tracks in a merger appear/disappear together."
            foundAllArcs = True;
            numAllAnnotatedDivisions = 0

            self.features = self.ObjectFeatures(range(0,self.LabelImage.meta.shape[0])).wait()

            for cropKey in self.Crops.value.keys():
                if foundAllArcs:

                    if not cropKey in self.Annotations.value.keys():
                        if not withBatchProcessing:
                            self._criticalMessage("You have not trained or saved your training for " + str(cropKey) + \
                                              ". \nGo back to the Training applet and save all your training!")
                        return

                    crop = self.Annotations.value[cropKey]

                    if "labels" in crop.keys():

                        labels = crop["labels"]

                        for time in labels.keys():

                            if not foundAllArcs:
                                break

                            for label in labels[time].keys():

                                if not foundAllArcs:
                                    break

                                trackSet = labels[time][label]
                                center = self.features[time][default_features_key]['RegionCenter'][label]
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
                                    if time > self.Crops.value[cropKey]["time"][0]:
                                        structuredLearningTracker.addDisappearanceLabel(time, int(label), 0.0)

                                elif type[0] == "LAST":
                                    structuredLearningTracker.addLastLabels(time, int(label), float(trackCount))
                                    if time < self.Crops.value[cropKey]["time"][1]:
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

        if new_max_nearest_neighbors > maxNearestNeighbors:
            maxNearestNeighbors = new_max_nearest_neighbors
            parameters['maxNearestNeighbors'] = maxNearestNeighbors
            if not withBatchProcessing:
                self.parent.parent.trackingApplet._drawer.maxNearestNeighborsSpinBox.setValue(maxNearestNeighbors)

        forbidden_cost = 0.0
        ep_gap = 0.005
        withTracklets=False
        withMergerResolution=True
        transition_parameter = 5.0
        sigmas = pgmlink.VectorOfDouble()
        for i in range(5):
            sigmas.append(0.0)
        uncertaintyParams = pgmlink.UncertaintyParameter(1, pgmlink.DistrId.PerturbAndMAP, sigmas)

        cplex_timeout=float(1000.0)
        transitionClassifier = None

        detectionWeight = self.DetectionWeight.value
        divisionWeight = self.DivisionWeight.value
        transitionWeight = self.TransitionWeight.value
        disappearanceWeight = self.DisappearanceWeight.value
        appearanceWeight = self.AppearanceWeight.value

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
        if not withBatchProcessing and withDivisions and numAllAnnotatedDivisions == 0 and not structuredLearningTracker.weight(1) == 0.0:
            self._informationMessage ("Divisible objects are checked, but you did not annotate any divisions in your tracking training. " + \
                                 "The resulting division weight might be arbitrarily high and if there are divisions present in the dataset, " +\
                                 "they might not be present in the tracking solution.")

        norm = 0
        for i in range(5):
            norm += structuredLearningTracker.weight(i)*structuredLearningTracker.weight(i)
        norm = math.sqrt(norm)

        if norm > 0.0000001:
            self.DetectionWeight.setValue(structuredLearningTracker.weight(0)/norm)
            self.DivisionWeight.setValue(structuredLearningTracker.weight(1)/norm)
            self.TransitionWeight.setValue(structuredLearningTracker.weight(2)/norm)
            self.AppearanceWeight.setValue(structuredLearningTracker.weight(3)/norm)
            self.DisappearanceWeight.setValue(structuredLearningTracker.weight(4)/norm)

        if not withBatchProcessing:
            gui._drawer.detWeightBox.setValue(self.DetectionWeight.value);
            gui._drawer.divWeightBox.setValue(self.DivisionWeight.value);
            gui._drawer.transWeightBox.setValue(self.TransitionWeight.value);
            gui._drawer.appearanceBox.setValue(self.AppearanceWeight.value);
            gui._drawer.disappearanceBox.setValue(self.DisappearanceWeight.value);

        epsZero = 0.01
        if not withBatchProcessing:
            if self.DetectionWeight.value < 0.0:
                gui._informationMessage ("Detection weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                    "Furthermore, you should add more training and recalculate the learning weights in order to improve your tracking solution.")
            elif self.DivisionWeight.value < 0.0:
                gui._informationMessage ("Division weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                    "Furthermore, you should add more division cells to your training and recalculate the learning weights in order to improve your tracking solution.")
            elif self.TransitionWeight.value < 0.0:
                gui._informationMessage ("Transition weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                    "Furthermore, you should add more transitions to your training and recalculate the learning weights in order to improve your tracking solution.")
            elif self.AppearanceWeight.value < 0.0:
                gui._informationMessage ("Appearance weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                    "Furthermore, you should add more appearances to your training and recalculate the learning weights in order to improve your tracking solution.")
            elif self.DisappearanceWeight.value < 0.0:
                gui._informationMessage ("Disappearance weight calculated was negative. Tracking solution will be re-calculated with non-negativity constraints for learning weights. " + \
                    "Furthermore, you should add more disappearances to your training and recalculate the learning weights in order to improve your tracking solution.")

        if self.DetectionWeight.value < 0.0 or self.DivisionWeight.value < 0.0 or self.TransitionWeight.value < 0.0 or \
            self.AppearanceWeight.value < 0.0 or self.DisappearanceWeight.value < 0.0:

            structuredLearningTrackerParameters.setWithNonNegativeWeights(True)
            structuredLearningTracker.structuredLearning(structuredLearningTrackerParameters)
            norm = 0
            for i in range(5):
                norm += structuredLearningTracker.weight(i)*structuredLearningTracker.weight(i)
            norm = math.sqrt(norm)

            if norm > 0.0000001:
                self.DetectionWeight.setValue(structuredLearningTracker.weight(0)/norm)
                self.DivisionWeight.setValue(structuredLearningTracker.weight(1)/norm)
                self.TransitionWeight.setValue(structuredLearningTracker.weight(2)/norm)
                self.AppearanceWeight.setValue(structuredLearningTracker.weight(3)/norm)
                self.DisappearanceWeight.setValue(structuredLearningTracker.weight(4)/norm)

            if not withBatchProcessing:
                gui._drawer.detWeightBox.setValue(self.DetectionWeight.value);
                gui._drawer.divWeightBox.setValue(self.DivisionWeight.value);
                gui._drawer.transWeightBox.setValue(self.TransitionWeight.value);
                gui._drawer.appearanceBox.setValue(self.AppearanceWeight.value);
                gui._drawer.disappearanceBox.setValue(self.DisappearanceWeight.value);

        logger.info("Structured Learning Tracking Weights (normalized):")
        logger.info("   detection weight     = {}".format(self.DetectionWeight.value))
        logger.info("   detection weight     = {}".format(self.DivisionWeight.value))
        logger.info("   detection weight     = {}".format(self.TransitionWeight.value))
        logger.info("   detection weight     = {}".format(self.AppearanceWeight.value))
        logger.info("   detection weight     = {}".format(self.DisappearanceWeight.value))

        parameters['detWeight'] = self.DetectionWeight.value
        parameters['divWeight'] = self.DivisionWeight.value
        parameters['transWeight'] = self.TransitionWeight.value
        parameters['appearanceCost'] = self.AppearanceWeight.value
        parameters['disappearanceCost'] = self.DisappearanceWeight.value

        print "-----------+------------->parameters['detWeight']",parameters['detWeight']
        print "-----------+------------->parameters['divWeight']",parameters['divWeight']
        print "-----------+------------->parameters['transWeight']",parameters['transWeight']

        self.Parameters.setValue(parameters)

        return [self.DetectionWeight.value, self.DivisionWeight.value, self.TransitionWeight.value, self.AppearanceWeight.value, self.DisappearanceWeight.value]

    def getLabelInCrop(self, cropKey, time, track):
        labels = self.Annotations.value[cropKey]["labels"][time]
        for label in labels.keys():
            if self.Annotations.value[cropKey]["labels"][time][label] == set([track]):
                return label
        return -1

    def _type(self, cropKey, time, track):
        # returns [type, previous_label] (if type=="LAST" or "INTERMEDIATE" else [type])
        type = None
        if track == -1:
            return ["FALSE_DETECTION"]
        elif time == 0:
            type = "FIRST"

        labels = self.Annotations.value[cropKey]["labels"]
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

