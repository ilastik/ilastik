import pgmlink
import math
from ilastik.applets.tracking.base.opTrackingBase import OpTrackingBase

class OpChaingraphTracking(OpTrackingBase): 
    
    def track( self,
            time_range,
            x_range,
            y_range,
            z_range,
            size_range = (0,100000),
            x_scale = 1.0,
            y_scale = 1.0,
            z_scale = 1.0,               
            rf_fn = "none",
            app = 500,
            dis = 500,
            noiserate = 0.10,
            noiseweight = 100,
            use_rf = False,
            opp = 100,
            forb = 0,
            with_constr = True,
            fixed_detections = False,
            mdd = 0,
            min_angle = 0,
            ep_gap = 0.2,
            n_neighbors = 2,            
            with_div = True,
            cplex_timeout = None):

        if not self.Parameters.ready():
            raise Exception("Parameter slot is not ready")
        
        parameters = self.Parameters.value
        parameters['appearance'] = app
        parameters['disappearance'] = dis
        parameters['opportunity'] = opp
        parameters['noiserate'] = noiserate
        parameters['noiseweight'] = noiseweight
        parameters['epgap'] = ep_gap
        parameters['nneighbors'] = n_neighbors   
        parameters['with_divisions'] = with_div
        if cplex_timeout:
            parameters['cplex_timeout'] = cplex_timeout
        else:
            parameters['cplex_timeout'] = ''
        self.Parameters.setValue(parameters)        
        
        det = noiseweight*(-1)*math.log(1-noiserate)
        mdet = noiseweight*(-1)*math.log(noiserate)
        
        ts, filtered_labels, empty_frame = self._generate_traxelstore(time_range, x_range, y_range, z_range, size_range, x_scale, y_scale, z_scale)
        
        if empty_frame:
            raise Exception, 'Cannot track frames with 0 objects, abort.'
        
        tracker = pgmlink.ChaingraphTracking(rf_fn,
                                app,
                                dis,
                                det,
                                mdet,
                                use_rf,
                                opp,
                                forb,
                                with_constr,
                                fixed_detections,
                                mdd,
                                min_angle,
                                ep_gap,
                                n_neighbors
                                )

        tracker.set_with_divisions(with_div)        
        if cplex_timeout:
            tracker.set_cplex_timeout(cplex_timeout)
                
        try:
            self.events = tracker(ts)
        except Exception as e:
            raise Exception, 'Tracking terminated unsucessfully: ' + str(e)
        
        self._setLabel2Color(self.events, time_range, filtered_labels, x_range, y_range, z_range, successive_ids=True)
        
