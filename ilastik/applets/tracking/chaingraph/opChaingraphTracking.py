import ctracking
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
            det = 10,
            mdet = 200,
            use_rf = False,
            opp = 100,
            forb = 0,
            with_constr = True,
            fixed_detections = False,
            mdd = 0,
            min_angle = 0,
            ep_gap = 0.2):

        tracker = ctracking.MrfTracking(rf_fn,
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
                                        ep_gap)

        ts, filtered_labels, empty_frame = self._generate_traxelstore(time_range, x_range, y_range, z_range, size_range, x_scale, y_scale, z_scale)
        
        if empty_frame:
            print 'cannot track frames with 0 objects, abort.'
            return
        
        self.events = tracker(ts)
        self._setLabel2Color(self.events, time_range, filtered_labels, x_range, y_range, z_range)
        