import numpy as np
from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.rtype import List
from lazyflow.stype import Opaque
try:
    import pgmlink
except:
    import pgmlinkNoIlpSolver as pgmlink
from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.applets.tracking.base.opTrackingBase import OpTrackingBase
from ilastik.applets.tracking.base.trackingUtilities import relabel, highlightMergers
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key, OpRegionFeatures
from ilastik.applets.tracking.base.trackingUtilities import get_events
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.roi import sliceToRoi
from opRelabeledMergerFeatureExtraction import OpRelabeledMergerFeatureExtraction

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

class OpConservationTrackingPgmLink(OpTrackingBase):
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
        super(OpConservationTrackingPgmLink, self).__init__(parent=parent, graph=graph)

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
        super(OpConservationTrackingPgmLink, self).setupOutputs()
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
            parameters = self.Parameters.value
            trange = range(roi.start[0], roi.stop[0])
            original = np.zeros(result.shape, dtype=slot.meta.dtype)
            super(OpConservationTrackingPgmLink, self).execute(slot, subindex, roi, original)
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
        else:  # default bahaviour
            super(OpConservationTrackingPgmLink, self).execute(slot, subindex, roi, result)
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
        parameters['max_nearest_neighbors'] = max_nearest_neighbors

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
        elif solverName == "Flow-based":
            if hasattr(pgmlink.ConsTrackingSolverType, "FlowSolver"):
                solver = pgmlink.ConsTrackingSolverType.FlowSolver
            else:
                raise AssertionError("Cannot select Flow solver if pgmlink was compiled without Flow support")
        else:
            raise ValueError("Unknown solver {} selected".format(solverName))
        return solver

    def propagateDirty(self, inputSlot, subindex, roi):
        super(OpConservationTrackingPgmLink, self).propagateDirty(inputSlot, subindex, roi)

        if inputSlot == self.NumLabels:
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

        vigra_features = list((set(config.vigra_features)).union(config.selected_features_objectcount[config.features_vigra_name]))
        feature_names_vigra = {}
        feature_names_vigra[config.features_vigra_name] = { name: {} for name in vigra_features }
        opRelabeledRegionFeatures.FeatureNames.setValue(feature_names_vigra)

        return opRelabeledRegionFeatures