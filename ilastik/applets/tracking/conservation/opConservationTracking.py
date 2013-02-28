from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.rtype import List
from lazyflow.stype import Opaque
import pgmlink
from ilastik.applets.tracking.base.opTrackingBase import OpTrackingBase
from ilastik.applets.tracking.base.trackingUtilities import relabelMergers


class OpConservationTracking(OpTrackingBase):
    ClassMapping = InputSlot(stype=Opaque, rtype=List, optional=True)   
    MergerOutput = OutputSlot()
    
    def setupOutputs(self):
        super(OpConservationTracking, self).setupOutputs()        
        self.MergerOutput.meta.assignFrom(self.LabelImage.meta)
    
    def execute(self, slot, subindex, roi, result):
        result = super(OpConservationTracking, self).execute(slot, subindex, roi, result)
        
        if slot is self.MergerOutput:
            result = self.LabelImage.get(roi).wait()
            t = roi.start[0]
            if (self.last_timerange and t <= self.last_timerange[-1] and t >= self.last_timerange[0]):
                result[0,...,0] = relabelMergers(result[0,...,0], self.mergers[t])
            else:
                result[...] = 0
            
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
            withDivisions=True
            ):
        
        median_obj_size = [0]
                
        ts, filtered_labels, empty_frame = self._generate_traxelstore(time_range, x_range, y_range, z_range, 
                                                                      size_range, x_scale, y_scale, z_scale, 
                                                                      median_object_size=median_obj_size, 
                                                                      with_div=withDivisions)
        
        if empty_frame:
            raise Exception, 'cannot track frames with 0 objects, abort.'
              
        
        if avgSize[0] > 0:
            median_obj_size = avgSize
        
        print 'median_obj_size = ', median_obj_size
        print 'fixed appearance and disappearance cost to 500'
        ep_gap = 0.05
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
                                         500.0,
                                         500.0
                                         )
        
        try:
            self.events = tracker(ts)
        except:
            raise Exception, 'tracking terminated unsucessfully.'
        
        self._setLabel2Color(self.events, time_range, filtered_labels, x_range, y_range, z_range)
        
