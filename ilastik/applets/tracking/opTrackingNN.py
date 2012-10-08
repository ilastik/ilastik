from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion, List
from lazyflow.stype import Opaque
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader

import h5py
import numpy
import numpy as np
import ctracking
import vigra
from ete2 import Tree,NodeStyle,TreeStyle,faces,AttrFace,TextFace
from PyQt4.QtGui import (QFont, QGraphicsSimpleTextItem, QPen, QColor,
                         QGraphicsRectItem, QTransform, QBrush)
from PyQt4.QtCore import Qt

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

class OpTrackingNN(Operator):
    name = "Tracking"
    category = "other"

    LabelImage = InputSlot()
    ObjectFeatures = InputSlot( stype=Opaque, rtype=List )
    ClassMapping = InputSlot( stype=Opaque, rtype=List )

    Output = OutputSlot()
#    LineageTrees = OutputSlot()

    def __init__( self, parent = None, graph = None ):
        super(OpTrackingNN, self).__init__(parent=parent,graph=graph)
        self.label2color = []
        self.last_timerange = ()
        self.last_x_range = ()
        self.last_y_range = ()
        self.last_z_range = ()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.LabelImage.meta )
#        self.LineageTrees.meta.axistags = vigra.defaultAxistags('txyzc');
    
    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            result = self.LabelImage.get(roi).wait()
            
            t = roi.start[0]
            if (self.last_timerange and t <= self.last_timerange[-1] and t >= self.last_timerange[0]):
                result[0,...,0] = relabel( result[0,...,0], self.label2color[t] )
            else:
                result[...] = 0
            return result
        if slot is self.LineageTrees:
            tree = self._createLineageTrees()
            return tree
            
            
        
    def propagateDirty(self, inputSlot, roi):
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
            divDist = 30,
            movDist = 10):

        

        ts, filtered_labels = self._generate_traxelstore( time_range, x_range, y_range, z_range, size_range, x_scale, y_scale, z_scale )
        tracker = ctracking.NNTracking(divDist,movDist)
        
        self.events = tracker(ts)
        label2color = []
        label2color.append({})

        # handle start time offsets
        for i in range(time_range[0]):
            label2color.append({})

        for i, events_at in enumerate(self.events):
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
        print "fetching region features and division probabilities"
        feats = self.ObjectFeatures( time_range ).wait()
        divProbs = self.ClassMapping( time_range ).wait()
        
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
                tr.add_feature_array("divProb", 1)                    
                tr.set_feature_value("divProb", 0, divProbs[t][idx][1])
                ts.add(tr)
            print "at timestep ", t, count, "traxels passed filter"
        return ts, filtered_labels


    def _createLineageTrees(self):
        tree = Tree()
        
#        for t, events_at in enumerate(self.events):
#            dis = []
#            app = []
#            div = []
#            mov = []
#            for event in events_at:
#                if event.type == ctracking.EventType.Appearance:
#                    app.append((event.traxel_ids[0], event.energy))
#                if event.type == ctracking.EventType.Disappearance:
#                    dis.append((event.traxel_ids[0], event.energy))
#                if event.type == ctracking.EventType.Division:
#                    div.append((event.traxel_ids[0], event.traxel_ids[1], event.traxel_ids[2], event.energy))
#                if event.type == ctracking.EventType.Move:
#                    mov.append((event.traxel_ids[0], event.traxel_ids[1], event.energy))
#                    
#                for label in list(reversed(sorted(appearances[frame],key=lambda a:map(int,a.split('.'))))): 
#            addLineage(data,tree,initialFrame,frame,label,options.line_width,options.branch_type,options.node_color,
#               options.node_size, options.node_shape)
#      plotTree(tree, options.out_fn, options.verbose_rot,options.verbose_leaf, options.verbose_branch, 
#         options.verbose_mode, options.internal, options.dist_branch,options.border, options.image_width)  
        
        
        return tree