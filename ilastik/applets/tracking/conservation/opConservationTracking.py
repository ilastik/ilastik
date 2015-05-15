import numpy as np
from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.rtype import List
from lazyflow.stype import Opaque
import pgmlink
from ilastik.applets.tracking.base.opTrackingBase import OpTrackingBase
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
from ilastik.applets.tracking.base.trackingUtilities import relabelMergers
from ilastik.applets.tracking.base.trackingUtilities import get_events
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.roi import sliceToRoi


import logging
logger = logging.getLogger(__name__)


class OpConservationTracking(OpTrackingBase):
    DivisionProbabilities = InputSlot(stype=Opaque, rtype=List)
    DetectionProbabilities = InputSlot(stype=Opaque, rtype=List)
    NumLabels = InputSlot()

    # compressed cache for merger output
    MergerInputHdf5 = InputSlot(optional=True)
    MergerCleanBlocks = OutputSlot()
    MergerOutputHdf5 = OutputSlot()
    MergerCachedOutput = OutputSlot() # For the GUI (blockwise access)
    MergerOutput = OutputSlot()
    

    def __init__(self, parent=None, graph=None):
        super(OpConservationTracking, self).__init__(parent=parent, graph=graph)

        self._mergerOpCache = OpCompressedCache( parent=self )
        self._mergerOpCache.InputHdf5.connect(self.MergerInputHdf5)
        self._mergerOpCache.Input.connect(self.MergerOutput)
        self.MergerCleanBlocks.connect(self._mergerOpCache.CleanBlocks)
        self.MergerOutputHdf5.connect(self._mergerOpCache.OutputHdf5)
        self.MergerCachedOutput.connect(self._mergerOpCache.Output)
        
        self.tracker = None


    def setupOutputs(self):
        super(OpConservationTracking, self).setupOutputs()
        self.MergerOutput.meta.assignFrom(self.LabelImage.meta)

        self._mergerOpCache.BlockShape.setValue( self._blockshape )
    
    def execute(self, slot, subindex, roi, result):
        result = super(OpConservationTracking, self).execute(slot, subindex, roi, result)
        
        if slot is self.MergerOutput:
            result = self.LabelImage.get(roi).wait()
            parameters = self.Parameters.value
            
            trange = range(roi.start[0], roi.stop[0])
            for t in trange:
                if ('time_range' in parameters and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0] and len(self.mergers) > t and len(self.mergers[t])):
                    result[t-roi.start[0],...,0] = relabelMergers(result[t-roi.start[0],...,0], self.mergers[t])
                else:
                    result[t-roi.start[0],...][:] = 0
            
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
            graph_building_parameter_changed = True
            ):
        
        if not self.Parameters.ready():
            raise Exception("Parameter slot is not ready")
        
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
                
        if cplex_timeout:
            parameters['cplex_timeout'] = cplex_timeout
        else:
            parameters['cplex_timeout'] = ''
            cplex_timeout = float(1e75)
        
        if withClassifierPrior:
            if not self.DetectionProbabilities.ready() or len(self.DetectionProbabilities([0]).wait()[0]) == 0:
                raise Exception, 'Classifier not ready yet. Did you forget to train the Object Count Classifier?'
            if not self.NumLabels.ready() or self.NumLabels.value != (maxObj + 1):
                raise Exception, 'The max. number of objects must be consistent with the number of labels given in Object Count Classification.\n'\
                    'Check whether you have (i) the correct number of label names specified in Object Count Classification, and (ii) provided at least' \
                    'one training example for each class.'
            if len(self.DetectionProbabilities([0]).wait()[0][0]) != (maxObj + 1):
                raise Exception, 'The max. number of objects must be consistent with the number of labels given in Object Count Classification.\n'\
                    'Check whether you have (i) the correct number of label names specified in Object Count Classification, and (ii) provided at least' \
                    'one training example for each class.'            
        
        median_obj_size = [0]

        ts, empty_frame = self._generate_traxelstore(time_range, x_range, y_range, z_range, 
                                                                      size_range, x_scale, y_scale, z_scale, 
                                                                      median_object_size=median_obj_size, 
                                                                      with_div=withDivisions,
                                                                      with_opt_correction=withOpticalCorrection,
                                                                      with_classifier_prior=withClassifierPrior)
        
        if empty_frame:
            raise Exception, 'cannot track frames with 0 objects, abort.'
              
        
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

        if(self.tracker == None or graph_building_parameter_changed):
            print '\033[94m' +"make new graph"+  '\033[0m'
            self.tracker = pgmlink.ConsTracking(maxObj,
                                         sizeDependent,   # size_dependent_detection_prob
                                         float(median_obj_size[0]), # median_object_size
                                         float(maxDist),
                                         withDivisions,
                                         float(divThreshold),
                                         "none",  # detection_rf_filename
                                         fov,
                                         "none", # dump traxelstore,
                                         pgmlink.ConsTrackingSolverType.CplexSolver
                                         )
            self.tracker.buildGraph(ts) # return value ???

            # add labels and annotations

        # create dummy uncertainty parameter object with just one iteration, so no perturbations at all (iter=0 -> MAP)
        sigmas = pgmlink.VectorOfDouble()
        for i in range(5):
            sigmas.append(0.0)
        uncertaintyParams = pgmlink.UncertaintyParameter(1, pgmlink.DistrId.PerturbAndMAP, sigmas)

        try:
            eventsVector = self.tracker.track(0,       # forbidden_cost
                                            float(ep_gap), # ep_gap
                                            withTracklets,
                                            10.0, # detection weight
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
                                            None) # TransitionClassifier

            eventsVector = eventsVector[0] # we have a vector such that we could get a vector per perturbation

            # extract the coordinates with the given event vector
            if withMergerResolution:
                coordinate_map = pgmlink.TimestepIdCoordinateMap()
                # TODO what should the variable withArmaCoordinates toggle?
                # is this the intended use?
                if withArmaCoordinates:
                    coordinate_map.initialize()
                self._get_merger_coordinates(coordinate_map,
                                             time_range,
                                             eventsVector)

                eventsVector = self.tracker.resolve_mergers(eventsVector,
                                                coordinate_map.get(),
                                                float(ep_gap),
                                                transWeight,
                                                withTracklets,
                                                ndim,
                                                transition_parameter,
                                                True, # with_constraints
                                                #True) # with_multi_frame_moves
                                                None) # TransitionClassifier
        except Exception as e:
            raise Exception, 'Tracking terminated unsuccessfully: ' + str(e)
        
        if len(eventsVector) == 0:
            raise Exception, 'Tracking terminated unsuccessfully: Events vector has zero length.'
        
        events = get_events(eventsVector)
        self.Parameters.setValue(parameters, check_changed=False)
        self.EventsVector.setValue(events, check_changed=False)
        

    def propagateDirty(self, inputSlot, subindex, roi):
        super(OpConservationTracking, self).propagateDirty(inputSlot, subindex, roi)

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
