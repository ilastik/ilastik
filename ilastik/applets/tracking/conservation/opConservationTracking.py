import numpy as np
import os
import itertools
from lazyflow.graph import Operator, InputSlot, OutputSlot
from ilastik.utility.exportingOperator import ExportingOperator
from lazyflow.rtype import List
from lazyflow.stype import Opaque

from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key, OpRegionFeatures
from ilastik.applets.tracking.base.trackingUtilities import get_dict_value, get_events
from lazyflow.operators import OpBlockedArrayCache
from lazyflow.operators.valueProviders import OpZeroDefault
from lazyflow.roi import sliceToRoi
from opRelabeledMergerFeatureExtraction import OpRelabeledMergerFeatureExtraction

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
from hytra.pluginsystem.plugin_manager import TrackingPluginManager

import vigra

import logging
logger = logging.getLogger(__name__)

import dpct
try:
    import multiHypoTracking_with_cplex as mht
except ImportError:
    try:
        import multiHypoTracking_with_gurobi as mht
    except ImportError:
        logger.warning("Could not find any ILP solver")

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
    HypothesesGraph = InputSlot(value={})
    ResolvedMergers = InputSlot(value={})
 
    # for serialization
    CleanBlocks = OutputSlot()
    AllBlocks = OutputSlot()
    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)
 
    Output = OutputSlot() # Volume relabelled with lineage IDs
 
    # Use a slot for storing the export settings in the project file.
    ExportSettings = InputSlot()

    DivisionProbabilities = InputSlot(optional=True, stype=Opaque, rtype=List)
    DetectionProbabilities = InputSlot(stype=Opaque, rtype=List)
    NumLabels = InputSlot()

    # compressed cache for merger output
    MergerCleanBlocks = OutputSlot()
    MergerCachedOutput = OutputSlot() # For the GUI (blockwise access)
    MergerOutput = OutputSlot() # Volume showing only merger IDs

    RelabeledCleanBlocks = OutputSlot()
    RelabeledCachedOutput = OutputSlot() # For the GUI (blockwise access)
    RelabeledImage = OutputSlot() # Volume showing object IDs

    def __init__(self, parent=None, graph=None):
        super(OpConservationTracking, self).__init__(parent=parent, graph=graph)

        self._opCache = OpBlockedArrayCache(parent=self)
        self._opCache.name = "OpConservationTracking._opCache"
        self._opCache.CompressionEnabled.setValue(True)
        self._opCache.Input.connect(self.Output)
        self.CleanBlocks.connect(self._opCache.CleanBlocks)
        self.CachedOutput.connect(self._opCache.Output)

        self.zeroProvider = OpZeroDefault(parent=self)
        self.zeroProvider.MetaInput.connect(self.LabelImage)

        # As soon as input data is available, check its constraints
        self.RawImage.notifyReady(self._checkConstraints)
        self.LabelImage.notifyReady(self._checkConstraints)

        self.export_progress_dialog = None
        self.ExportSettings.setValue( (None, None) )

        self._mergerOpCache = OpBlockedArrayCache(parent=self)
        self._mergerOpCache.name = "OpConservationTracking._mergerOpCache"
        self._mergerOpCache.CompressionEnabled.setValue(True)
        self._mergerOpCache.Input.connect(self.MergerOutput)
        self.MergerCleanBlocks.connect(self._mergerOpCache.CleanBlocks)
        self.MergerCachedOutput.connect(self._mergerOpCache.Output)

        self._relabeledOpCache = OpBlockedArrayCache(parent=self)
        self._relabeledOpCache.name = "OpConservationTracking._mergerOpCache"
        self._relabeledOpCache.CompressionEnabled.setValue(True)
        self._relabeledOpCache.Input.connect(self.RelabeledImage)
        self.RelabeledCleanBlocks.connect(self._relabeledOpCache.CleanBlocks)
        self.RelabeledCachedOutput.connect(self._relabeledOpCache.Output)
        
        # Merger resolver plugin manager (contains GMM fit routine)
        self.pluginPaths = [os.path.join(os.path.dirname(os.path.abspath(hytra.__file__)), 'plugins')]
        pluginManager = TrackingPluginManager(verbose=False, pluginPaths=self.pluginPaths)
        self.mergerResolverPlugin = pluginManager.getMergerResolver()       

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.LabelImage.meta)

        # cache our own output, don't propagate from internal operator
        chunks = list(self.LabelImage.meta.shape)
        # FIXME: assumes t,x,y,z,c
        chunks[0] = 1  # 't'        
        self._blockshape = tuple(chunks)
        self._opCache.outerBlockShape.setValue(self._blockshape)

        self.AllBlocks.meta.shape = (1,)
        self.AllBlocks.meta.dtype = object
        
        self.MergerOutput.meta.assignFrom(self.LabelImage.meta)
        self.RelabeledImage.meta.assignFrom(self.LabelImage.meta)

        self._mergerOpCache.outerBlockShape.setValue( self._blockshape )
        self._relabeledOpCache.outerBlockShape.setValue( self._blockshape )
        
        frame_shape = (1,) + self.LabelImage.meta.shape[1:] # assumes t,x,y,z,c order
        assert frame_shape[-1] == 1
        self.MergerOutput.meta.ideal_blockshape = frame_shape
        self.RelabeledImage.meta.ideal_blockshape = frame_shape
          
    def execute(self, slot, subindex, roi, result):
        # Output showing lineage IDs
        if slot is self.Output:
            if not self.Parameters.ready():
                raise Exception("Parameter slot is not ready")
            parameters = self.Parameters.value
            resolvedMergers = self.ResolvedMergers.value
            
            # Assume [t,x,y,z,c] order           
            trange = range(roi.start[0], roi.stop[0])
            offset = roi.start[1:-1]
       
            result[:] =  self.LabelImage.get(roi).wait()

            for t in trange:
                if 'time_range' in parameters and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0]:
                    if resolvedMergers:
                        self._labelMergers(result[t-roi.start[0],...,0], t, offset)
                    result[t-roi.start[0],...,0] = self._labelLineageIds(result[t-roi.start[0],...,0], t)
                else:
                    result[t-roi.start[0],...][:] = 0
        
        # Output showing mergers only    
        elif slot is self.MergerOutput:
            parameters = self.Parameters.value
            resolvedMergers = self.ResolvedMergers.value
            
            # Assume [t,x,y,z,c] order
            trange = range(roi.start[0], roi.stop[0])
            offset = roi.start[1:-1]

            result[:] =  self.LabelImage.get(roi).wait()
   
            for t in trange:
                if 'time_range' in parameters and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0]:
                    if resolvedMergers:
                        self._labelMergers(result[t-roi.start[0],...,0], t, offset)   
                    result[t-roi.start[0],...,0] = self._labelLineageIds(result[t-roi.start[0],...,0], t, onlyMergers=True)
                else:
                    result[t-roi.start[0],...][:] = 0

        # Output showing object Ids (before lineage IDs are assigned)   
        elif slot is self.RelabeledImage:
            parameters = self.Parameters.value
            resolvedMergers = self.ResolvedMergers.value
            
            # Assume [t,x,y,z,c] order
            trange = range(roi.start[0], roi.stop[0])
            offset = roi.start[1:-1] 

            result[:] =  self.LabelImage.get(roi).wait()
            
            for t in trange:
                if resolvedMergers and 'time_range' in parameters and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0]:
                    self._labelMergers(result[t-roi.start[0],...,0], t, offset)
        
        # Cache blocks            
        elif slot == self.AllBlocks:
            # if nothing was computed, return empty list
            if not self.HypothesesGraph.value:
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
    
    def _createHypothesesGraph(self):
        '''
        Construct a hypotheses graph given the current settings in the parameters slot
        '''
        parameters = self.Parameters.value
        time_range = range(parameters['time_range'][0],parameters['time_range'][1] + 1)
        x_range = parameters['x_range']
        y_range = parameters['y_range']
        z_range = parameters['z_range']
        size_range = parameters['size_range']
        scales = parameters['scales']
        withDivisions = parameters['withDivisions']
        withClassifierPrior = parameters['withClassifierPrior']
        maxDist = parameters['maxDist']
        maxObj = parameters['maxObj']
        divThreshold = parameters['divThreshold']
        max_nearest_neighbors = parameters['max_nearest_neighbors']

        traxelstore = self._generate_traxelstore(time_range, x_range, y_range, z_range,
                                                       size_range, scales[0], scales[1], scales[2], 
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
                                   scales)

        hypothesesGraph = IlastikHypothesesGraph(
            probabilityGenerator=traxelstore,
            timeRange=(0,time_range[-1]+1),
            maxNumObjects=maxObj,
            numNearestNeighbors=max_nearest_neighbors,
            fieldOfView=fieldOfView,
            withDivisions=withDivisions,
            maxNeighborDistance=maxDist,
            divisionThreshold=divThreshold
        )
        return hypothesesGraph
    
    def _resolveMergers(self, hypothesesGraph, model):
        '''
        run merger resolution on the hypotheses graph which contains the current solution
        '''
        logger.info("Resolving mergers.")
                
        parameters = self.Parameters.value
        withTracklets = parameters['withTracklets']
        originalGraph = hypothesesGraph.referenceTraxelGraph if withTracklets else hypothesesGraph
        resolvedMergersDict = {}
        
        # Enable full graph computation for animal tracking workflow
        withFullGraph = False
        if 'withAnimalTracking' in parameters and parameters['withAnimalTracking']: # TODO: Setting this parameter outside of the track() function (on AnimalConservationTrackingWorkflow) is not desirable 
            withFullGraph = True
            logger.info("Computing full graph on merger resolver (Only enabled on animal tracking workflow)")
        
        mergerResolver = IlastikMergerResolver(originalGraph, pluginPaths=self.pluginPaths, withFullGraph=withFullGraph)
        
        # Check if graph contains mergers, otherwise skip merger resolving
        if not mergerResolver.mergerNum:
            logger.info("Graph contains no mergers. Skipping merger resolving.")
        else:        
            # Fit and refine merger nodes using a GMM 
            # It has to be done per time-step in order to aviod loading the whole video on RAM
            traxelIdPerTimestepToUniqueIdMap, uuidToTraxelMap = getMappingsBetweenUUIDsAndTraxels(model)
            timesteps = [int(t) for t in traxelIdPerTimestepToUniqueIdMap.keys()]
            timesteps.sort()
            
            timeIndex = self.LabelImage.meta.axistags.index('t')
            
            for timestep in timesteps:
                roi = [slice(None) for i in range(len(self.LabelImage.meta.shape))]
                roi[timeIndex] = slice(timestep, timestep+1)
                roi = tuple(roi)
                
                labelImage = self.LabelImage[roi].wait()
                
                # Get coordinates for object IDs in label image. Used by GMM merger fit.
                objectIds = vigra.analysis.unique(labelImage[0,...,0])
                maxObjectId = max(objectIds)
                
                coordinatesForIds = {}
                
                pool = RequestPool()
                for objectId in objectIds:
                    pool.add(Request(partial(mergerResolver.getCoordinatesForObjectId, coordinatesForIds, labelImage[0, ..., 0], timestep, objectId)))                 

                # Run requests to get object ID coordinates
                pool.wait()              
                
                # Fit mergers and store fit info in nodes  
                if coordinatesForIds:
                    mergerResolver.fitAndRefineNodesForTimestep(coordinatesForIds, maxObjectId, timestep)   
                
            # Compute object features, re-run flow solver, update model and result, and get merger dictionary
            resolvedMergersDict = mergerResolver.run()
        return resolvedMergersDict

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
            motionModelWeight=10.0,
            force_build_hypotheses_graph = False,
            max_nearest_neighbors = 2,
            withBatchProcessing = False,
            solverName="Flow-based"
            ):
        """
        Main conservation tracking function. Runs tracking solver, generates hypotheses graph, and resolves mergers.
        """
        
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
        parameters['scales'] = [x_scale, y_scale, z_scale]
        parameters['time_range'] = [min(time_range), max(time_range)]
        parameters['x_range'] = x_range
        parameters['y_range'] = y_range
        parameters['z_range'] = z_range
        parameters['max_nearest_neighbors'] = max_nearest_neighbors
        parameters['solver'] = str(solverName)

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
        
        hypothesesGraph = self._createHypothesesGraph()

        if withTracklets:
            hypothesesGraph = hypothesesGraph.generateTrackletGraph()

        hypothesesGraph.insertEnergies()
        trackingGraph = hypothesesGraph.toTrackingGraph()
        trackingGraph.convexifyCosts()
        model = trackingGraph.model

        weights = {u'weights': [transWeight, detWeight, appearance_cost, disappearance_cost]}
        if withDivisions:
            weights = {u'weights': [transWeight, detWeight, divWeight, appearance_cost, disappearance_cost]}

        if solverName == 'Flow-based' and dpct:
            result = dpct.trackFlowBased(model, weights)
        elif solverName == 'ILP' and mht:
            result = mht.track(model, weights)
        else:
            raise ValueError("Invalid tracking solver selected")
        
        # Insert the solution into the hypotheses graph and from that deduce the lineages
        if hypothesesGraph:
            hypothesesGraph.insertSolution(result)
            
        # Merger resolution
        resolvedMergersDict = {}
        if withMergerResolution:
            resolvedMergersDict = self._resolveMergers(hypothesesGraph, model)
        
        # Set value of resolved mergers slot (Should be empty if mergers are disabled)         
        self.ResolvedMergers.setValue(resolvedMergersDict, check_changed=False)
                
        # Computing tracking lineage IDs from within Hytra
        logger.info("Computing hypotheses graph lineages")
        hypothesesGraph.computeLineage()

        # Uncomment to export a hypothese graph diagram
        #logger.info("Exporting hypotheses graph diagram")
        #from hytra.util.hypothesesgraphdiagram import HypothesesGraphDiagram
        #hgv = HypothesesGraphDiagram(hypothesesGraph._graph, timeRange=(0, 10), fileName='HypothesesGraph.png' )
                
        # Set value of hypotheses grap slot (use referenceTraxelGraph if using tracklets)
        hypothesesGraph = hypothesesGraph.referenceTraxelGraph if withTracklets else hypothesesGraph
        self.HypothesesGraph.setValue(hypothesesGraph, check_changed=False)

        # Set all the output slots dirty (See execute() function)
        self.Output.setDirty()
        self.MergerOutput.setDirty()
        self.RelabeledImage.setDirty()

        # Get events vector (only used when saving old h5 events file)
        events = self._getEventsVector(result, model)
        self.EventsVector.setValue(events, check_changed=False)

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)
        elif inputSlot is self.EventsVector:
            pass
        elif inputSlot is self.HypothesesGraph:
            pass
        elif inputSlot is self.ResolvedMergers:
            pass
        elif inputSlot == self.NumLabels:
            if self.parent.parent.trackingApplet._gui \
                    and self.parent.parent.trackingApplet._gui.currentGui() \
                    and self.NumLabels.ready() \
                    and self.NumLabels.value > 1:
                self.parent.parent.trackingApplet._gui.currentGui()._drawer.maxObjectsBox.setValue(self.NumLabels.value-1)

    def _getEventsVector(self, result, model):        
        traxelIdPerTimestepToUniqueIdMap, uuidToTraxelMap = getMappingsBetweenUUIDsAndTraxels(model)
        timesteps = [t for t in traxelIdPerTimestepToUniqueIdMap.keys()]
        
        mergers, detections, links, divisions = getMergersDetectionsLinksDivisions(result, uuidToTraxelMap)
        
        # Group by timestep for event creation
        mergersPerTimestep = getMergersPerTimestep(mergers, timesteps)
        linksPerTimestep = getLinksPerTimestep(links, timesteps)
        detectionsPerTimestep = getDetectionsPerTimestep(detections, timesteps)
        divisionsPerTimestep = getDivisionsPerTimestep(divisions, linksPerTimestep, timesteps)

        # Populate events dictionary
        events = {}
        
        # Save mergers, links, detections, and divisions
        for timestep in traxelIdPerTimestepToUniqueIdMap.keys():
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
            div = np.asarray([[k, v[0], v[1]] for k,v in divisionsPerTimestep[timestep].iteritems()])
            mov = np.asarray(linksPerTimestep[timestep])
            mer = np.asarray([[k,v] for k,v in mergersPerTimestep[timestep].iteritems()])
            mul = np.asarray(mul)
            
            events[timestep] = {}
         
            if len(dis) > 0:
                events[timestep]['dis'] = dis
            if len(app) > 0:
                events[timestep]['app'] = app
            if len(div) > 0:
                events[timestep]['div'] = div
            if len(mov) > 0:
                events[timestep]['mov'] = mov
            if len(mer) > 0:
                events[timestep]['mer'] = mer
            if len(mul) > 0:
                events[timestep]['mul'] = mul

            # Write merger results dictionary
            resolvedMergersDict = self.ResolvedMergers.value
            
            if resolvedMergersDict:
                mergerRes = {}
                
                for idx in mergersPerTimestep[timestep]:
                    mergerRes[idx] = resolvedMergersDict[int(timestep)][idx]['newIds']
                    
                events[timestep]['res'] = mergerRes
                
        else:
            logger.info("Resolved Merger Dictionary not available. Please click on the Track button.")
                
        return events

    def _labelMergers(self, volume, time, offset):
        """
        Label volume mergers with correspoding IDs, using the plugin GMM fit
        """
        resolvedMergersDict = self.ResolvedMergers.value
        
        if time not in resolvedMergersDict:
            return volume
        
        idxs = vigra.analysis.unique(volume)
        
        for idx in idxs: 
            if idx in resolvedMergersDict[time]:
                fits = resolvedMergersDict[time][idx]['fits']
                newIds = resolvedMergersDict[time][idx]['newIds']
                self.mergerResolverPlugin.updateLabelImage(volume, idx, fits, newIds, offset=offset)
        
        return volume               

    def _labelLineageIds(self, volume, time, onlyMergers=False):
        """
        Label the every object in the volume for the given time frame by the lineage ID it belongs to.
        If onlyMergers is True, then only those segments that were resolved from a merger are shown, everything else set to zero.

        :return: the relabeled volume, where 0 means background, 1 means false detection, and all higher numbers indicate lineages
        """
        hypothesesGraph = self.HypothesesGraph.value
        
        if not hypothesesGraph:
            return np.zeros_like(volume) 
        
        resolvedMergersDict = self.ResolvedMergers.value

        indexMapping = np.zeros(np.amax(volume) + 1, dtype=volume.dtype)
        
        idxs = vigra.analysis.unique(volume)
        
        # Reduce labels to the ones that contain mergers
        if onlyMergers:
            if resolvedMergersDict:
                if time not in resolvedMergersDict:
                    idxs = []
                else:
                    newIds = [newId for _, nodeDict in resolvedMergersDict[time].items() for newId in nodeDict['newIds']]
                    idxs = [id for id in idxs if id in newIds]
            else:
                idxs = [idx for idx in idxs if idx > 0 and hypothesesGraph.hasNode((time,idx)) and hypothesesGraph._graph.node[(time,idx)]['value'] > 1]

        # Map labels to corresponding lineage IDs
        for idx in idxs:
            if idx > 0 and hypothesesGraph.hasNode((time,idx)):
                lineage_id = hypothesesGraph.getLineageId(time, idx)
                if lineage_id is None:
                    lineage_id = 1
                indexMapping[idx] = lineage_id
            
        return indexMapping[volume]
                  
    
    def _setupRelabeledFeatureSlot(self, original_feature_slot):
        from ilastik.applets.trackingFeatureExtraction import config
        # when exporting after merger resolving, the stored object features are not up to date for the relabeled objects
        opRelabeledRegionFeatures = OpRelabeledMergerFeatureExtraction(parent=self)
        opRelabeledRegionFeatures.RawImage.connect(self.RawImage)
        opRelabeledRegionFeatures.LabelImage.connect(self.LabelImage)
        opRelabeledRegionFeatures.RelabeledImage.connect(self.RelabeledImage)
        opRelabeledRegionFeatures.OriginalRegionFeatures.connect(original_feature_slot)

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

        hypothesesGraph = self.HypothesesGraph.value

        if not hypothesesGraph:
            raise DatasetConstraintError('Tracking', 'Tracking solution not ready: Did you forgot to press the Track button?')

        with_divisions = self.Parameters.value["withDivisions"] if self.Parameters.ready() else False

        obj_count = list(objects_per_frame(label_image_slot))        
        object_ids_generator = ilastik_ids(obj_count)
        
        # Tracking results data 
        object_ids = [] 
        lineage_ids = []
        track_ids = []
        
        # Division table data
        div_timesteps = []
        div_object_ids = []
        div_lineage_ids = []
        div_track_ids = []
        div_child1_oids = []
        div_child1_track_ids = []
        div_child2_oids = []
        div_child2_track_ids = []        
          
        for (time, object_id) in object_ids_generator: 
            node = (time, object_id)
            
            # Populate results table
            object_ids.append(node)
            
            if hypothesesGraph.hasNode(node):        
                lineage_id = hypothesesGraph.getLineageId(time, object_id)
                if not lineage_id:    
                    lineage_id = 0
                lineage_ids.append(lineage_id)
                    
                track_id = hypothesesGraph.getTrackId(time, object_id)    
                if not track_id:
                    track_id = 0
                track_ids.append(track_id) 
                
                # Populate division table  
                if with_divisions and 'divisionValue' in hypothesesGraph._graph.node[node] and hypothesesGraph._graph.node[node]['divisionValue']:
                    div_timesteps.append(time)
                    div_object_ids.append(object_id)
                    
                    if not lineage_id:
                        lineage_id = 0
                    div_lineage_ids.append(object_id)
                                        
                    if not track_id:
                        track_id = 0
                    div_track_ids.append(track_id)
                    
                    assert len(hypothesesGraph._graph.out_edges(node)) != 2, "Division node {}, does not contain 2 children".format(node) 
                    
                    child1 = hypothesesGraph._graph.out_edges(node)[0][1]
                    child1_time = child1[0]
                    child1_object_id = child1[1]
                    div_child1_oids.append(child1_object_id)
                    child1_track_id = hypothesesGraph.getTrackId(child1_time, child1_object_id)
                    if not child1_track_id:
                        child1_track_id = 0
                    div_child1_track_ids.append(child1_track_id)
                    
                    child2 = hypothesesGraph._graph.out_edges(node)[1][1]
                    child2_time = child2[0]
                    child2_object_id = child2[1]
                    div_child2_oids.append(child2_object_id)
                    child2_track_id = hypothesesGraph.getTrackId(child2_time, child2_object_id)
                    if not child2_track_id:
                        child2_track_id = 0
                    div_child2_track_ids.append(child2_track_id)
                                          
            else:
                lineage_ids.append(0)
                track_ids.append(0)
                
        # Write results table
        selected_features = list(selected_features)

        file_path = settings["file path"]
        if filename_suffix:
            path, ext = os.path.splitext(file_path)
            file_path = path + "-" + filename_suffix + ext

        export_file = ExportFile(file_path)
        export_file.ExportProgress.subscribe(progress_slot)
        export_file.InsertionProgress.subscribe(progress_slot)

        export_file.add_columns("table", range(sum(obj_count)), Mode.List, Default.KnimeId)
        export_file.add_columns("table", object_ids, Mode.List, Default.IlastikId)
        export_file.add_columns("table", lineage_ids, Mode.List, Default.Lineage)
        export_file.add_columns("table", track_ids, Mode.List, Default.TrackId)

        export_file.add_columns("table", object_feature_slot, Mode.IlastikFeatureTable,
                                {"selection": selected_features})

        # Write divisions tab;e
        if with_divisions:
            divisions_data = zip(div_timesteps, div_object_ids, div_lineage_ids, div_track_ids, div_child1_oids, div_child1_track_ids, div_child2_oids, div_child2_track_ids)
            if divisions_data:
                export_file.add_columns("divisions", divisions_data, Mode.List, Default.DivisionNames)

        if settings["file type"] == "h5":
            export_file.add_rois(Default.LabelRoiPath, label_image_slot, "table", settings["margin"], "labeling")
            if settings["include raw"]:
                export_file.add_image(Default.RawPath, self.RawImage)
            else:
                export_file.add_rois(Default.RawRoiPath, self.RawImage, "table", settings["margin"])
                
        # Write files
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

        for t in feats.keys():
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
                    traxel.add_feature_array("divProb", 2)
                    # idx+1 because rc and ct start from 1, divProbs starts from 0
                    prob = float(divProbs[t][idx + 1][1])
                    prob = float(prob)
                    if prob < 0.0000001:
                        prob = 0.0000001
                    if prob > 0.99999999:
                        prob = 0.99999999
                    traxel.set_feature_value("divProb", 0, 1.0 - prob)
                    traxel.set_feature_value("divProb", 1, prob)

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
        
