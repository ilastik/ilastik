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

def cTraxels_from_objects_group( objects_g, timestep=0):
    features_g = objects_g["features"]
    ids = objects_g["meta/id"].value

    features = {}
    for name in features_g.keys():
        features[name] = features_g[name].value

    ts = ctracking.Traxels()
    for idx in xrange(len(ids)):
        tr = ctracking.Traxel()
        tr.set_x_scale(1.)
        tr.set_y_scale(1.)
        tr.set_z_scale(12.3)
        tr.Id = int(ids[idx])
        tr.Timestep = timestep
        for name_value in features.items():
            if name_value[0] == "RegionCenter":
                name_value = ("com", name_value[1])
            tr.add_feature_array(str(name_value[0]), len(name_value[1][idx]))
            for i,v in enumerate(name_value[1][idx]):
                tr.set_feature_value(str(name_value[0]), i, float(v))
        ts.add_traxel(tr)
    return ts

class OpTracking(Operator):
    name = "Tracking"
    category = "other"

    LabelImage = InputSlot()
    Traxels = InputSlot( stype=Opaque, rtype=List )
    ObjectCenters = InputSlot( stype=Opaque, optional=True )

    Output = OutputSlot()

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpTracking, self).__init__(parent=parent,graph=graph,register=register)
        self.label2color = []
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.LabelImage.meta )
    
    def execute(self, slot, roi, result):
        if slot is self.Output:
            result = self.LabelImage.get(roi).wait()
            
            t = roi.start[0]
            if t < len(self.label2color):
                result[0,...,0] = relabel( result[0,...,0], self.label2color[t] )
            else:
                result[...] = 0
            return result
        
    def propagateDirty(self, inputSlot, roi):
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)

    def track( self,
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

        ts = self.Traxels(range(self.LabelImage.meta.shape[0]) ).wait()
        
        events = tracker(ts)
        label2color = []
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

        self.label2color = label2color
        self.Output.setDirty(SubRegion(self.Output))
