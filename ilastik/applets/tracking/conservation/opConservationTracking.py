import numpy as np
from lazyflow.graph import Operator, InputSlot, OutputSlot
from ilastik.utility.exportingOperator import ExportingOperator
from lazyflow.rtype import List
from lazyflow.stype import Opaque
try:
    import pgmlink
except:
    import pgmlinkNoIlpSolver as pgmlink
from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.applets.tracking.base.trackingUtilities import relabel, highlightMergers
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key, OpRegionFeatures
from ilastik.applets.tracking.base.trackingUtilities import get_dict_value, get_events
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.operators.valueProviders import OpZeroDefault
from lazyflow.roi import sliceToRoi
from opRelabeledMergerFeatureExtraction import OpRelabeledMergerFeatureExtraction

from hytra.core.ilastik_project_options import IlastikProjectOptions
from hytra.core.jsongraph import JsonTrackingGraph
from hytra.core.ilastikhypothesesgraph import IlastikHypothesesGraph
from hytra.core.fieldofview import FieldOfView
from hytra.core.mergerresolver import MergerResolver
from hytra.core.probabilitygenerator import ProbabilityGenerator
from hytra.core.probabilitygenerator import Traxel

import dpct

import logging
logger = logging.getLogger(__name__)

def swirl_motion_func_creator(velocityWeight):
    def swirl_motion_func(traxelA, traxelB, traxelC, traxelD):
        traxels = [traxelA, traxelB, traxelC, traxelD]
        positions = [np.array([t.X(), t.Y(), t.Z()]) for t in traxels]
        vecs = [positions[1] - positions[0], positions[2] - positions[1]]

        # acceleration is change in velocity
        acc = vecs[1] - vecs[0]

        # assume constant acceleration to find expected velocity vector
        expected_vel = vecs[1] + acc

        # construct expected position
        expected_pos = positions[2] + expected_vel

        # penalize deviation from that position
        deviation = np.linalg.norm(expected_pos - positions[3])
        cost = float(velocityWeight) * deviation
        tIds = [(t.Timestep, t.Id) for t in traxels]

        return cost
    return swirl_motion_func

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


    def __init__(self, parent=None, graph=None):
        super(OpConservationTracking, self).__init__(parent=parent, graph=graph)

        self.label2color = []
        self.mergers = []
        self.resolvedto = []

        self.track_id = None
        self.extra_track_ids = None
        self.divisions = None

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
            
            trange = range(roi.start[0], roi.stop[0])
            original = np.zeros(result.shape, dtype=slot.meta.dtype)         
            
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
            parameters = self.Parameters.value
            trange = range(roi.start[0], roi.stop[0])
            result[:] = self.LabelImage.get(roi).wait()
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
        elif slot == self.AllBlocks:
            # if nothing was computed, return empty list
            if len(self.label2color) == 0:
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
            max_nearest_neighbors = 1,
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

        do_build_hypotheses_graph = True

        if cplex_timeout:
            parameters['cplex_timeout'] = cplex_timeout
        else:
            parameters['cplex_timeout'] = ''
            cplex_timeout = float(1e75)
        
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
        
        median_obj_size = [0]

        ################[HyTra Integration ends here]#####################
        
        traxelstore = self._generate_traxelstore_HyTra(time_range, x_range, y_range, z_range,
                                                                      size_range, x_scale, y_scale, z_scale, 
                                                                      median_object_size=median_obj_size, 
                                                                      with_div=withDivisions,
                                                                      with_opt_correction=withOpticalCorrection,
                                                                      with_classifier_prior=withClassifierPrior)
        
        def constructFov(shape, t0, t1, scale=[1, 1, 1]):
            [xshape, yshape, zshape] = shape
            [xscale, yscale, zscale] = scale
        
            fov = FieldOfView(t0, 0, 0, 0, t1, xscale * (xshape - 1), yscale * (yshape - 1),
                              zscale * (zshape - 1))
            return fov

        # FIXME: Assumes (x,y,z) axis order
        fieldOfView = constructFov((x_range[1], y_range[1], z_range[1]),
                                   0,
                                   time_range[-1]+1,
                                   [x_scale,
                                   y_scale,
                                   z_scale])

        hypotheses_graph = IlastikHypothesesGraph(
            traxelstore=traxelstore,
            timeRange=(0,time_range[-1]+1),
            maxNumObjects=maxObj,
            numNearestNeighbors=max_nearest_neighbors,
            fieldOfView=fieldOfView,
            withDivisions=False,#'without-divisions' not in params,
            divisionThreshold=0.1
        )

        #if withTracklets:
        #    hypotheses_graph = hypotheses_graph.generateTrackletGraph()
            
        hypotheses_graph = hypotheses_graph.generateTrackletGraph()

        hypotheses_graph.insertEnergies()

        trackingGraph = hypotheses_graph.toTrackingGraph()
        
        trackingGraph.convexifyCosts()
        
        model = trackingGraph.model

        weights = {u'weights': [divWeight, transWeight, appearance_cost, disappearance_cost]}
        result = dpct.trackFlowBased(model, weights)
        
        #hytra.core.jsongraph.writeToFormattedJSON(options.result_filename, result)

#         if withMergerResolution:
#             # Merger resolving code here

        import hytra    
        traxelIdPerTimestepToUniqueIdMap, uuidToTraxelMap = hytra.core.jsongraph.getMappingsBetweenUUIDsAndTraxels(model)
        timesteps = [t for t in traxelIdPerTimestepToUniqueIdMap.keys()]
    
        mergers, detections, links, divisions = hytra.core.jsongraph.getMergersDetectionsLinksDivisions(result, uuidToTraxelMap, withDivisions=False)
    
        # group by timestep for event creation
        #mergersPerTimestep = hytra.core.jsongraph.getMergersPerTimestep(mergers, timesteps)
        #linksPerTimestep = hytra.core.jsongraph.getLinksPerTimestep(links, timesteps)
        #detectionsPerTimestep = hytra.core.jsongraph.getDetectionsPerTimestep(detections, timesteps)
        #divisionsPerTimestep = hytra.core.jsongraph.getDivisionsPerTimestep(divisions, linksPerTimestep, timesteps, withDivisions=False)
        
        ################[HyTra Integration ends here]#####################

        fs, ts, empty_frame, max_traxel_id_at = self._generate_traxelstore(time_range, x_range, y_range, z_range,
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
        transition_parameter = 5
        
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

        if self.tracker is None:
            do_build_hypotheses_graph = True

        solverType = self.getPgmlinkSolverType(solverName)

        if do_build_hypotheses_graph:
            print '\033[94m' +"make new graph"+  '\033[0m'
            self.tracker = pgmlink.ConsTracking(int(maxObj),
                                         bool(sizeDependent),   # size_dependent_detection_prob
                                         float(median_obj_size[0]), # median_object_size
                                         float(maxDist),
                                         bool(withDivisions),
                                         float(divThreshold),
                                         "none",  # detection_rf_filename
                                         fov,
                                         "none", # dump traxelstore,
                                         solverType,
                                         ndim
                                         )
            g = self.tracker.buildGraph(ts, max_nearest_neighbors)

        # create dummy uncertainty parameter object with just one iteration, so no perturbations at all (iter=0 -> MAP)
        sigmas = pgmlink.VectorOfDouble()
        for i in range(5):
            sigmas.append(0.0)
        uncertaintyParams = pgmlink.UncertaintyParameter(1, pgmlink.DistrId.PerturbAndMAP, sigmas)

        params = self.tracker.get_conservation_tracking_parameters(
            0,       # forbidden_cost
            float(ep_gap), # ep_gap
            bool(withTracklets), # with tracklets
            float(10.0), # detection weight
            float(divWeight), # division weight
            float(transWeight), # transition weight
            float(disappearance_cost), # disappearance cost
            float(appearance_cost), # appearance cost
            bool(withMergerResolution), # with merger resolution
            int(ndim), # ndim
            float(transition_parameter), # transition param
            float(borderAwareWidth), # border width
            True, #with_constraints
            uncertaintyParams, # uncertainty parameters
            float(cplex_timeout), # cplex timeout
            None, # transition classifier
            solverType,
            False, # training to hard constraints
            1 # num threads
        )

        # if motionModelWeight > 0:
        #     logger.info("Registering motion model with weight {}".format(motionModelWeight))
        #     params.register_motion_model4_func(swirl_motion_func_creator(motionModelWeight), motionModelWeight * 25.0)

        try:
            eventsVector = self.tracker.track(params, False)

            eventsVector = eventsVector[0] # we have a vector such that we could get a vector per perturbation

            # extract the coordinates with the given event vector
            if withMergerResolution:
                coordinate_map = pgmlink.TimestepIdCoordinateMap()

                self._get_merger_coordinates(coordinate_map,
                                             time_range,
                                             eventsVector)
                self.CoordinateMap.setValue(coordinate_map)

                eventsVector = self.tracker.resolve_mergers(
                    eventsVector,
                    params,
                    coordinate_map.get(),
                    float(ep_gap),
                    float(transWeight),
                    bool(withTracklets),
                    ndim,
                    transition_parameter,
                    max_traxel_id_at,
                    True, # with_constraints
                    None) # TransitionClassifier

        except Exception as e:
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

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)
        elif inputSlot is self.EventsVector:
            self._setLabel2Color()
            try:
                self._setLabel2Color(export_mode=True)
            except:
                logger.debug("Warning: some label information might be wrong...")
        elif inputSlot == self.NumLabels:
            if self.parent.parent.trackingApplet._gui \
                    and self.parent.parent.trackingApplet._gui.currentGui() \
                    and self.NumLabels.ready() \
                    and self.NumLabels.value > 1:
                self.parent.parent.trackingApplet._gui.currentGui()._drawer.maxObjectsBox.setValue(self.NumLabels.value-1)

    def _get_merger_coordinates(self, coordinate_map, time_range, eventsVector):
        # fetch features
        feats = self.ObjectFeatures(time_range).wait()
        # iterate over all timesteps
        for t in feats.keys():
            rc = feats[t][default_features_key]['RegionCenter']
            lower = feats[t][default_features_key]['Coord<Minimum>']
            upper = feats[t][default_features_key]['Coord<Maximum>']
            size = feats[t][default_features_key]['Count']
            for event in eventsVector[t]:
                # check for merger events
                if event.type == pgmlink.EventType.Merger:
                    idx = event.traxel_ids[0]
                    # generate roi: assume the following order: txyzc
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
        if self.CoordinateMap.value.size() == 0:
            logger.info("Skipping merger relabeling because coordinate map is empty")
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

    def _do_export_impl(self, settings, selected_features, progress_slot, object_feature_slot, label_image_slot, lane_index, filename_suffix=""):
        from ilastik.utility.exportFile import objects_per_frame, ExportFile, ilastik_ids, Mode, Default, \
            flatten_dict, division_flatten_dict

        selected_features = list(selected_features)
        with_divisions = self.Parameters.value["withDivisions"] if self.Parameters.ready() else False
        obj_count = list(objects_per_frame(label_image_slot))
        track_ids, extra_track_ids, divisions = self.export_track_ids()
        self._setLabel2Color()
        lineage = flatten_dict(self.label2color, obj_count)
        multi_move_max = self.Parameters.value["maxObj"] if self.Parameters.ready() else 2
        t_range = self.Parameters.value["time_range"] if self.Parameters.ready() else (0, 0)
        ids = ilastik_ids(obj_count)

        file_path = settings["file path"]
        if filename_suffix:
            path, ext = os.path.splitext(file_path)
            file_path = path + "-" + filename_suffix + ext

        export_file = ExportFile(file_path)
        export_file.ExportProgress.subscribe(progress_slot)
        export_file.InsertionProgress.subscribe(progress_slot)

        export_file.add_columns("table", range(sum(obj_count)), Mode.List, Default.KnimeId)
        export_file.add_columns("table", list(ids), Mode.List, Default.IlastikId)
        export_file.add_columns("table", lineage, Mode.List, Default.Lineage)
        export_file.add_columns("table", track_ids, Mode.IlastikTrackingTable,
                                {"max": multi_move_max, "counts": obj_count, "extra ids": extra_track_ids,
                                 "range": t_range})

        export_file.add_columns("table", object_feature_slot, Mode.IlastikFeatureTable,
                                {"selection": selected_features})

        if with_divisions:
            if divisions:
                div_lineage = division_flatten_dict(divisions, self.label2color)
                zips = zip(*divisions)
                divisions = zip(zips[0], div_lineage, *zips[1:])
                export_file.add_columns("divisions", divisions, Mode.List, Default.DivisionNames)
            else:
                logger.debug("No divisions occurred. Division Table will not be exported!")

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

    def _setLabel2Color(self, successive_ids=True, export_mode=False):
        if not self.EventsVector.ready() or not self.Parameters.ready() \
                or not self.FilteredLabels.ready():
            return

        if export_mode:
            assert successive_ids, "Export mode only works for successive ids"

        events = self.EventsVector.value
        parameters = self.Parameters.value
        
        time_min = 0
        time_max = self.RawImage.meta.shape[0] - 1 # Assumes t,x,y,z,c
        if 'time_range' in parameters:
            time_min, time_max = parameters['time_range']
        time_range = range(time_min, time_max)

        filtered_labels = self.FilteredLabels.value

        label2color = []
        label2color.append({})
        mergers = []
        resolvedto = []

        maxId = 2  # misdetections have id 1

        # handle start time offsets
        for i in range(time_range[0]):
            label2color.append({})
            mergers.append({})
            resolvedto.append({})

        extra_track_ids = {}
        if export_mode:
            multi_move = {}
            multi_move_next = {}
            divisions = []

        for i in time_range:
            app = get_dict_value(events[str(i - time_range[0] + 1)], "app", [])
            div = get_dict_value(events[str(i - time_range[0] + 1)], "div", [])
            mov = get_dict_value(events[str(i - time_range[0] + 1)], "mov", [])
            merger = get_dict_value(events[str(i - time_range[0])], "merger", [])
            res = get_dict_value(events[str(i - time_range[0])], "res", {})

            logger.debug(" {} app at {}".format(len(app), i))
            logger.debug(" {} div at {}".format(len(div), i))
            logger.debug(" {} mov at {}".format(len(mov), i))
            logger.debug(" {} merger at {}".format(len(merger), i))

            label2color.append({})
            mergers.append({})
            moves_at = []
            resolvedto.append({})

            if export_mode:
                moves_to = {}

            for e in app:
                if successive_ids:
                    label2color[-1][int(e[0])] = maxId  # in export mode, the label color is used as track ID
                    maxId += 1
                else:
                    label2color[-1][int(e[0])] = np.random.randint(1, 255)

            for e in mov:
                if export_mode:
                    if e[1] in moves_to:
                        multi_move.setdefault(i, {})
                        multi_move[i][e[0]] = e[1]
                        if len(moves_to[e[1]]) == 1:  # if we are just setting up this multi move
                            multi_move[i][moves_to[e[1]][0]] = e[1]
                        multi_move_next[(i, e[1])] = 0
                    moves_to.setdefault(e[1], [])
                    moves_to[e[1]].append(e[0])  # moves_to[target] contains list of incoming object ids

                # alternative way of appearance
                if not label2color[-2].has_key(int(e[0])):
                    if successive_ids:
                        label2color[-2][int(e[0])] = maxId
                        maxId += 1
                    else:
                        label2color[-2][int(e[0])] = np.random.randint(1, 255)

                # assign color of parent
                label2color[-1][int(e[1])] = label2color[-2][int(e[0])]
                moves_at.append(int(e[0]))

                if export_mode:
                    key = i - 1, e[0]
                    if key in multi_move_next:  # captures mergers staying connected over longer time spans
                        multi_move_next[key] = e[1]  # redirects output of last merger to target in this frame
                        multi_move_next[(i, e[1])] = 0  # sets current end to zero (might be changed by above line in the future)

            for e in div:  # event(parent, child, child)
                # if not label2color[-2].has_key(int(e[0])):
                if not int(e[0]) in label2color[-2]:
                    if successive_ids:
                        label2color[-2][int(e[0])] = maxId
                        maxId += 1
                    else:
                        label2color[-2][int(e[0])] = np.random.randint(1, 255)
                ancestor_color = label2color[-2][int(e[0])]
                if export_mode:
                    label2color[-1][int(e[1])] = maxId
                    label2color[-1][int(e[2])] = maxId + 1
                    divisions.append((i, int(e[0]), ancestor_color,
                                      int(e[1]), maxId,
                                      int(e[2]), maxId + 1
                    ))
                    maxId += 2
                else:
                    label2color[-1][int(e[1])] = ancestor_color
                    label2color[-1][int(e[2])] = ancestor_color

            for e in merger:
                mergers[-1][int(e[0])] = int(e[1])

            for o, r in res.iteritems():
                resolvedto[-1][int(o)] = [int(c) for c in r[:-1]]
                # label the original object with the false detection label
                mergers[-1][int(o)] = len(r[:-1])

                if export_mode:
                    extra_track_ids.setdefault(i, {})
                    extra_track_ids[i][int(o)] = [int(c) for c in r[:-1]]

        # last timestep
        merger = get_dict_value(events[str(time_range[-1] - time_range[0] + 1)], "merger", [])
        mergers.append({})
        for e in merger:
            mergers[-1][int(e[0])] = int(e[1])

        res = get_dict_value(events[str(time_range[-1] - time_range[0] + 1)], "res", {})
        resolvedto.append({})
        if export_mode:
            extra_track_ids[time_range[-1] + 1] = {}
        for o, r in res.iteritems():
            resolvedto[-1][int(o)] = [int(c) for c in r[:-1]]
            mergers[-1][int(o)] = len(r[:-1])

            if export_mode:
                    extra_track_ids[time_range[-1] + 1][int(o)] = [int(c) for c in r[:-1]]

        # mark the filtered objects
        for i in filtered_labels.keys():
            if int(i) + time_range[0] >= len(label2color):
                continue
            fl_at = filtered_labels[i]
            for l in fl_at:
                assert l not in label2color[int(i) + time_range[0]]
                label2color[int(i) + time_range[0]][l] = 0

        if export_mode:  # don't set fields when in export_mode
            self.track_id = label2color
            self.divisions = divisions
            self.extra_track_ids = extra_track_ids
            return label2color, extra_track_ids, divisions

        self.track_id = label2color
        self.extra_track_ids = extra_track_ids
        self.label2color = label2color
        self.resolvedto = resolvedto
        self.mergers = mergers

        self.Output._value = None
        self.Output.setDirty(slice(None))

        if 'MergerOutput' in self.outputs:
            self.MergerOutput._value = None
            self.MergerOutput.setDirty(slice(None))

    def export_track_ids(self):
        return self._setLabel2Color(export_mode=True)

    def track_children(self, track_id, start=0):
        if start in self.divisions:
            for t, _, track, _, child_track1, _, child_track2 in self.divisions[start:]:
                if track == track_id:
                    children_of = partial(self.track_children, start=t)
                    return [child_track1, child_track2] + \
                           children_of(child_track1) + children_of(child_track2)
        return []

    def track_parent(self, track_id):
        if not self.divisions == {}:
            for t, oid, track, _, child_track1, _, child_track2 in self.divisions[:-1]:
                if track_id in (child_track1, child_track2):
                    return [track] + self.track_parent(track)
        return []

    def track_family(self, track_id):
        return self.track_children(track_id), self.track_parent(track_id)


    def _generate_traxelstore_HyTra(self,
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
                              median_object_size=None,
                              max_traxel_id_at=None,
                              with_opt_correction=False,
                              with_coordinate_list=False,
                              with_classifier_prior=False):

        if not self.Parameters.ready():
            raise Exception("Parameter slot is not ready")

        # FIXME: Should we set the parameters here?
        parameters = self.Parameters.value
        parameters['scales'] = [x_scale, y_scale, z_scale]
        parameters['time_range'] = [min(time_range), max(time_range)]
        parameters['x_range'] = x_range
        parameters['y_range'] = y_range
        parameters['z_range'] = z_range
        parameters['size_range'] = size_range

        logger.info("generating traxels")
        logger.info("fetching region features and division probabilities")
        
        traxelstore = ProbabilityGenerator()
        
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

        max_traxel_id_at = pgmlink.VectorOfInt()
        filtered_labels = {}
        obj_sizes = []
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

            if with_opt_correction:
                try:
                    rc_corr = feats[t][config.features_vigra_name]['RegionCenter_corr']
                except:
                    raise Exception, 'Can not consider optical correction since it has not been computed before'
                if rc_corr.size:
                    rc_corr = rc_corr[1:, ...]

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

                if with_opt_correction:
                    traxel.add_feature_array("com_corrected", 3)
                    for i, v in enumerate(rc_corr[idx]):
                        traxel.set_feature_value("com_corrected", i, float(v))
                    if len(rc_corr[idx]) == 2:
                        traxel.set_feature_value("com_corrected", 2, 0.)

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
                
                if median_object_size is not None:
                    obj_sizes.append(float(size))

                # Add traxel to traxelstore
                traxelstore.TraxelsPerFrame.setdefault(int(t), {})[int(idx + 1)] = traxel

            if len(filtered_labels_at) > 0:
                filtered_labels[str(int(t) - time_range[0])] = filtered_labels_at
                
            logger.debug("at timestep {}, {} traxels passed filter".format(t, count))
            max_traxel_id_at.append(int(rc.shape[0]))
            if count == 0:
                empty_frame = True
                logger.info('Found empty frames')

            total_count += count

        if median_object_size is not None:
            median_object_size[0] = np.median(np.array(obj_sizes), overwrite_input=True)
            logger.info('median object size = ' + str(median_object_size[0]))

        self.FilteredLabels.setValue(filtered_labels, check_changed=True)

        return traxelstore


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
                              median_object_size=None,
                              max_traxel_id_at=None,
                              with_opt_correction=False,
                              with_coordinate_list=False,
                              with_classifier_prior=False):

        if not self.Parameters.ready():
            raise Exception("Parameter slot is not ready")

        parameters = self.Parameters.value
        parameters['scales'] = [x_scale, y_scale, z_scale]
        parameters['time_range'] = [min(time_range), max(time_range)]
        parameters['x_range'] = x_range
        parameters['y_range'] = y_range
        parameters['z_range'] = z_range
        parameters['size_range'] = size_range

        logger.info("generating traxels")
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
        ts = pgmlink.TraxelStore()
        fs = pgmlink.FeatureStore()

        max_traxel_id_at = pgmlink.VectorOfInt()
        filtered_labels = {}
        obj_sizes = []
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

            if with_opt_correction:
                try:
                    rc_corr = feats[t][config.features_vigra_name]['RegionCenter_corr']
                except:
                    raise Exception, 'Can not consider optical correction since it has not been computed before'
                if rc_corr.size:
                    rc_corr = rc_corr[1:, ...]

            ct = feats[t][default_features_key]['Count']
            if ct.size:
                ct = ct[1:, ...]

            logger.debug("at timestep {}, {} traxels found".format(t, rc.shape[0]))
            count = 0
            filtered_labels_at = []
            for idx in range(rc.shape[0]):
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
                tr = pgmlink.Traxel()
                tr.set_feature_store(fs)
                tr.set_x_scale(x_scale)
                tr.set_y_scale(y_scale)
                tr.set_z_scale(z_scale)
                tr.Id = int(idx + 1)
                tr.Timestep = int(t)

                # pgmlink expects always 3 coordinates, z=0 for 2d data
                tr.add_feature_array("com", 3)
                for i, v in enumerate([x, y, z]):
                    tr.set_feature_value('com', i, float(v))

                tr.add_feature_array("CoordMinimum", 3)
                for i, v in enumerate(lower[idx]):
                    tr.set_feature_value("CoordMinimum", i, float(v))
                tr.add_feature_array("CoordMaximum", 3)
                for i, v in enumerate(upper[idx]):
                    tr.set_feature_value("CoordMaximum", i, float(v))

                if with_opt_correction:
                    tr.add_feature_array("com_corrected", 3)
                    for i, v in enumerate(rc_corr[idx]):
                        tr.set_feature_value("com_corrected", i, float(v))
                    if len(rc_corr[idx]) == 2:
                        tr.set_feature_value("com_corrected", 2, 0.)

                if with_div:
                    tr.add_feature_array("divProb", 1)
                    # idx+1 because rc and ct start from 1, divProbs starts from 0
                    tr.set_feature_value("divProb", 0, float(divProbs[t][idx + 1][1]))

                if with_classifier_prior:
                    tr.add_feature_array("detProb", len(detProbs[t][idx + 1]))
                    for i, v in enumerate(detProbs[t][idx + 1]):
                        val = float(v)
                        if val < 0.0000001:
                            val = 0.0000001
                        if val > 0.99999999:
                            val = 0.99999999
                        tr.set_feature_value("detProb", i, float(val))


                # FIXME: check whether it is 2d or 3d data!
                if with_local_centers:
                    tr.add_feature_array("localCentersX", len(localCenters[t][idx + 1]))
                    tr.add_feature_array("localCentersY", len(localCenters[t][idx + 1]))
                    tr.add_feature_array("localCentersZ", len(localCenters[t][idx + 1]))
                    for i, v in enumerate(localCenters[t][idx + 1]):
                        tr.set_feature_value("localCentersX", i, float(v[0]))
                        tr.set_feature_value("localCentersY", i, float(v[1]))
                        tr.set_feature_value("localCentersZ", i, float(v[2]))

                tr.add_feature_array("count", 1)
                tr.set_feature_value("count", 0, float(size))
                if median_object_size is not None:
                    obj_sizes.append(float(size))

                ts.add(fs, tr)

            if len(filtered_labels_at) > 0:
                filtered_labels[str(int(t) - time_range[0])] = filtered_labels_at
            logger.debug("at timestep {}, {} traxels passed filter".format(t, count))
            max_traxel_id_at.append(int(rc.shape[0]))
            if count == 0:
                empty_frame = True

            total_count += count

        if median_object_size is not None:
            median_object_size[0] = np.median(np.array(obj_sizes), overwrite_input=True)
            logger.info('median object size = ' + str(median_object_size[0]))

        self.FilteredLabels.setValue(filtered_labels, check_changed=True)

        return fs, ts, empty_frame, max_traxel_id_at

    def save_export_progress_dialog(self, dialog):
        """
        Implements ExportOperator.save_export_progress_dialog
        Without this the progress dialog would be hidden after the export
        :param dialog: the ProgressDialog to save
        """
        self.export_progress_dialog = dialog
        