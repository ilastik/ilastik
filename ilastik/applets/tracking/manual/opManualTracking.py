from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import List
from lazyflow.stype import Opaque

import numpy as np
import pgmlink


class OpManualTracking(Operator):
    name = "Manual Tracking"
    category = "other"
    
    BinaryImage = InputSlot()
    LabelImage = InputSlot()    
    RawImage = InputSlot()
    ActiveTrack = InputSlot(stype='int', value=0)
    
    TrackImage = OutputSlot()
    Labels = OutputSlot(stype=Opaque, rtype=List)
    Divisions = OutputSlot(stype=Opaque, rtype=List)
    UntrackedImage = OutputSlot()
    
    def __init__(self, parent=None, graph=None):
        super(OpManualTracking, self).__init__(parent=parent, graph=graph)        
        self.tracks = {}
        self.labels = {}
        self.divisions = {}
        
    def setupOutputs(self):        
        self.TrackImage.meta.assignFrom(self.LabelImage.meta)        
        self.UntrackedImage.meta.assignFrom(self.LabelImage.meta)
                
        for t in range(self.LabelImage.meta.shape[0]):
            if t not in self.labels.keys():
                self.labels[t]={}     

    
    def execute(self, slot, subindex, roi, result):
        if slot is self.Divisions:
            result = {}
            for trackid in self.divisions.keys():
                (children, t_parent) = self.divisions[trackid] 
                result[trackid] = (children, t_parent)
            return result
         
        if slot is self.Labels:
            result = {}
            for t in self.labels.keys():
                result[t] = self.labels[t]
                
        elif slot is self.TrackImage:
            for t in range(roi.start[0],roi.stop[0]):          
                if t not in self.labels.keys():
                    result[t-roi.start[0],...][:] = 0
                    return result
            
                result[t-roi.start[0],...] = self.LabelImage.get(roi).wait()[t-roi.start[0],...]      
                result[t-roi.start[0], ..., 0] = self._relabel(result[t-roi.start[0], ..., 0], self.labels[t])        
        
        elif slot is self.UntrackedImage:
            for t in range(roi.start[0],roi.stop[0]):
                result[t-roi.start[0],...] = self.LabelImage.get(roi).wait()[t-roi.start[0],...]
                labels_at = []
                if t in self.labels.keys():
                    labels_at = self.labels[t]
                result[t-roi.start[0],...,0] = self._relabelUntracked(result[t-roi.start[0],...,0], labels_at)

        return result
        
    def propagateDirty(self, inputSlot, subindex, roi):
        pass
#        print 'opManualTracking::propagateDirty: roi =', roi        
#        if inputSlot is self.Labels:
#            if len(roi._l) == 0:
#                self.TrackImage.setDirty(slice(None))
#            elif isinstance(roi._l[0], int):
#                for t in roi._l:
#                    self.TrackImage.setDirty(slice(t))
#            else:
#                print 'cannot propagate dirtyness: ', roi
                
#        if inputSlot is self.LabelImage:
#            self.Output.setDirty(roi)

 
    def _relabel(self, volume, replace):
        mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
        mp[1:] = 0
        labels = np.unique(volume)
        for label in labels:
            if label > 0:
                if label in replace and len(replace[label]) > 0:
                    l = list(replace[label])[-1]
                    if l == -1:
                        mp[label] = 2**16-1
                    else:
                        mp[label] = l 
        return mp[volume]
    
    def _relabelUntracked(self, volume, tracked_at):
        mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
        mp[1:] = 1
        labels = np.unique(volume)
        for label in labels:
            if (label != 0) and (label in tracked_at.keys()) and (len(tracked_at[label]) > 0):                
                mp[label] = 0
        return mp[volume]