###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.applet import DatasetConstraintError

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import List, SubRegion
from lazyflow.stype import Opaque

import numpy as np

import logging
logger = logging.getLogger(__name__)

class OpAnnotations(Operator):
    name = "Structured Tracking"
    category = "other"
    
    BinaryImage = InputSlot()
    LabelImage = InputSlot()    
    RawImage = InputSlot()
    ActiveTrack = InputSlot(stype='int', value=0)
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List)
    Crops = InputSlot()
    
    TrackImage = OutputSlot()
    Labels = OutputSlot()
    Divisions = OutputSlot()
    UntrackedImage = OutputSlot()

    Annotations = OutputSlot(stype=Opaque)

    def __init__(self, parent=None, graph=None):
        super(OpAnnotations, self).__init__(parent=parent, graph=graph)
        self.labels = {}
        self.divisions = {}

        self.Annotations.setValue(dict())
        self.Labels.setValue({})
        self.Divisions.setValue({})

        self.RawImage.notifyReady( self._checkConstraints )
        self.BinaryImage.notifyReady( self._checkConstraints )

    def setupOutputs(self):
        self.TrackImage.meta.assignFrom(self.LabelImage.meta)
        self.UntrackedImage.meta.assignFrom(self.LabelImage.meta)

        for t in range(self.LabelImage.meta.shape[0]):
            if t not in self.labels.keys():
                self.labels[t]={}

        self.Annotations.meta.dtype = object
        self.Annotations.meta.shape = (1,)

        self.Labels.meta.dtype = object
        self.Labels.meta.shape = self.LabelImage.meta.shape

        self.Divisions.meta.dtype = object
        self.Divisions.meta.shape = (1,)


    def initOutputs(self):
        self.TrackImage.meta.assignFrom(self.LabelImage.meta)
        self.UntrackedImage.meta.assignFrom(self.LabelImage.meta)

        self.Labels.meta.assignFrom(self.LabelImage.meta)
        for t in range(self.LabelImage.meta.shape[0]):
            self.labels[t]={}

    def _checkConstraints(self, *args):
        if self.RawImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            if rawTaggedShape['t'] < 2:
                raise DatasetConstraintError(
                     "Tracking",
                     "For tracking, the dataset must have a time axis with at least 2 images.   "\
                     "Please load time-series data instead. See user documentation for details." )

        if self.LabelImage.ready():
            segmentationTaggedShape = self.LabelImage.meta.getTaggedShape()        
            if segmentationTaggedShape['t'] < 2:
                raise DatasetConstraintError(
                     "Tracking",
                     "For tracking, the dataset must have a time axis with at least 2 images.   "\
                     "Please load time-series data instead. See user documentation for details." )

        if self.RawImage.ready() and self.LabelImage.ready():
            rawTaggedShape['c'] = None
            segmentationTaggedShape['c'] = None
            if dict(rawTaggedShape) != dict(segmentationTaggedShape):
                raise DatasetConstraintError("Tracking",
                     "For tracking, the raw data and the prediction maps must contain the same "\
                     "number of timesteps and the same shape.   "\
                     "Your raw image has a shape of (t, x, y, z, c) = {}, whereas your prediction image has a "\
                     "shape of (t, x, y, z, c) = {}"\
                     .format( self.RawImage.meta.shape, self.BinaryImage.meta.shape ) )
            
            
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
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
                labels_at = {}
                if t in self.labels.keys():
                    labels_at = self.labels[t]
                result[t-roi.start[0],...,0] = self._relabelUntracked(result[t-roi.start[0],...,0], labels_at)

        if slot.name == 'Annotations':
            annotations = self.Annotations[key].wait()
            result[...] = annotations

        return result
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.LabelImage:
            self.labels = {}
            self.divisions = {}
        elif slot.name == "Annotations":
            self.Annotations.setDirty( roi )
        elif slot.name == "Labels":
            self.Labels.setDirty( roi )
        elif slot.name == "Divisions":
            self.Divisions.setDirty( roi )
        else:
            self.Labels.setDirty( slice(None) )
            self.Divisions.setDirty( slice(None) )
            self.Annotations.setDirty( slice(None) )

    def _relabel(self, volume, replace):
        mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
        mp[1:] = 0
        labels = np.unique(volume).tolist()
        if 0 in labels:
            labels.remove(0)
        for label in labels:
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
        labels = np.unique(volume).tolist()
        if 0 in labels:
            labels.remove(0)
        for label in labels:
            if (label in tracked_at.keys()) and (len(tracked_at[label]) > 0):                
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
                         
            logger.info( "at timestep {}, {} traxels found".format( t, count ) )
            
        return oid2tids, alltids
