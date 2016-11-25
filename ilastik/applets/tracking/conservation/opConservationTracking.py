import numpy as np
import os
import itertools
from lazyflow.graph import Operator, InputSlot, OutputSlot
from ilastik.utility.exportingOperator import ExportingOperator
from lazyflow.rtype import List
from lazyflow.stype import Opaque

from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.applets.tracking.base.trackingUtilities import relabel, highlightMergers
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key, OpRegionFeatures
from ilastik.applets.tracking.base.trackingUtilities import get_dict_value, get_events
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.operators.valueProviders import OpZeroDefault
from lazyflow.roi import sliceToRoi
from .opRelabeledMergerFeatureExtraction import OpRelabeledMergerFeatureExtraction

from functools import partial
from lazyflow.request import Request, RequestPool

import hytra
from hytra.core.ilastik_project_options import IlastikProjectOptions
from hytra.core.jsongraph import JsonTrackingGraph
from hytra.core.jsongraph import getMappingsBetweenUUIDsAndTraxels, getMergersDetectionsLinksDivisions, getMergersPerTimestep, getLinksPerTimestep, getDetectionsPerTimestep, getDivisionsPerTimestep
from hytra.core.ilastikhypothesesgraph import IlastikHypothesesGraph
from hytra.core.fieldofview import FieldOfView
from hytra.core.ilastikmergerresolver import IlastikMergerResolver
from hytra.core.probabilitygenerator import ProbabilityGenerator
from hytra.core.probabilitygenerator import Traxel

import dpct

import vigra

import logging
logger = logging.getLogger(__name__)

class OpConservationTracking(Operator, ExportingOperator):
    LabelImage = InputSlot()
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List)
    ObjectFeaturesWithDivFeatures = InputSlot(optional=True, stype=Opaque, rtype=List)
    ComputedFeatureNames = InputSlot(rtype=List, stype=Opaque)
    ComputedFeatureNamesWithDivFeatures = InputSlot(optional=True, rtype=List, stype=Opaque)
    EventsVector = InputSlot(value={})
    FilteredLabels = InputSlot(value={})
    RawImage = InputSlot()
    Parameters = InputSlot(value={})
 
    # for serialization
    InputHdf5 = InputSlot(optional=True)
    CleanBlocks = OutputSlot()
    AllBlocks = OutputSlot()
    OutputHdf5 = OutputSlot()
    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)
 
    Output = OutputSlot()
 
    # Use a slot for storing the export settings in the project file.
    ExportSettings = InputSlot()

    DivisionProbabilities = InputSlot(optional=True, stype=Opaque, rtype=List)
    DetectionProbabilities = InputSlot(stype=Opaque, rtype=List)
    NumLabels = InputSlot()

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

    hypotheses_graph = None
    mergerResolver = None

    def __init__(self, parent=None, graph=None):
        super(OpConservationTracking, self).__init__(parent=parent, graph=graph)

        self.mergers = []
        self.resolvedto = []

        self.track_id = None
        self.extra_track_ids = None
        self.divisions = None
        self.resolvedMergersDict = None

        self._opCache = OpCompressedCache(parent=self)
        self._opCache.InputHdf5.connect(self.InputHdf5)
        self._opCache.Input.connect(self.Output)
        self.CleanBlocks.connect(self._opCache.CleanBlocks)
        self.OutputHdf5.connect(self._opCache.OutputHdf5)
        self.CachedOutput.connect(self._opCache.Output)

        self.zeroProvider = OpZeroDefault(parent=self)
        self.zeroProvider.MetaInput.connect(self.LabelImage)

        # As soon as input data is available, check its constraints
        self.RawImage.notifyReady(self._checkConstraints)
        self.LabelImage.notifyReady(self._checkConstraints)

        self.export_progress_dialog = None
        self.ExportSettings.setValue( (None, None) )

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
        self.tracker = None
        self._ndim = 3        

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.LabelImage.meta)

        # cache our own output, don't propagate from internal operator
        chunks = list(self.LabelImage.meta.shape)
        # FIXME: assumes t,x,y,z,c
        chunks[0] = 1  # 't'        
        self._blockshape = tuple(chunks)
        self._opCache.BlockShape.setValue(self._blockshape)

        self.AllBlocks.meta.shape = (1,)
        self.AllBlocks.meta.dtype = object
        
        self.MergerOutput.meta.assignFrom(self.LabelImage.meta)
        self.RelabeledImage.meta.assignFrom(self.LabelImage.meta)
        self._ndim = 2 if self.LabelImage.meta.shape[3] == 1 else 3

        self._mergerOpCache.BlockShape.setValue( self._blockshape )
        self._relabeledOpCache.BlockShape.setValue( self._blockshape )
        
        frame_shape = (1,) + self.LabelImage.meta.shape[1:] # assumes t,x,y,z,c order
        assert frame_shape[-1] == 1
        self.MergerOutput.meta.ideal_blockshape = frame_shape
        self.RelabeledImage.meta.ideal_blockshape = frame_shape
        
    
    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            if not self.Parameters.ready():
                raise Exception("Parameter slot is not ready")
            parameters = self.Parameters.value           
            trange = list(range(roi.start[0], roi.stop[0]))
            
            original = np.zeros(result.shape, dtype=slot.meta.dtype)         
            result[:] =  self.LabelImage.get(roi).wait()

            for t in trange:
                if (self.mergerResolver 
                        and 'time_range' in parameters 
                        and t <= parameters['time_range'][-1] 
                        and t >= parameters['time_range'][0]):
                    self.mergerResolver.relabelMergers(result[t-roi.start[0],...,0], t)
                    result[t-roi.start[0],...,0] = self._labelLineageIds(result[t-roi.start[0],...,0], t)
                else:
                    result[t-roi.start[0],...,0] = self._labelLineageIds(result[t-roi.start[0],...,0], t)

            original[result != 0] = result[result != 0]
            result[:] = original
            
        elif slot is self.MergerOutput:
            parameters = self.Parameters.value
            trange = list(range(roi.start[0], roi.stop[0]))

            result[:] =  self.LabelImage.get(roi).wait()
   
            for t in trange:
                if (self.mergerResolver 
                        and self.resolvedMergersDict 
                        and t in self.resolvedMergersDict 
                        and 'time_range' in parameters 
                        and t <= parameters['time_range'][-1] 
                        and t >= parameters['time_range'][0]):
                    if 'withMergerResolution' in list(parameters.keys()) and parameters['withMergerResolution']:
                        self.mergerResolver.relabelMergers(result[t-roi.start[0],...,0], t)
                        result[t-roi.start[0],...,0] = self._labelLineageIds(result[t-roi.start[0],...,0], t, onlyMergers=True)
                    else:
                        result[t-roi.start[0],...,0] = highlightMergers(result[t-roi.start[0],...,0], self.mergers[t])
                else:
                    result[t-roi.start[0],...][:] = 0
            
        elif slot is self.RelabeledImage:
            parameters = self.Parameters.value
            trange = list(range(roi.start[0], roi.stop[0]))

            result[:] =  self.LabelImage.get(roi).wait()
            
            for t in trange:
                if (self.mergerResolver
                        and 'time_range' in parameters
                        and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0]
                        and 'withMergerResolution' in list(parameters.keys()) and parameters['withMergerResolution']):
                    self.mergerResolver.relabelMergers(result[t-roi.start[0],...,0], t)
                    
        elif slot == self.AllBlocks:
            # if nothing was computed, return empty list
            if not self.hypotheses_graph:
                result[0] = []
                return result

            all_block_rois = []
            shape = self.Output.meta.shape
            # assumes t,x,y,z,c
            slicing = [slice(None), ] * 5
            for t in range(shape[0]):
                slicing[0] = slice(t, t + 1)
                all_block_rois.append(sliceToRoi(slicing, shape))

            result[0] = all_block_rois
            return result

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.InputHdf5 or slot == self.MergerInputHdf5 or slot == self.RelabeledInputHdf5, "Invalid slot for setInSlot(): {}".format( slot.name )

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
            motionModelWeight=10.0,
            force_build_hypotheses_graph = False,
            max_nearest_neighbors = 2,
            withBatchProcessing = False,
            solverName="ILP"
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
        parameters['scales'] = [x_scale, y_scale, z_scale]
        parameters['time_range'] = [min(time_range), max(time_range)]
        parameters['x_range'] = x_range
        parameters['y_range'] = y_range
        parameters['z_range'] = z_range
        parameters['max_nearest_neighbors'] = max_nearest_neighbors

        # Set a size range with a minimum area equal to the max number of objects (since the GMM throws an error if we try to fit more gaussians than the number of pixels in the object)
        size_range = (max(maxObj, size_range[0]), size_range[1])
        parameters['size_range'] = size_range

        if cplex_timeout:
            parameters['cplex_timeout'] = cplex_timeout
        else:
            parameters['cplex_timeout'] = ''
            cplex_timeout = float(1e75)
        
        self.Parameters.setValue(parameters, check_changed=False)
        
        if withClassifierPrior:
            if not self.DetectionProbabilities.ready() or len(self.DetectionProbabilities([0]).wait()[0]) == 0:
                raise DatasetConstraintError('Tracking', 'Classifier not ready yet. Did you forget to train the Object Count Classifier?')
            if not self.NumLabels.ready() or self.NumLabels.value < (maxObj + 1):
                raise DatasetConstraintError('Tracking', 'The max. number of objects must be consistent with the number of labels given in Object Count Classification.\n' +\
                    'Check whether you have (i) the correct number of label names specified in Object Count Classification, and (ii) provided at least ' +\
                    'one training example for each class.')
            if len(self.DetectionProbabilities([0]).wait()[0][0]) < (maxObj + 1):
                raise DatasetConstraintError('Tracking', 'The max. number of objects must be consistent with the number of labels given in Object Count Classification.\n' +\
                    'Check whether you have (i) the correct number of label names specified in Object Count Classification, and (ii) provided at least ' +\
                    'one training example for each class.')
        
        traxelstore = self._generate_traxelstore(time_range, x_range, y_range, z_range,
                                                       size_range, x_scale, y_scale, z_scale, 
                                                       with_div=withDivisions,
                                                       with_classifier_prior=withClassifierPrior)
        
        def constructFov(shape, t0, t1, scale=[1, 1, 1]):
            [xshape, yshape, zshape] = shape
            [xscale, yscale, zscale] = scale
        
            fov = FieldOfView(t0, 0, 0, 0, t1, xscale * (xshape - 1), yscale * (yshape - 1),
                              zscale * (zshape - 1))
            return fov

        fieldOfView = constructFov((x_range[1], y_range[1], z_range[1]),
                                   0,
                                   time_range[-1]+1,
                                   [x_scale,
                                   y_scale,
                                   z_scale])

        hypotheses_graph = IlastikHypothesesGraph(
            probabilityGenerator=traxelstore,
            timeRange=(0,time_range[-1]+1),
            maxNumObjects=maxObj,
            numNearestNeighbors=max_nearest_neighbors,
            fieldOfView=fieldOfView,
            withDivisions=False,
            maxNeighborDistance=maxDist,
            divisionThreshold=0.1
        )

        if withTracklets:
            hypotheses_graph = hypotheses_graph.generateTrackletGraph()

        hypotheses_graph.insertEnergies()
        trackingGraph = hypotheses_graph.toTrackingGraph()
        trackingGraph.convexifyCosts()
        model = trackingGraph.model

        detectionWeight = 10.0 # FIXME: Should we store this weight in the parameters slot?
        weights = {'weights': [transWeight, detectionWeight, appearance_cost, disappearance_cost]}
        if withDivisions:
            weights = {'weights': [transWeight, detectionWeight, divWeight, appearance_cost, disappearance_cost]}
            
        result = dpct.trackFlowBased(model, weights)
        
        # Insert the solution into the hypotheses graph and from that deduce the lineages
        if hypotheses_graph:
            hypotheses_graph.insertSolution(result)
            
        # Merger resolution
        if withMergerResolution:
            logger.info("Resolving mergers.")
            
            originalGraph = hypotheses_graph.referenceTraxelGraph if withTracklets else hypotheses_graph
            
            pluginPath = os.path.join(os.path.dirname(os.path.abspath(hytra.__file__)), 'plugins')
            
            # Enable full graph computation for animal tracking workflow
            withFullGraph = False
            if 'withAnimalTracking' in parameters and parameters['withAnimalTracking']: # TODO: Setting this parameter outside of the track() function (on AnimalConservationTrackingWorkflow) is not desirable 
                withFullGraph = True
                logger.info("Computing full graph on merger resolver (Only enabled on animal tracking workflow)")
            
            self.mergerResolver = IlastikMergerResolver(originalGraph, pluginPaths=[pluginPath], withFullGraph=withFullGraph)
            
            # Check if graph contains mergers, otherwise skip merger resolving
            if not self.mergerResolver.mergerNum:
                logger.info("Graph contains no mergers. Skipping merger resolving.")
                self.mergerResolver = None
                self.resolvedMergersDict = {}
            else:        
                # Fit and refine merger nodes using a GMM 
                # It has to be done per time-step in order to aviod loading the whole video on RAM
                traxelIdPerTimestepToUniqueIdMap, uuidToTraxelMap = getMappingsBetweenUUIDsAndTraxels(model)
                timesteps = [int(t) for t in list(traxelIdPerTimestepToUniqueIdMap.keys())]
                timesteps.sort()
                
                timeIndex = self.LabelImage.meta.axistags.index('t')
                
                for timestep in timesteps:
                    roi = [slice(None) for i in range(len(self.LabelImage.meta.shape))]
                    roi[timeIndex] = slice(timestep, timestep+1)
                    roi = tuple(roi)
                    
                    labelImage = self.LabelImage[roi].wait()
                    
                    # Get coordinates for object IDs in label image. Used by GMM merger fit.
                    objectIds = vigra.analysis.unique(labelImage[0,...,0])
                    coordinatesForIds = {}
                    
                    pool = RequestPool()
                    for objectId in objectIds:
                        pool.add(Request(partial(self.mergerResolver.getCoordinatesForObjectId, coordinatesForIds, labelImage[0, ..., 0], objectId)))                   
                    pool.wait()                
                    
                    # Fit mergers and store fit info in nodes  
                    self.mergerResolver.fitAndRefineNodesForTimestep(coordinatesForIds, timestep)
                    
                # Compute object features, re-run flow solver, update model and result, and get merger dictionary
                self.resolvedMergersDict = self.mergerResolver.run()
                
            self.MergerOutput.setDirty()

        logger.info("Computing hypotheses graph lineages")
        hypotheses_graph.computeLineage()

        # Uncomment to export a hypothese graph diagram
        #logger.info("Exporting hypotheses graph diagram")
        #from hytra.util.hypothesesgraphdiagram import HypothesesGraphDiagram
        #hgv = HypothesesGraphDiagram(hypotheses_graph._graph, timeRange=(0, 10), fileName='HypothesesGraph.png' )
                
        self.hypotheses_graph = hypotheses_graph.referenceTraxelGraph if withTracklets else hypotheses_graph

        # Refresh (execute) output slots
        self.Output.setDirty()
        self.RelabeledImage.setDirty()

        # Get events vector (only used when saving old h5 events file)
        events = self._getEventsVector(result, model)
        self.EventsVector.setValue(events, check_changed=False)
        
        if not withBatchProcessing:
            merger_layer_idx = self.parent.parent.trackingApplet._gui.currentGui().layerstack.findMatchingIndex(lambda x: x.name == "Merger")
            tracking_layer_idx = self.parent.parent.trackingApplet._gui.currentGui().layerstack.findMatchingIndex(lambda x: x.name == "Tracking")
            if 'withMergerResolution' in list(parameters.keys()) and not parameters['withMergerResolution']:
                self.parent.parent.trackingApplet._gui.currentGui().layerstack[merger_layer_idx].colorTable = \
                    self.parent.parent.trackingApplet._gui.currentGui().merger_colortable
            else:
                self.parent.parent.trackingApplet._gui.currentGui().layerstack[merger_layer_idx].colorTable = \
                    self.parent.parent.trackingApplet._gui.currentGui().tracking_colortable

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)
        elif inputSlot is self.EventsVector:
            pass
        elif inputSlot == self.NumLabels:
            if self.parent.parent.trackingApplet._gui \
                    and self.parent.parent.trackingApplet._gui.currentGui() \
                    and self.NumLabels.ready() \
                    and self.NumLabels.value > 1:
                self.parent.parent.trackingApplet._gui.currentGui()._drawer.maxObjectsBox.setValue(self.NumLabels.value-1)

    def _getEventsVector(self, result, model):        
        traxelIdPerTimestepToUniqueIdMap, uuidToTraxelMap = getMappingsBetweenUUIDsAndTraxels(model)
        timesteps = [t for t in list(traxelIdPerTimestepToUniqueIdMap.keys())]
        
        mergers, detections, links, divisions = getMergersDetectionsLinksDivisions(result, uuidToTraxelMap)
        
        # Group by timestep for event creation
        mergersPerTimestep = getMergersPerTimestep(mergers, timesteps)
        linksPerTimestep = getLinksPerTimestep(links, timesteps)
        detectionsPerTimestep = getDetectionsPerTimestep(detections, timesteps)
        divisionsPerTimestep = getDivisionsPerTimestep(divisions, linksPerTimestep, timesteps)

        # Populate events dictionary
        events = {}
        
        # Save mergers, links, detections, and divisions
        for timestep in list(traxelIdPerTimestepToUniqueIdMap.keys()):
            # We need to add an extra column with zeros in order to be backward compatible with the older version
            def stackExtraColumnWithZeros(array):
                return np.hstack((array, np.zeros((array.shape[0], 1), dtype=array.dtype)))
            
            dis = []
            app = []
            div = []
            mov = []
            mer = []
            mul = []
    
            dis = np.asarray(dis)
            app = np.asarray(app)
            div = np.asarray([[k, v[0], v[1]] for k,v in divisionsPerTimestep[timestep].items()])
            mov = np.asarray(linksPerTimestep[timestep])
            mer = np.asarray([[k,v] for k,v in mergersPerTimestep[timestep].items()])
            mul = np.asarray(mul)
            
            events[str(timestep)] = {}
         
            if len(dis) > 0:
                events[str(timestep)]['dis'] = dis
            if len(app) > 0:
                events[str(timestep)]['app'] = app
            if len(div) > 0:
                events[str(timestep)]['div'] = div
            if len(mov) > 0:
                events[str(timestep)]['mov'] = mov
            if len(mer) > 0:
                events[str(timestep)]['mer'] = mer
            if len(mul) > 0:
                events[str(timestep)]['mul'] = mul

        # Write merger results dictionary
        if self.resolvedMergersDict:
            for timestep, results in list(self.resolvedMergersDict.items()):
                mergerRes = {}
                for key, result in list(results.items()):
                    mergerRes[key] = result
                    
                events[str(timestep)]['res'] = mergerRes
        else:
            logger.info("Resolved Merger Dictionary not available. Please click on the Track button.")
                
        return events

    def _labelLineageIds(self, volume, time, onlyMergers=False):
        """
        Label the every object in the volume for the given time frame by the lineage ID it belongs to.
        If onlyMergers is True, then only those segments that were resolved from a merger are shown, everything else set to zero.

        :return: the relabeled volume, where 0 means background, 1 means false detection, and all higher numbers indicate lineages
        """
        if self.hypotheses_graph:
            indexMapping = np.zeros(np.amax(volume) + 1, dtype=volume.dtype)
            
            labels = np.unique(volume)
            if onlyMergers:
                # restrict the labels to only those that came out of a merger
                assert(self.resolvedMergersDict is not None)
                values = []
                if time in self.resolvedMergersDict:
                    values = list(self.resolvedMergersDict[time].values())
                labels = [l for l in labels if l in itertools.chain(*values)]
            for label in labels:
                if label > 0 and self.hypotheses_graph.hasNode((time,label)):
                    lineage_id = self.hypotheses_graph.getLineageId(time, label)
                    if lineage_id is None:
                        lineage_id = 1
                    indexMapping[label] = lineage_id
                
            return indexMapping[volume]
        else:
            return volume        
    
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

    def _do_export_impl(self, settings, selected_features, progress_slot, object_feature_slot, label_image_slot, lane_index, filename_suffix=""):
        from ilastik.utility.exportFile import objects_per_frame, ExportFile, ilastik_ids, Mode, Default, \
            flatten_dict, division_flatten_dict

        if not self.hypotheses_graph:
            raise DatasetConstraintError('Tracking', 'Tracking solution not ready: Did you forgot to press the Track button?')

        obj_count = list(objects_per_frame(label_image_slot))        
        object_ids_generator = ilastik_ids(obj_count)
         
        object_ids = [] 
        lineage_ids = []
        track_ids = []
          
        for (time, object_id) in object_ids_generator: 
            object_ids.append((time, object_id))
            
            if self.hypotheses_graph.hasNode((time,object_id)):        
                lineage_id = self.hypotheses_graph.getLineageId(time, object_id)
                if lineage_id:    
                    lineage_ids.append(lineage_id)
                else:
                    logger.debug("Empty lineage ID for node ({},{})".format(time, object_id))
                    lineage_ids.append(0)
                    
                track_id = self.hypotheses_graph.getTrackId(time, object_id)    
                if track_id:
                    track_ids.append(track_id)
                else:
                    track_ids.append(0) 
            else:
                lineage_ids.append(0)
                track_ids.append(0)
                

        selected_features = list(selected_features)
        with_divisions = self.Parameters.value["withDivisions"] if self.Parameters.ready() else False

        file_path = settings["file path"]
        if filename_suffix:
            path, ext = os.path.splitext(file_path)
            file_path = path + "-" + filename_suffix + ext

        export_file = ExportFile(file_path)
        export_file.ExportProgress.subscribe(progress_slot)
        export_file.InsertionProgress.subscribe(progress_slot)

        export_file.add_columns("table", list(range(sum(obj_count))), Mode.List, Default.KnimeId)
        export_file.add_columns("table", object_ids, Mode.List, Default.IlastikId)
        export_file.add_columns("table", lineage_ids, Mode.List, Default.Lineage)
        export_file.add_columns("table", track_ids, Mode.List, Default.TrackId)

        export_file.add_columns("table", object_feature_slot, Mode.IlastikFeatureTable,
                                {"selection": selected_features})

        if with_divisions:
            # Export divisions here
            # export_file.add_columns("divisions", divisions, Mode.List, Default.DivisionNames)
            pass

        if settings["file type"] == "h5":
            export_file.add_rois(Default.LabelRoiPath, label_image_slot, "table", settings["margin"], "labeling")
            if settings["include raw"]:
                export_file.add_image(Default.RawPath, self.RawImage)
            else:
                export_file.add_rois(Default.RawRoiPath, self.RawImage, "table", settings["margin"])
        export_file.write_all(settings["file type"], settings["compression"])

        export_file.ExportProgress.unsubscribe(progress_slot)
        export_file.InsertionProgress.unsubscribe(progress_slot)

    # Override functions ExportingOperator mixin
    def configure_table_export_settings(self, settings, selected_features):
        self.ExportSettings.setValue( (settings, selected_features) )

    def get_table_export_settings(self):
        if self.ExportSettings.ready():
            (settings, selected_features) = self.ExportSettings.value
            return (settings, selected_features)
        else:
            return None, None

    def _checkConstraints(self, *args):
        if self.RawImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            if rawTaggedShape['t'] < 2:
                raise DatasetConstraintError(
                    "Tracking",
                    "For tracking, the dataset must have a time axis with at least 2 images.   " \
                    "Please load time-series data instead. See user documentation for details.")

        if self.LabelImage.ready():
            segmentationTaggedShape = self.LabelImage.meta.getTaggedShape()
            if segmentationTaggedShape['t'] < 2:
                raise DatasetConstraintError(
                    "Tracking",
                    "For tracking, the dataset must have a time axis with at least 2 images.   " \
                    "Please load time-series data instead. See user documentation for details.")

        if self.RawImage.ready() and self.LabelImage.ready():
            rawTaggedShape['c'] = None
            segmentationTaggedShape['c'] = None
            if dict(rawTaggedShape) != dict(segmentationTaggedShape):
                raise DatasetConstraintError("Tracking",
                                             "For tracking, the raw data and the prediction maps must contain the same " \
                                             "number of timesteps and the same shape.   " \
                                             "Your raw image has a shape of (t, x, y, z, c) = {}, whereas your prediction image has a " \
                                             "shape of (t, x, y, z, c) = {}" \
                                             .format(self.RawImage.meta.shape, self.BinaryImage.meta.shape))

    def _generate_traxelstore(self,
                              time_range,
                              x_range,
                              y_range,
                              z_range,
                              size_range,
                              x_scale=1.0,
                              y_scale=1.0,
                              z_scale=1.0,
                              with_div=False,
                              with_local_centers=False,
                              with_classifier_prior=False):

        logger.info("generating traxels")
        traxelstore = ProbabilityGenerator()
        
        logger.info("fetching region features and division probabilities")
        feats = self.ObjectFeatures(time_range).wait()
        
        if with_div:
            if not self.DivisionProbabilities.ready() or len(self.DivisionProbabilities([0]).wait()[0]) == 0:
                msgStr = "\nDivision classifier has not been trained! " + \
                         "Uncheck divisible objects if your objects don't divide or " + \
                         "go back to the Division Detection applet and train it."
                raise DatasetConstraintError ("Tracking",msgStr)
            divProbs = self.DivisionProbabilities(time_range).wait()

        if with_local_centers:
            localCenters = self.RegionLocalCenters(time_range).wait()

        if with_classifier_prior:
            if not self.DetectionProbabilities.ready() or len(self.DetectionProbabilities([0]).wait()[0]) == 0:
                msgStr = "\nObject count classifier has not been trained! " + \
                         "Go back to the Object Count Classification applet and train it."
                raise DatasetConstraintError ("Tracking",msgStr)
            detProbs = self.DetectionProbabilities(time_range).wait()

        logger.info("filling traxelstore")

        filtered_labels = {}
        total_count = 0
        empty_frame = False

        for t in list(feats.keys()):
            rc = feats[t][default_features_key]['RegionCenter']
            lower = feats[t][default_features_key]['Coord<Minimum>']
            upper = feats[t][default_features_key]['Coord<Maximum>']
            if rc.size:
                rc = rc[1:, ...]
                lower = lower[1:, ...]
                upper = upper[1:, ...]

            ct = feats[t][default_features_key]['Count']
            if ct.size:
                ct = ct[1:, ...]

            logger.debug("at timestep {}, {} traxels found".format(t, rc.shape[0]))
            count = 0
            filtered_labels_at = []
            for idx in range(rc.shape[0]):
                traxel = Traxel()
                
                # for 2d data, set z-coordinate to 0:
                if len(rc[idx]) == 2:
                    x, y = rc[idx]
                    z = 0
                elif len(rc[idx]) == 3:
                    x, y, z = rc[idx]
                else:
                    raise DatasetConstraintError ("Tracking", "The RegionCenter feature must have dimensionality 2 or 3.")
                size = ct[idx]
                if (x < x_range[0] or x >= x_range[1] or
                            y < y_range[0] or y >= y_range[1] or
                            z < z_range[0] or z >= z_range[1] or
                            size < size_range[0] or size >= size_range[1]):
                    filtered_labels_at.append(int(idx + 1))
                    continue
                else:
                    count += 1
                
                traxel.Id = int(idx + 1)
                traxel.Timestep = int(t) 
                traxel.set_x_scale(x_scale)
                traxel.set_y_scale(y_scale)
                traxel.set_z_scale(z_scale)

                # Expects always 3 coordinates, z=0 for 2d data
                traxel.add_feature_array("com", 3)
                for i, v in enumerate([x, y, z]):
                    traxel.set_feature_value('com', i, float(v))

                traxel.add_feature_array("CoordMinimum", 3)
                for i, v in enumerate(lower[idx]):
                    traxel.set_feature_value("CoordMinimum", i, float(v))
                traxel.add_feature_array("CoordMaximum", 3)
                for i, v in enumerate(upper[idx]):
                    traxel.set_feature_value("CoordMaximum", i, float(v))

                if with_div:
                    traxel.add_feature_array("divProb", 1)
                    # idx+1 because rc and ct start from 1, divProbs starts from 0
                    traxel.set_feature_value("divProb", 0, float(divProbs[t][idx + 1][1]))

                if with_classifier_prior:
                    traxel.add_feature_array("detProb", len(detProbs[t][idx + 1]))
                    for i, v in enumerate(detProbs[t][idx + 1]):
                        val = float(v)
                        if val < 0.0000001:
                            val = 0.0000001
                        if val > 0.99999999:
                            val = 0.99999999
                        traxel.set_feature_value("detProb", i, float(val))

                # FIXME: check whether it is 2d or 3d data!
                if with_local_centers:                   
                    traxel.add_feature_array("localCentersX", len(localCenters[t][idx + 1]))
                    traxel.add_feature_array("localCentersY", len(localCenters[t][idx + 1]))
                    traxel.add_feature_array("localCentersZ", len(localCenters[t][idx + 1]))
                    
                    for i, v in enumerate(localCenters[t][idx + 1]):                        
                        traxel.set_feature_value("localCentersX", i, float(v[0]))
                        traxel.set_feature_value("localCentersY", i, float(v[1]))
                        traxel.set_feature_value("localCentersZ", i, float(v[2]))
                
                traxel.add_feature_array("count", 1)
                traxel.set_feature_value("count", 0, float(size))

                # Add traxel to traxelstore after checking position, time, and size ranges
                if (x < x_range[0] or x >= x_range[1] or
                            y < y_range[0] or y > y_range[1] or
                            z < z_range[0] or z > z_range[1] or
                            size < size_range[0] or size > size_range[1]):
                    logger.info("Omitting traxel with ID: {}".format(traxel.Id))
                else:
                    traxelstore.TraxelsPerFrame.setdefault(int(t), {})[int(idx + 1)] = traxel

            if len(filtered_labels_at) > 0:
                filtered_labels[str(int(t) - time_range[0])] = filtered_labels_at
                
            logger.debug("at timestep {}, {} traxels passed filter".format(t, count))

            if count == 0:
                empty_frame = True
                logger.info('Found empty frames')

            total_count += count

        self.FilteredLabels.setValue(filtered_labels, check_changed=True)

        return traxelstore

    def save_export_progress_dialog(self, dialog):
        """
        Implements ExportOperator.save_export_progress_dialog
        Without this the progress dialog would be hidden after the export
        :param dialog: the ProgressDialog to save
        """
        self.export_progress_dialog = dialog
        