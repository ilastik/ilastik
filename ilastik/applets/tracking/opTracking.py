from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion, List
from lazyflow.stype import Opaque
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader

import h5py
import numpy
import numpy as np
import ctracking

def relabel( volume, replace ):
    mp = np.arange(0,np.amax(volume)+1, dtype=volume.dtype)
    mp[1:] = 255
    labels = np.unique(volume)
    for label in labels:
        if label > 0:
            try:
                r = replace[label]
                mp[label] = r
            except:
                pass
    #mp[replace.keys()] = replace.values()
    return mp[volume]

class OpTracking(Operator):
    name = "Tracking"
    category = "other"

    LabelImage = InputSlot()
    ObjectFeatures = InputSlot( stype=Opaque, rtype=List )

    Output = OutputSlot()

    def __init__( self, parent = None, graph = None ):
        super(OpTracking, self).__init__(parent=parent,graph=graph)
        self.label2color = []
        self.last_timerange = ()
        self.last_x_range = ()
        self.last_y_range = ()
        self.last_z_range = ()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.LabelImage.meta )
    
    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            result = self.LabelImage.get(roi).wait()
            
            t = roi.start[0]
            if (self.last_timerange and t <= self.last_timerange[-1] and t >= self.last_timerange[0]):
                result[0,...,0] = relabel( result[0,...,0], self.label2color[t] )
            else:
                result[...] = 0
            return result
        
    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)

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

        ts, filtered_labels = self._generate_traxelstore( time_range, x_range, y_range, z_range, size_range, x_scale, y_scale, z_scale )
        
        events = tracker(ts)
        label2color = []
        label2color.append({})

        # handle start time offsets
        for i in range(time_range[0]):
            label2color.append({})

        for i, events_at in enumerate(events):
            dis = []
            app = []
            div = []
            mov = []
            for event in events_at:
                if event.type == ctracking.EventType.Appearance:
                    app.append((event.traxel_ids[0], event.energy))
                if event.type == ctracking.EventType.Disappearance:
                    dis.append((event.traxel_ids[0], event.energy))
                if event.type == ctracking.EventType.Division:
                    div.append((event.traxel_ids[0], event.traxel_ids[1], event.traxel_ids[2], event.energy))
                if event.type == ctracking.EventType.Move:
                    mov.append((event.traxel_ids[0], event.traxel_ids[1], event.energy))

            print len(dis), "dis at", i + time_range[0]
            print len(app), "app at", i + time_range[0]
            print len(div), "div at", i + time_range[0]
            print len(mov), "mov at", i + time_range[0]            
            print
            label2color.append({})
            #for e in dis:
            #    label2color[-2][e[0]] = 255 # mark disapps

            for e in app:
                label2color[-1][e[0]] = np.random.randint(1,255)

            for e in mov:
                if not label2color[-2].has_key(e[0]):
                    label2color[-2][e[0]] = np.random.randint(1,255)
                label2color[-1][e[1]] = label2color[-2][e[0]]

            for e in div:
                if not label2color[-2].has_key(e[0]):
                    label2color[-2][e[0]] = np.random.randint(1,255)
                ancestor_color = label2color[-2][e[0]]
                label2color[-1][e[1]] = ancestor_color
                label2color[-1][e[2]] = ancestor_color

        # mark the filtered objects
        for t in filtered_labels.keys():

            fl_at = filtered_labels[t]
            for l in fl_at:
                assert( l not in label2color[int(t)])
                label2color[int(t)][l] = 128

        self.label2color = label2color
        self.last_timerange = time_range
        self.last_x_range = x_range
        self.last_y_range = y_range
        self.last_z_range = z_range
        self.Output.setDirty(SubRegion(self.Output))

    def _generate_traxelstore( self,
                               time_range,
                               x_range,
                               y_range,
                               z_range,
                               size_range,
                               x_scale = 1.0,
                               y_scale = 1.0,
                               z_scale = 1.0):
        print "generating traxels"
        print "fetching region centers"
        feats = self.ObjectFeatures( time_range ).wait()

        print "filling traxelstore"
        ts = ctracking.TraxelStore()
        filtered_labels = {}
        for t in feats.keys():
            rc = feats[t]['RegionCenter']
            if rc.size:
                rc = rc[1:,...]

            ct = feats[t]['Count']
            if ct.size:
                ct = ct[1:,...]
            
            print "at timestep ", t, rc.shape[0], "traxels found"
            count = 0
            filtered_labels[t] = []
            for idx in range(rc.shape[0]):
                x,y,z = rc[idx]
                size = ct[idx]
                if (x < x_range[0] or x >= x_range[1] or
                    y < y_range[0] or y >= y_range[1] or
                    z < z_range[0] or z >= z_range[1] or
                    size < size_range[0] or size >= size_range[1]):
                    filtered_labels[t].append(int(idx + 1))
                    continue
                else:
                    count += 1
                tr = ctracking.Traxel()
                tr.set_x_scale(x_scale)
                tr.set_y_scale(y_scale)
                tr.set_z_scale(z_scale)
                tr.Id = int(idx + 1)
                tr.Timestep = t
                tr.add_feature_array("com", len(rc[idx]))
                for i,v in enumerate(rc[idx]):
                    tr.set_feature_value('com', i, float(v))
                ts.add(tr)
            print "at timestep ", t, count, "traxels passed filter"
        return ts, filtered_labels


