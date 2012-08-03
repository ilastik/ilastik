from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
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
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpTracking"
    category = "other"
    
    #InputImage = InputSlot()
    #MinValue = InputSlot(stype='int')
    #MaxValue = InputSlot(stype='int')
    
    Output = OutputSlot()
    RawData = OutputSlot()
    Locpic = OutputSlot()
    Objects = InputSlot()

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpTracking, self).__init__(parent=parent,graph=graph,register=register)
        
        print "extract traxels"
        self.ts = ctracking.TraxelStore()
        f = h5py.File("/home/bkausler/src/ilastik/tracking/relabeled-stack/regioncenter.h5", 'r')
        for t in range(10):
            og = f['samples/'+str(t)+'/objects']
            traxels = cTraxels_from_objects_group( og, t)
            self.ts.add_from_Traxels(traxels)
            print "-- extracted %d traxels at t %d" % (len(traxels), t)
        f.close()
        rf_fn = "none"
        app = 500
        dis = 500
        det = 10
        mdet = 200
        use_rf = False
        opp = 100
        forb = 0
        with_constr = True
        fixed_detections = False
        mdd = 0
        min_angle = 0
        ep_gap = 0.2

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
                                        
        events = tracker(self.ts)
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
        

        self._rawReader = OpInputDataReader( graph )
        self._rawReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5/raw')
        self.RawData.connect( self._rawReader.Output )

        #self._trackingReader = OpInputDataReader( graph )
        #self._trackingReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/labeledtracking.h5/labeledtracking')
        #self.Output.connect( self._trackingReader.Output )

        self._locpicReader = OpInputDataReader( graph )
        self._locpicReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/locpic.h5/locpic')
        self.Locpic.connect( self._locpicReader.Output )

        self._objectsReader = OpInputDataReader( graph )
        self._objectsReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5/objects')

        print self.Objects.meta
        assert( self._objectsReader.Output.ready() )

        self.Objects.connect( self._objectsReader.Output )
        assert( self.Objects.ready() )
        assert( self.Objects.configured() )
        self._initialized = True
        assert(self.configured() )
        print self.Objects.meta
        print self.Output.meta
        
        #self.Output.connect( self._reader.Output )

    
    def setupOutputs(self):
        print "tracking: setupOutputs"
        # Copy the input metadata to both outputs
        #self.Output.meta.assignFrom( self.InputImage.meta )
        #self.InvertedOutput.meta.assignFrom( self.InputImage.meta )
        #self.RawData.meta.assignFrom(self._reader.Output.meta )
        self.Output.meta.assignFrom(self.Objects.meta )
    
    def execute(self, slot, roi, result):
        if slot is self.Output:
            self.Objects.get(roi, destination=result).wait()
            t = roi.start[0]
            if t < len(self.label2color):
                result[0,...,0] = relabel( result[0,...,0], self.label2color[t] )
            else:
                result[...] = 0
            #al = self.Objects.get( SubRegion( self.Objects ) ).wait()
            #print type(al), al.shape

    def propagateDirty(self, inputSlot, roi):
        print "tracking: propagateDirty"
        if inputSlot is self.Objects:
            self.Output.setDirty(roi)
        # if inputSlot.name == "InputImage":
        #     self.Output.setDirty(roi)
        #     self.InvertedOutput.setDirty(roi)
        # if inputSlot.name == "MinValue" or inputSlot.name == "MaxValue":
        #     self.Output.setDirty( slice(None) )
        #     self.InvertedOutput.setDirty( slice(None) )
