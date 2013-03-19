from lazyflow.graph import InputSlot
from lazyflow.rtype import List
from lazyflow.stype import Opaque

import pgmlink
from ilastik.applets.tracking.base.opTrackingBase import OpTrackingBase


class OpFastApproximateTracking(OpTrackingBase): 
    DivisionProbabilities = InputSlot(stype=Opaque, rtype=List)            
    
    def track(self,
            time_range,
            x_range,
            y_range,
            z_range,
            size_range=(0, 100000),
            x_scale=1.0,
            y_scale=1.0,
            z_scale=1.0,
            divDist=30,
            movDist=10,
            divThreshold=0.5,
            distanceFeatures=["com"],
            splitterHandling=True,
            mergerHandling=True):
        
        distFeatureVector = pgmlink.VectorOfString();
        for d in distanceFeatures:
            distFeatureVector.append(d)  
            
        max_traxel_id_at = pgmlink.VectorOfInt()
        ts, filtered_labels, empty_frame = self._generate_traxelstore(time_range, x_range, y_range, z_range, 
                                                                      size_range, x_scale, y_scale, z_scale, 
                                                                      max_traxel_id_at=max_traxel_id_at, 
                                                                      with_div=True)        
        
        if empty_frame:
            print 'cannot track frames with 0 objects, abort.'
            return
    
        tracker = pgmlink.NNTracking(float(divDist), 
                                       float(movDist), 
                                       distFeatureVector, 
                                       float(divThreshold), 
                                       splitterHandling, 
                                       mergerHandling, 
                                       max_traxel_id_at)
                
        self.events = tracker(ts)
        
        self._setLabel2Color(self.events, time_range, filtered_labels, x_range, y_range, z_range)
        
