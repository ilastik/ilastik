from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import List, SubRegion
from lazyflow.stype import Opaque

import numpy as np

class OpManualTracking(Operator):
    name = "Manual Tracking"
    category = "other"
    
    BinaryImage = InputSlot()
    LabelImage = InputSlot()    
    RawImage = InputSlot()
    ActiveTrack = InputSlot(stype='int', value=0)
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List)    
    
    TrackImage = OutputSlot()
    Labels = OutputSlot(stype=Opaque, rtype=List)
    Divisions = OutputSlot(stype=Opaque, rtype=List)
    UntrackedImage = OutputSlot()
    
    def __init__(self, parent=None, graph=None):
        super(OpManualTracking, self).__init__(parent=parent, graph=graph)        
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
    
    def _getObjects(self, trange, misdet_idx):                  
        filtered_labels = {}
        oid2tids = {}
        alltids = set()
        for t in range(trange[0],trange[1]):
            count = 0
            filtered_labels[t] = []
            oid2tids[t] = {}
            troi = SubRegion(self.LabelImage, start=[t,] + [0,] * len(self.LabelImage.meta.shape[1:]), 
                             stop=[t+1,] + list(self.LabelImage.meta.shape[1:]))            
            max_oid = np.max(self.LabelImage.get(troi).wait())
            for idx in range(max_oid + 1):
                oid = int(idx) + 1                
                if t in self.labels.keys() and oid in self.labels[t].keys():
                    if misdet_idx not in self.labels[t][oid]:
                        oid2tids[t][oid] = self.labels[t][oid]
                        for l in self.labels[t][oid]:
                            alltids.add(l)   
                        count += 1
                         
            print "at timestep ", t, count, "traxels found"
            
        return oid2tids, alltids
    
#    def _getObjects(self, time_range, x_range, y_range, z_range, size_range, misdet_idx):
#        trange = range(time_range[0], time_range[1])
#        print 'trange=', trange
#        feats = self.ObjectFeatures(trange).wait()        
#          
#        filtered_labels = {}
#        oid2tids = {}
#        alltids = set()
#        for t in feats.keys():
#            rc = feats[t][0]['RegionCenter']
#            if rc.size:
#                rc = rc[1:, ...]
#                
#            ct = feats[t][0]['Count']
#            if ct.size:
#                ct = ct[1:, ...]
#            mainOperator
#            print "at timestep ", t, rc.shape[0], "traxels found"
#            count = 0
#            filtered_labels[t] = []
#            oid2tids[t] = {}
#            for idx in range(rc.shape[0]):
#                oid = int(idx) + 1
#                x, y, z = rc[idx]
#                size = ct[idx]
#                if (x < x_range[0] or x >= x_range[1] or
#                    y < y_range[0] or y >= y_range[1] or
#                    z < z_range[0] or z >= z_range[1] or                    
#                    size < size_range[0] or size >= size_range[1]):
#                    filtered_labels[t].append(oid)
#                    continue
#                
#                count += 1
#                if t in self.labels.keys() and oid in self.labels[t].keys():
#                    if misdet_idx not in self.labels[t][oid]:
#                        oid2tids[t][oid] = self.labels[t][oid]
#                        for l in self.labels[t][oid]:
#                            alltids.add(l)   
#                         
#            print "at timestep ", t, count, "traxels passed filter"
#            
#        return oid2tids, alltids
    
