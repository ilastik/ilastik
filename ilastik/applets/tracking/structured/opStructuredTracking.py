from __future__ import division
from builtins import range
from past.utils import old_div
import math

from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import List
from ilastik.utility import bind

from ilastik.applets.tracking.conservation.opConservationTracking import OpConservationTracking
from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key

from ilastik.utility.progress import DefaultProgressVisitor, CommandLineProgressVisitor

import logging
logger = logging.getLogger(__name__)

from ilastik.applets.tracking.conservation.opConservationTracking import OpConservationTracking
try:
    import multiHypoTracking_with_cplex as mht
except ImportError:
    try:
        import multiHypoTracking_with_gurobi as mht
    except ImportError:
        logger.warning("Could not find any ILP solver")


class OpStructuredTracking(OpConservationTracking):
    Labels = InputSlot(stype=Opaque, rtype=List)
    Divisions = InputSlot(stype=Opaque, rtype=List)
    Appearances = InputSlot(stype=Opaque)
    Disappearances = InputSlot(stype=Opaque)
    Annotations = InputSlot(stype=Opaque)
    MaxNumObj = InputSlot()
    LearningHypothesesGraph = InputSlot(value={})

    DivisionWeight = OutputSlot()
    DetectionWeight = OutputSlot()
    TransitionWeight = OutputSlot()
    AppearanceWeight = OutputSlot()
    DisappearanceWeight = OutputSlot()
    MaxNumObjOut = OutputSlot()

    def __init__(self, parent=None, graph=None):
        self._solver = "ILP"
        super(OpStructuredTracking, self).__init__(parent=parent, graph=graph)

        self.labels = {}
        self.divisions = {}
        self.appearances = {}
        self.disappearances = {}
        self.Annotations.setValue({})
        self.Appearances.setValue({})
        self.Disappearances.setValue({})
        self._ndim = 3

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

        self.Labels.notifyReady( bind(self._updateLabelsFromOperator) )
        self.Divisions.notifyReady( bind(self._updateDivisionsFromOperator) )
        self.Appearances.notifyReady( bind(self._updateAppearancesFromOperator) )
        self.Disappearances.notifyReady( bind(self._updateDisappearancesFromOperator) )

        self._solver = self.parent.parent._solver

    def _updateLabelsFromOperator(self):
        self.labels = self.Labels.value

    def _updateDivisionsFromOperator(self):
        self.divisions = self.Divisions.value

    def _updateAppearancesFromOperator(self):
        self.appearances = self.Appearances.value

    def _updateDisappearancesFromOperator(self):
        self.disappearances = self.Disappearances.value

    def setupOutputs(self):
        super(OpStructuredTracking, self).setupOutputs()
        self._ndim = 2 if self.LabelImage.meta.shape[3] == 1 else 3

        for t in range(self.LabelImage.meta.shape[0]):
            if t not in list(self.labels.keys()):
                self.labels[t]={}

    def execute(self, slot, subindex, roi, result):

        if slot is self.Labels:
            result=self.Labels.wait()

        elif slot is self.Divisions:
            result=self.Divisions.wait()

        elif slot is self.Appearances:
            result=self.Appearances.wait()

        elif slot is self.Disappearances:
            result=self.Disappearances.wait()

        else:
            super(OpStructuredTracking, self).execute(slot, subindex, roi, result)

        return result

    def _runStructuredLearning(self,
            z_range,
            maxObj,
            maxNearestNeighbors,
            maxDist,
            divThreshold,
            scales,
            size_range,
            withDivisions,
            borderAwareWidth,
            withClassifierPrior,
            withBatchProcessing=False,
            progressWindow=None,
            progressVisitor=CommandLineProgressVisitor()
        ):

        if not withBatchProcessing:
            gui = self.parent.parent.trackingApplet._gui.currentGui()

        self.progressWindow = progressWindow
        self.progressVisitor=progressVisitor
        
        emptyAnnotations = False
        empty = self.Annotations.value == {} or \
                "divisions" in list(self.Annotations.value.keys()) and self.Annotations.value["divisions"]=={} and \
                "labels" in self.Annotations.value.keys() and self.Annotations.value["labels"]=={}
        if empty and not withBatchProcessing:
            gui._criticalMessage("Error: Weights can not be calculated because training annotations are missing. " +\
                              "Go back to Training applet!")
        emptyAnnotations = emptyAnnotations or empty

        if emptyAnnotations:
            return [self.DetectionWeight.value, self.DivisionWeight.value, self.TransitionWeight.value, self.AppearanceWeight.value, self.DisappearanceWeight.value]

        median_obj_size = [0]

        from_z = z_range[0]
        to_z = z_range[1]
        ndim=3
        if (to_z - from_z == 0):
            ndim=2

        time_range = [0, self.LabelImage.meta.shape[0]-1]
        x_range = [0, self.LabelImage.meta.shape[1]]
        y_range = [0, self.LabelImage.meta.shape[2]]
        z_range = [0, self.LabelImage.meta.shape[3]]

        parameters = self.Parameters.value

        parameters['maxDist'] = maxDist
        parameters['maxObj'] = maxObj
        parameters['divThreshold'] = divThreshold
        parameters['withDivisions'] = withDivisions
        parameters['withClassifierPrior'] = withClassifierPrior
        parameters['borderAwareWidth'] = borderAwareWidth
        parameters['scales'] = scales
        parameters['time_range'] = [min(time_range), max(time_range)]
        parameters['x_range'] = x_range
        parameters['y_range'] = y_range
        parameters['z_range'] = z_range
        parameters['max_nearest_neighbors'] = maxNearestNeighbors
        parameters['withTracklets'] = False

        # Set a size range with a minimum area equal to the max number of objects (since the GMM throws an error if we try to fit more gaussians than the number of pixels in the object)
        size_range = (max(maxObj, size_range[0]), size_range[1])
        parameters['size_range'] = size_range

        self.Parameters.setValue(parameters, check_changed=False)

        foundAllArcs = False
        new_max_nearest_neighbors = max ([maxNearestNeighbors-1,1])
        maxObjOK = True
        parameters['max_nearest_neighbors'] = maxNearestNeighbors
        while not foundAllArcs and maxObjOK and new_max_nearest_neighbors<10:
            new_max_nearest_neighbors += 1
            logger.info("new_max_nearest_neighbors: {}".format(new_max_nearest_neighbors))

            time_range = list(range(0,self.LabelImage.meta.shape[0]))

            parameters['max_nearest_neighbors'] = new_max_nearest_neighbors
            self.Parameters.setValue(parameters, check_changed=False)

            hypothesesGraph = self._createHypothesesGraph()
            if hypothesesGraph.countNodes() == 0:
                raise DatasetConstraintError('Structured Learning', 'Can not track frames with 0 objects, abort.')

            logger.info("Structured Learning: Adding Training Annotations to Hypotheses Graph")

            mergeMsgStr = "Your tracking annotations contradict this model assumptions! All tracks must be continuous; mergers may merge or split but all tracks in a merger appear/disappear together. " + \
                "You may also have to improve division and/or object count classifier in order to match your tracking annotations with small uncertainty (see Uncertainty Layer in the classiefiers)."
            foundAllArcs = True;
            numAllAnnotatedDivisions = 0

            self.features = self.ObjectFeatures(list(range(0,self.LabelImage.meta.shape[0]))).wait()

            if foundAllArcs:

                timeRange = [0,self.LabelImage.meta.shape[0]]

                if "labels" in self.Annotations.value:

                    labels = self.Annotations.value["labels"]

                    for time in list(labels.keys()):
                        if time in range(timeRange[0],timeRange[1]+1):

                            if not foundAllArcs:
                                break

                            for label in list(labels[time].keys()):

                                if not foundAllArcs:
                                    break

                                trackSet = labels[time][label]
                                center = self.features[time][default_features_key]['RegionCenter'][label]
                                trackCount = len(trackSet)

                                if trackCount > maxObj:
                                    logger.info("Your track count for object {} in time frame {} is {} =| {} |, which is greater than maximum object number {} defined by object count classifier!".format(label,time,trackCount,trackSet,maxObj))
                                    logger.info("Either remove track(s) from this object or train the object count classifier with more labels!")
                                    maxObjOK = False
                                    self.raiseDatasetConstraintError(self.progressWindow, 'Structured Learning', "Your track count for object "+str(label)+" in time frame " +str(time)+ " equals "+str(trackCount)+"=|"+str(trackSet)+"|," + \
                                            " which is greater than the maximum object number "+str(maxObj)+" defined by object count classifier! " + \
                                            "Either remove track(s) from this object or train the object count classifier with more labels!")

                                for track in trackSet:

                                    if not foundAllArcs:
                                        logger.info("[structuredTrackingGui] Increasing max nearest neighbors!")
                                        break

                                    # is this a FIRST, INTERMEDIATE, LAST, SINGLETON(FIRST_LAST) object of a track (or FALSE_DETECTION)
                                    type = self._type(time, track) # returns [type, previous_label] if type=="LAST" or "INTERMEDIATE" (else [type])
                                    print ("time, track",time, track, "type",type)
                                    if type == None:
                                        self.raiseDatasetConstraintError(self.progressWindow, 'Structured Learning', mergeMsgStr)

                                    elif type[0] in ["LAST", "INTERMEDIATE"]:

                                        previous_label = int(type[1])
                                        previousTrackSet = labels[time-1][previous_label]
                                        intersectionSet = trackSet.intersection(previousTrackSet)
                                        trackCountIntersection = len(intersectionSet)

                                        if trackCountIntersection > maxObj:
                                            logger.info("Your track count for transition ( {},{} ) ---> ( {},{} ) is {} =| {} |, which is greater than maximum object number {} defined by object count classifier!".format(previous_label,time-1,label,time,trackCountIntersection,intersectionSet,maxObj))
                                            logger.info("Either remove track(s) from these objects or train the object count classifier with more labels!")
                                            maxObjOK = False
                                            self.raiseDatasetConstraintError(self.progressWindow, 'Structured Learning', "Your track count for transition ("+str(previous_label)+","+str(time-1)+") ---> ("+str(label)+","+str(time)+") is "+str(trackCountIntersection)+"=|"+str(intersectionSet)+"|, " + \
                                                    "which is greater than maximum object number "+str(maxObj)+" defined by object count classifier!" + \
                                                    "Either remove track(s) from these objects or train the object count classifier with more labels!")


                                        sink = (time, int(label))
                                        foundAllArcs = False
                                        for edge in list(hypothesesGraph._graph.in_edges(sink)): # an edge is a tuple of source and target nodes
                                            logger.debug("Looking at in edge {} of node {}, searching for ({},{})".format(edge, sink, time-1, previous_label))
                                            # print "Looking at in edge {} of node {}, searching for ({},{})".format(edge, sink, time-1, previous_label)
                                            if edge[0][0] == time-1 and edge[0][1] == int(previous_label): # every node 'id' is a tuple (timestep, label), so we need the in-edge coming from previous_label
                                                foundAllArcs = True
                                                hypothesesGraph._graph.edge[edge[0]][edge[1]]['value'] = int(trackCountIntersection)
                                                break
                                        if not foundAllArcs:
                                            logger.info("[structuredTrackingGui] Increasing max nearest neighbors! LABELS/MERGERS t:{} id:{}".format(time-1, int(previous_label)))
                                            # print "[structuredTrackingGui] Increasing max nearest neighbors! LABELS/MERGERS t:{} id:{}".format(time-1, int(previous_label))
                                            break

                                    if type[0] in ["FIRST", "SINGLETON(FIRST_LAST)"] and time in self.appearances.keys() and label in self.appearances[time].keys() and track in self.appearances[time][label].keys() and self.appearances[time][label][track]:
                                        # print("---> appearance",time,label,track)
                                        if (time, int(label)) in list(hypothesesGraph._graph.node.keys()):
                                            hypothesesGraph._graph.node[(time, int(label))]['appearance'] = True
                                            logger.debug("[structuredTrackingGui] APPEARANCE: {} {}".format(time, int(label)))

                                    elif type[0] in ["LAST", "SINGLETON(FIRST_LAST)"] and time in self.disappearances.keys() and label in self.disappearances[time].keys() and track in self.disappearances[time][label].keys() and self.disappearances[time][label][track]:
                                        # print("---> disappearance",time,label,track)
                                        if (time, int(label)) in list(hypothesesGraph._graph.node.keys()):
                                            hypothesesGraph._graph.node[(time, int(label))]['disappearance'] = True
                                            logger.debug("[structuredTrackingGui] DISAPPEARANCE: {} {}".format(time, int(label)))

                                if type == None:
                                    self.raiseDatasetConstraintError(self.progressWindow, 'Structured Learning', mergeMsgStr)

                                elif type[0] in ["FIRST", "LAST", "INTERMEDIATE", "SINGLETON(FIRST_LAST)"]:
                                    if (time, int(label)) in list(hypothesesGraph._graph.node.keys()):
                                        hypothesesGraph._graph.node[(time, int(label))]['value'] = trackCount
                                        logger.debug("[structuredTrackingGui] NODE: {} {}".format(time, int(label)))
                                        # print "[structuredTrackingGui] NODE: {} {} {}".format(time, int(label), int(trackCount))
                                    else:
                                        logger.debug("[structuredTrackingGui] NODE: {} {} NOT found".format(time, int(label)))
                                        # print "[structuredTrackingGui] NODE: {} {} NOT found".format(time, int(label))

                                        foundAllArcs = False
                                        break

                if foundAllArcs and "divisions" in list(self.Annotations.value.keys()):
                    divisions = self.Annotations.value["divisions"]

                    numAllAnnotatedDivisions = numAllAnnotatedDivisions + len(divisions)
                    for track in list(divisions.keys()):
                        if not foundAllArcs:
                            break

                        division = divisions[track]
                        time = int(division[1])

                        parent = int(self.getLabelTT(time, track))

                        if parent >=0:
                            children = [int(self.getLabelTT(time+1, division[0][i])) for i in [0, 1]]
                            parentNode = (time, parent)
                            hypothesesGraph._graph.node[parentNode]['divisionValue'] = 1
                            foundAllArcs = False
                            for child in children:
                                for edge in hypothesesGraph._graph.out_edges(parentNode): # an edge is a tuple of source and target nodes
                                    if edge[1][0] == time+1 and edge[1][1] == int(child): # every node 'id' is a tuple (timestep, label), so we need the in-edge coming from previous_label
                                        foundAllArcs = True
                                        hypothesesGraph._graph.edge[edge[0]][edge[1]]['value'] = 1
                                        break
                                if not foundAllArcs:
                                    break

                            if not foundAllArcs:
                                logger.info("[structuredTrackingGui] Increasing max nearest neighbors! DIVISION {} {}".format(time, parent))
                                # print "[structuredTrackingGui] Increasing max nearest neighbors! DIVISION {} {}".format(time, parent)
                                break
        logger.info("max nearest neighbors= {}".format(new_max_nearest_neighbors))

        if new_max_nearest_neighbors > maxNearestNeighbors:
            maxNearestNeighbors = new_max_nearest_neighbors
            parameters['maxNearestNeighbors'] = maxNearestNeighbors
            if not withBatchProcessing:
                gui._drawer.maxNearestNeighborsSpinBox.setValue(maxNearestNeighbors)

        detectionWeight = self.DetectionWeight.value
        divisionWeight = self.DivisionWeight.value
        transitionWeight = self.TransitionWeight.value
        disappearanceWeight = self.DisappearanceWeight.value
        appearanceWeight = self.AppearanceWeight.value

        if not foundAllArcs:
            logger.info("[structuredTracking] Increasing max nearest neighbors did not result in finding all training arcs!")
            return [transitionWeight, detectionWeight, divisionWeight, appearanceWeight, disappearanceWeight]

        hypothesesGraph.insertEnergies()

        self.progressVisitor.showState("Structured learning")
        self.progressVisitor.showProgress(0)

        # crops away everything (arcs and nodes) that doesn't have 'value' set
        prunedGraph = hypothesesGraph.pruneGraphToSolution(distanceToSolution=0) # width of non-annotated border needed for negative training examples

        trackingGraph = prunedGraph.toTrackingGraph()

        # trackingGraph.convexifyCosts()
        model = trackingGraph.model
        model['settings']['optimizerEpGap'] = 0.005
        model['settings']['allowLengthOneTracks'] = False
        gt = prunedGraph.getSolutionDictionary()

        initialWeights = trackingGraph.weightsListToDict([transitionWeight, detectionWeight, divisionWeight, appearanceWeight, disappearanceWeight])

        self.LearningHypothesesGraph.setValue(hypothesesGraph)
        mht.trainWithWeightInitialization(model,gt, initialWeights)
        weightsDict = mht.train(model, gt)

        weights = trackingGraph.weightsDictToList(weightsDict)

        self.progressVisitor.showProgress(1)

        if not withBatchProcessing and withDivisions and numAllAnnotatedDivisions == 0 and not weights[2] == 0.0:
            gui._informationMessage("Divisible objects are checked, but you did not annotate any divisions in your tracking training. " + \
                                 "The resulting division weight might be arbitrarily and if there are divisions present in the dataset, " +\
                                 "they might not be present in the tracking solution.")

        norm = 0
        for i in range(len(weights)):
            norm += weights[i]*weights[i]
        norm = math.sqrt(norm)

        if norm > 0.0000001:
            self.TransitionWeight.setValue(old_div(weights[0],norm))
            self.DetectionWeight.setValue(old_div(weights[1],norm))
            self.DivisionWeight.setValue(old_div(weights[2],norm))
            self.AppearanceWeight.setValue(old_div(weights[3],norm))
            self.DisappearanceWeight.setValue(old_div(weights[4],norm))

        if not withBatchProcessing:
            gui._drawer.detWeightBox.setValue(self.DetectionWeight.value)
            gui._drawer.divWeightBox.setValue(self.DivisionWeight.value)
            gui._drawer.transWeightBox.setValue(self.TransitionWeight.value)
            gui._drawer.appearanceBox.setValue(self.AppearanceWeight.value)
            gui._drawer.disappearanceBox.setValue(self.DisappearanceWeight.value)

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

            self.progressVisitor.showProgress(0)
            model['settings']['nonNegativeWeightsOnly'] = True
            weightsDict = mht.train(model, gt)

            weights = trackingGraph.weightsDictToList(weightsDict)

            norm = 0
            for i in range(len(weights)):
                norm += weights[i]*weights[i]
            norm = math.sqrt(norm)

            if norm > 0.0000001:
                self.TransitionWeight.setValue(old_div(weights[0],norm))
                self.DetectionWeight.setValue(old_div(weights[1],norm))
                self.DivisionWeight.setValue(old_div(weights[2],norm))
                self.AppearanceWeight.setValue(old_div(weights[3],norm))
                self.DisappearanceWeight.setValue(old_div(weights[4],norm))

            if not withBatchProcessing:
                gui._drawer.detWeightBox.setValue(self.DetectionWeight.value)
                gui._drawer.divWeightBox.setValue(self.DivisionWeight.value)
                gui._drawer.transWeightBox.setValue(self.TransitionWeight.value)
                gui._drawer.appearanceBox.setValue(self.AppearanceWeight.value)
                gui._drawer.disappearanceBox.setValue(self.DisappearanceWeight.value)

        if self.progressWindow is not None:
            self.progressWindow.onTrackDone()

        logger.info("Structured Learning Tracking Weights (normalized):")
        logger.info("   detection weight     = {}".format(self.DetectionWeight.value))
        logger.info("   division weight     = {}".format(self.DivisionWeight.value))
        logger.info("   transition weight     = {}".format(self.TransitionWeight.value))
        logger.info("   appearance weight     = {}".format(self.AppearanceWeight.value))
        logger.info("   disappearance weight     = {}".format(self.DisappearanceWeight.value))

        parameters['detWeight'] = self.DetectionWeight.value
        parameters['divWeight'] = self.DivisionWeight.value
        parameters['transWeight'] = self.TransitionWeight.value
        parameters['appearanceCost'] = self.AppearanceWeight.value
        parameters['disappearanceCost'] = self.DisappearanceWeight.value

        self.Parameters.setValue(parameters)
        self.Parameters.setDirty()

        return [self.DetectionWeight.value, self.DivisionWeight.value, self.TransitionWeight.value, self.AppearanceWeight.value, self.DisappearanceWeight.value]

    def getLabelTT(self, time, track):
        labels = self.Annotations.value["labels"][time]
        for label in list(labels.keys()):
            if self.Annotations.value["labels"][time][label] == set([track]):
                return label
        return -1

    def _type(self, time, track):
        # returns [type, previous_label] (if type=="LAST" or "INTERMEDIATE" else [type])
        type = None
        if track == -1:
            return ["FALSE_DETECTION"]
        elif time == 0:
            type = "FIRST"

        labels = self.Annotations.value["labels"]
        lastTime = -1
        lastLabel = -1
        maxTime = self.LabelImage.meta.shape[0]
        for t in range(0,time):
            if t in list(labels.keys()):
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
        for t in range(maxTime,time,-1):
            if t in list(labels.keys()):
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

    def getLabel(self, time, track, labels):
        for label in list(labels[time].keys()):
            if labels[time][label] == set([track]):
                return label
        return False

    def getLabelT(self, track, labelsT):
        for label in list(labelsT.keys()):
            if labelsT[label] == set([track]):
                return label
        return False

    def insertAnnotationsToHypothesesGraph(self, traxelgraph, annotations,misdetectionLabel=-1):
        '''
        Add solution values to nodes and arcs from annotations.
        The resulting graph (=model) gets an additional property "value" that represents the number of objects inside a detection/arc
        Additionally a division indicator is saved in the node property "divisionValue".
        The link also gets a new attribute: the gap that is covered.
        E.g. 1, if consecutive timeframes, 2 if link skipping one timeframe.
        '''
        traxelToUuidMap, uuidToTraxelMap = traxelgraph.getMappingsBetweenUUIDsAndTraxels()

        # reset all values
        for n in traxelgraph._graph.nodes_iter():
            traxelgraph._graph.node[n]['value'] = 0
            traxelgraph._graph.node[n]['divisionValue'] = False

        for e in traxelgraph._graph.edges_iter():
            traxelgraph._graph.edge[e[0]][e[1]]['value'] = 0
            traxelgraph._graph.edge[e[0]][e[1]]['gap'] = 1 # only single step transitions supported in annotations

        labels = annotations['labels']
        divisions = annotations['divisions']

        for t in list(labels.keys()):
            for obj in labels[t]:
                trackSet = labels[t][obj]
                if (not -1 in trackSet) and str(obj) in list(traxelToUuidMap[str(t)].keys()):
                    traxelgraph._graph.node[(t,obj)]['value'] = len(trackSet)

        for t in list(labels.keys()):
            if t < max(list(labels.keys())):
                for source in list(labels[t].keys()):
                    if (misdetectionLabel not in labels[t][source]) and t+1 in list(labels.keys()):
                        for dest in list(labels[t+1].keys()):
                            if (misdetectionLabel not in labels[t+1][dest]):
                                intersectSet = labels[t][source].intersection(labels[t+1][dest])
                                lenIntersectSet = len(intersectSet)
                                assert ((t,source) in list(traxelgraph._graph.edge.keys()) and (t+1,dest) in list(traxelgraph._graph.edge[(t,source)].keys()),
                                        "Annotated arc that you are setting 'value' of is NOT in the hypotheses graph. " + \
                                        "Your two objects have either very dissimilar features or they are spatially distant. " + \
                                        "Increase maxNearestNeighbors in your project or force the addition of this arc by changing the code here :)" + \
                                        "source ---- dest "+str(source)+"--->"+str(dest)+"       : "+str(lenIntersectSet)+" , "+str(intersectSet))
                                if lenIntersectSet > 0:
                                    traxelgraph._graph.edge[(t,source)][(t+1,dest)]['value'] = lenIntersectSet

        for parentTrack in list(divisions.keys()):
            t = divisions[parentTrack][1]
            childrenTracks = divisions[parentTrack][0]
            parent = self.getLabelT(parentTrack,labels[t])
            for childTrack in childrenTracks:
                child = self.getLabelT(childTrack,labels[t+1])
                traxelgraph._graph.edge[(t,parent)][(t+1,child)]['value'] = 1
                traxelgraph._graph.edge[(t,parent)][(t+1,child)]['gap'] = 1
            traxelgraph._graph.node[(t,parent)]['divisionValue'] = True

        return traxelgraph
