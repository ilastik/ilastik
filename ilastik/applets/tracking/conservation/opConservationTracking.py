from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.rtype import List
from lazyflow.stype import Opaque
import pgmlink
from ilastik.applets.tracking.base.opTrackingBase import OpTrackingBase
from ilastik.applets.tracking.base.trackingUtilities import relabelMergers


class OpConservationTracking(OpTrackingBase):
    DivisionProbabilities = InputSlot(stype=Opaque, rtype=List)    
    DetectionProbabilities = InputSlot(stype=Opaque, rtype=List)
    
    MergerOutput = OutputSlot()    
    
    def setupOutputs(self):
        super(OpConservationTracking, self).setupOutputs()        
        self.MergerOutput.meta.assignFrom(self.LabelImage.meta)
    
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
            borderAwareWidth = 0.0
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
                
        if cplex_timeout:
            parameters['cplex_timeout'] = cplex_timeout
        else:
            parameters['cplex_timeout'] = ''
        self.Parameters.setValue(parameters)        
        
        if withClassifierPrior:
            if len(self.DetectionProbabilities([0]).wait()[0][0]) != (maxObj + 1):
                raise Exception, 'the max. number of objects must be consistent with the number of labels given in cell classification'
        
        median_obj_size = [0]
                
        ts, filtered_labels, empty_frame = self._generate_traxelstore(time_range, x_range, y_range, z_range, 
                                                                      size_range, x_scale, y_scale, z_scale, 
                                                                      median_object_size=median_obj_size, 
                                                                      with_div=withDivisions,
                                                                      with_opt_correction=withOpticalCorrection,
                                                                      with_coordinate_list=withMergerResolution,
                                                                      with_classifier_prior=withClassifierPrior)
        
        if empty_frame:
            raise Exception, 'cannot track frames with 0 objects, abort.'
              
        
        if avgSize[0] > 0:
            median_obj_size = avgSize
        
        print 'median_obj_size = ', median_obj_size
        
        print 'appearance and disappearance cost set to 500'
        ep_gap = 0.05
        transition_parameter = 5
        disappearance_cost = 500.0
        appearance_cost = 500.0

        fov = pgmlink.FieldOfView(time_range[0] * 1.0,
                                      x_range[0] * x_scale,
                                      y_range[0] * y_scale,
                                      z_range[0] * z_scale,
                                      time_range[-1] * 1.0,
                                      (x_range[1]-1) * x_scale,
                                      (y_range[1]-1) * y_scale,
                                      (z_range[1]-1) * z_scale,)

        tracker = pgmlink.ConsTracking(maxObj,
                                         float(maxDist),
                                         float(divThreshold),
                                         "none",  # detection_rf_filename
                                         sizeDependent,   # size_dependent_detection_prob
                                         0,       # forbidden_cost
                                         float(ep_gap), # ep_gap
                                         float(median_obj_size[0]), # median_object_size
                                         withTracklets,
                                         divWeight,
                                         transWeight,
                                         withDivisions,
                                         disappearance_cost, # disappearance cost
                                         appearance_cost, # appearance cost
                                         withMergerResolution,
                                         ndim,
                                         transition_parameter,
                                         borderAwareWidth,
                                         fov)
        
        try:
            self.events = tracker(ts)
        except:
            raise Exception, 'tracking terminated unsucessfully.'
        
        self._setLabel2Color(self.events, time_range, filtered_labels, x_range, y_range, z_range)
        
