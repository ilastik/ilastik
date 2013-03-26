from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion, List
from lazyflow.stype import Opaque

import numpy as np
import pgmlink
from ilastik.applets.tracking.base.trackingUtilities import relabel
from ilastik.utility.operatorSubView import OperatorSubView


class OpManualTracking(Operator):
    name = "Manual Tracking"
    category = "other"
    
    BinaryImage = InputSlot()
    LabelImage = InputSlot()    
    RawImage = InputSlot()
    Labels = InputSlot(stype=Opaque, rtype=List, value=[])
    ActiveTrack = InputSlot(stype='int', value=0)
    
    Tracks = OutputSlot(stype=Opaque, rtype=List)
    TrackImage = OutputSlot()
    
    def __init__(self, parent=None, graph=None):
        super(OpManualTracking, self).__init__(parent=parent, graph=graph)        
        self.tracks = {}
        
    def setupOutputs(self):        
        self.TrackImage.meta.assignFrom(self.LabelImage.meta)
        self.Tracks.meta.shape = [self.LabelImage.meta.shape[0]]
        self.Tracks.meta.dtype = object
        self.Tracks.meta.axistags = None

    
    def execute(self, slot, subindex, roi, result):
        if slot is self.Tracks:
            times = roi._l
            if len(times) == 0:
                times = range(self.LabelImage.meta.shape[0])
            
            for t in times:
                if t not in self.tracks.keys():
                    self.tracks[t] = {}                
#                self.tracks[t][]
                
        elif slot is self.TrackImage:            
            assert roi.stop[0] - roi.start[0], 'only implemented for single time steps'
            t = roi.start[0]
            
            if not self.Labels.ready():
                result[:] = 0
                return result
            oid2tid = self.Labels.value
            print 'opManualTracking::execute: oid2tid =',oid2tid
            if t not in oid2tid.keys():
                result[:] = 0
                return result
            
            result = self.LabelImage.get(roi).wait()      
            t = roi.start[0]            
            result[0, ..., 0] = self._relabel(result[0, ..., 0], oid2tid[t])
            
            return result
        
    def propagateDirty(self, inputSlot, subindex, roi):
        print 'opManualTracking::propagateDirty: roi =', roi        
        if inputSlot is self.Labels:
            if len(roi._l) == 0:
                self.TrackImage.setDirty(slice(None))
            elif isinstance(roi._l[0], int):
                for t in roi._l:
                    self.TrackImage.setDirty(slice(t))
            else:
                print 'cannot propagate dirtyness: ', roi
                
#        if inputSlot is self.LabelImage:
#            self.Output.setDirty(roi)

 
    def _relabel(self, volume, replace):
        mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
        mp[1:] = 0
        labels = np.unique(volume)
        for label in labels:
            if label > 0:
                if label in replace and len(replace[label]) > 0:
                    mp[label] = list(replace[label])[0]
        return mp[volume]