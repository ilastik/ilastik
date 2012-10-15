from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion, List
from lazyflow.stype import Opaque
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader

import h5py
import numpy
import numpy as np
import ctracking
import vigra
from ete2 import Tree, NodeStyle, TreeStyle, faces, AttrFace, TextFace
from PyQt4.QtGui import (QFont, QGraphicsSimpleTextItem, QPen, QColor,
                         QGraphicsRectItem, QTransform, QBrush)
from PyQt4.QtCore import Qt
from ete2.treeview.qt4_render import get_tree_img_map, render
from ete2.treeview.drawer import init_scene, _QApp
from ete2.treeview.main import save
from PyQt4 import QtSvg, QtCore, QtGui
from ete2.treeview.qt4_gui import _GUI

def relabel(volume, replace):
    mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
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
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List)
    ClassMapping = InputSlot(stype=Opaque, rtype=List)

    Output = OutputSlot()
#    LineageTrees = OutputSlot()
    
    def __init__(self, parent=None, graph=None):
        super(OpTrackingNN, self).__init__(parent=parent, graph=graph)
        self.label2color = []
        self.last_timerange = ()
        self.last_x_range = ()
        self.last_y_range = ()
        self.last_z_range = ()
        
        self.scene = None
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.LabelImage.meta)
#        self.LineageTrees.meta.axistags = vigra.defaultAxistags('txyzc');
    
    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            result = self.LabelImage.get(roi).wait()
            
            t = roi.start[0]
            if (self.last_timerange and t <= self.last_timerange[-1] and t >= self.last_timerange[0]):
                result[0, ..., 0] = relabel(result[0, ..., 0], self.label2color[t])
            else:
                result[...] = 0
            return result
        if slot is self.LineageTrees:
            tree = self._createLineageTrees()            
            return tree
            
            
        
    def propagateDirty(self, inputSlot, roi):
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)

    def track(self,
            time_range,
            x_range,
            y_range,
            z_range,
            size_range=(0, 100000),
            x_scale=1.0,
            y_scale=1.0,
            z_scale=1.0,
            divDist=30,
            movDist=10,
            divThreshold=0.5,
            distanceFeatures=["com"],
            splitterHandling=True):
        
        distFeatureVector = ctracking.VectorOfString();
        for d in distanceFeatures:
            distFeatureVector.append(d) 
                
        ts, filtered_labels, empty_frame = self._generate_traxelstore(time_range, x_range, y_range, z_range, size_range, x_scale, y_scale, z_scale)
        if empty_frame:
            print 'cannot track frames with 0 objects, abort.'
            return
        tracker = ctracking.NNTracking(float(divDist), float(movDist), distFeatureVector, float(divThreshold), splitterHandling)
        
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
                label2color[-1][e[0]] = np.random.randint(1, 255)

            for e in mov:
                if not label2color[-2].has_key(e[0]):
                    label2color[-2][e[0]] = np.random.randint(1, 255)
                label2color[-1][e[1]] = label2color[-2][e[0]]

            for e in div:
                if not label2color[-2].has_key(e[0]):
                    label2color[-2][e[0]] = np.random.randint(1, 255)
                ancestor_color = label2color[-2][e[0]]
                label2color[-1][e[1]] = ancestor_color
                label2color[-1][e[2]] = ancestor_color

        # mark the filtered objects
        for t in filtered_labels.keys():

            fl_at = filtered_labels[t]
            for l in fl_at:
                assert(l not in label2color[int(t)])
                label2color[int(t)][l] = 128

        self.label2color = label2color
        self.last_timerange = time_range
        self.last_x_range = x_range
        self.last_y_range = y_range
        self.last_z_range = z_range
        self.Output.setDirty(SubRegion(self.Output))
        
#        tree = self._createLineageTrees()
##        tree.write(format=1, outfile="/home/mschiegg/new_tree.nw")
##        self._plotTree(tree, "/home/mschiegg/lineagetrees.png", show_leaf_name=True, show_branch_length=True, show_division_nodes=True, width=1024)
#        
#        self.scene = self._plotTree(tree, None, width=1024, show_division_nodes=False, show_leaf_name=True)

        

    def _generate_traxelstore(self,
                               time_range,
                               x_range,
                               y_range,
                               z_range,
                               size_range,
                               x_scale=1.0,
                               y_scale=1.0,
                               z_scale=1.0):
        print "generating traxels"
        print "fetching region features and division probabilities"
        feats = self.ObjectFeatures(time_range).wait()
        divProbs = self.ClassMapping(time_range).wait()
        
        print "filling traxelstore"
        ts = ctracking.TraxelStore()
        filtered_labels = {}
        empty_frame = False
        for t in feats.keys():
            rc = feats[t]['RegionCenter']
            if rc.size:
                rc = rc[1:, ...]

            ct = feats[t]['Count']
            if ct.size:
                ct = ct[1:, ...]
            
            print "at timestep ", t, rc.shape[0], "traxels found"
            count = 0
            filtered_labels[t] = []
            for idx in range(rc.shape[0]):
                x, y, z = rc[idx]
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
                for i, v in enumerate(rc[idx]):
                    tr.set_feature_value('com', i, float(v))
                tr.add_feature_array("divProb", 1)
                # idx+1 because rc and ct start from 1, divProbs starts from 0
                tr.set_feature_value("divProb", 0, float(divProbs[t][idx+1][1]))                
                tr.add_feature_array("count", 1)
                tr.set_feature_value("count", 0, float(size))                
                ts.add(tr)            
            print "at timestep ", t, count, "traxels passed filter"
            if count == 0:
                empty_frame = True
        return ts, filtered_labels, empty_frame


    def _createLineageTrees(self):
        tree = Tree()
        
        initialFrame = 0
        
        appearances = {}        
        for t, events_at in enumerate(self.events):            
            app = []            
            for event in events_at:
                if t == 0:
                    app.append(event.traxel_ids[0])                    
                elif event.type == ctracking.EventType.Appearance:
                    app.append(event.traxel_ids[0])
                
            appearances[str(t)] = app    
        
        for t in sorted(appearances.keys(), reverse=True):
            for label in sorted(appearances[t]):
                self._addLineage(tree, self.events, initialFrame, t, label)
                  
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
#                for label in app:
#                    self._addLineage(tree, mov, div, dis, initialFrame, t, label)
                
#        plotTree(tree, options.out_fn, options.verbose_rot, options.verbose_leaf, options.verbose_branch, options.verbose_mode, options.internal, options.dist_branch, options.border, options.image_width)          
        
        return tree
    
    def _getNodeStyle(self, line_width=1, branch_type=0, node_color='DimGray', node_size=6, node_shape='circle'):
        style = NodeStyle()        
        style["hz_line_width"] = line_width
        style["vt_line_width"] = line_width
        # line type : 0 - solid, 1 - dashed, 2 - dotted
        style["hz_line_type"] = branch_type
        style["vt_line_type"] = branch_type
        style["fgcolor"] = node_color
        style["size"] = node_size
        # node shape: circle, sphere, square
        style["shape"] = node_shape
    
    
    def _getNodeName(self, frame, label):        
        name = "%s/%s" %(frame,label)     
        return name
    
     
    def _addLineage(self, tree, events, initialFrame, rootFrame, rootLabel):
        print '_addLineage ' + str(initialFrame) + ' ' + str(rootFrame) + ' ' + str(rootLabel) 
        text_rotated = False 
        initialFrame = 0
        
        style = self._getNodeStyle()
        divisionStyle = self._getNodeStyle()
        
        # making the branches from the root node to this subtree transparent    
        rootNode = tree.add_child(name=self._getNodeName(rootFrame, rootLabel), dist=5 + int(rootFrame) - int(initialFrame))
        print 'rootdistance = ' + str(2 + int(rootFrame) - int(initialFrame))       
        invisibleNodeStyle = NodeStyle()
        invisibleNodeStyle["hz_line_color"] = "white"
        invisibleNodeStyle["vt_line_color"] = "white"
        invisibleNodeStyle["fgcolor"] = "white"  
        n = rootNode
        while n:
            n.set_style(invisibleNodeStyle)
            n = n.up
        rootNode.set_style(invisibleNodeStyle)
        
        # show the label of the root node of this subtree
        name = AttrFace("name")
        name.fsize = 6
        if text_rotated is False:
            rootNode.add_face(name, column=0, position="branch-top")
        else:
            rot_text = faces.StaticItemFace(RotatedTextItem(rootNode.name, 7, "black", 270))
            rootNode.add_face(rot_text, column=0, position="branch-top")
        
        nodeMap = { str(rootLabel) : rootNode }
        branchSize = { str(rootLabel) : 0 }
        
#        events_at = events[int(rootFrame) - int(initialFrame):]
        
        for frame, events_at in enumerate(events[int(rootFrame) - int(initialFrame) + 1:]):
            frame += initialFrame
            for event in events_at:
                if str(event.traxel_ids[0]) not in nodeMap.keys():
                    continue
                print 'frame ' + str(frame) + ', label ' + str(event.traxel_ids[0])
                if event.type == ctracking.EventType.Disappearance:
                    label = event.traxel_ids[0]
                    print 'dis = ' + str(label) + ' ' +str(branchSize[str(label)])
                    newNode = nodeMap[str(label)].add_child(name = self._getNodeName(frame,str(label)),dist = branchSize[str(label)])                     
                    newNode.set_style(style)
                    del nodeMap[str(label)]
                    del branchSize[str(label)]
                    break
                if event.type == ctracking.EventType.Division:
                    labelOld = event.traxel_ids[0]
                    labelNew1 = event.traxel_ids[1]
                    labelNew2 = event.traxel_ids[2]
                    print 'div = ' + str(labelOld) + ' ' +str(labelNew1) + ' '+ str(labelNew2) + ' '+ str(branchSize[str(labelOld)])
                    newNode = nodeMap[str(labelOld)].add_child(name = self._getNodeName(frame-1,str(labelOld)),dist = branchSize[str(labelOld)])
                    del nodeMap[str(labelOld)]
                    del branchSize[str(labelOld)]
                    newNode.set_style(divisionStyle)
                    nodeMap[str(labelNew1)] = newNode
                    nodeMap[str(labelNew2)] = newNode
                    branchSize[str(labelNew1)] = 0
                    branchSize[str(labelNew2)] = 0
                if event.type == ctracking.EventType.Move:
                    labelOld = event.traxel_ids[0]
                    labelNew = event.traxel_ids[1]
                    print 'mov = ' + str(labelOld) + ' ' +str(labelNew)  + ' '+ str(branchSize[str(labelOld)])
                    nodeMap[str(labelNew)] = nodeMap[str(labelOld)]
                    del nodeMap[str(labelOld)]
                    branchSize[str(labelNew)] = branchSize[str(labelOld)] + 1 
                    del branchSize[str(labelOld)]

        for label in nodeMap.keys():
            newNode = nodeMap[label].add_child(name = self._getNodeName(frame,str(label)),dist = branchSize[label])
        
        return tree
            
            
#            # frame = frame + initialframe???
#            while ['-1'] in previousLabels:
#                previousLabels.remove(['-1'])    
#            nextLabels = [] 
#            # the empty nextLabels list is filled with the next label if exists,or with -1 if not 
#            for l in previousLabels:
#                if str(l[0]) in events[previousFrame].keys():
#                    nextLabels.append(data[previousFrame][str(l[0])])
#                else:
#                    nextLabels.append([-1]) 
#           # the newIdx corresponds to the new lists created 
#           newIdx = 0 
#           for idx, label in enumerate(previousLabels):   
#              # at the last frame, are added the nodes corresponding to each elements from the nodeList   
#              if frame == sorted(data.keys())[-1]: 
#                 n = nodeList[idx].add_child(name=getNodeName(frame, str(previousLabels[idx][0])), dist=1 + branchList[idx]) 
#                 n.set_style(style)
#              # division of the cell 
#              elif len(nextLabels[idx]) == 2 and nextLabels[idx] != [-1]:
#                 # add the node which divides at the tree
#                 divisionNode = nodeList[idx].add_child(name=getNodeName(previousFrame, str(previousLabels[idx][0])),
#                    dist=branchList[idx])
#                 divisionNode.set_style(divisionStyle)
#                 n1 = divisionNode
#                 n2 = divisionNode 
#                 newnodeList[newIdx] = n1
#                 newnodeList.insert(newIdx + 1, n2) 
#                 # split the element with idx from nextLabels, in 1-dimension lists
#                 nextLabels[idx] = split_list(nextLabels[idx], len(nextLabels[idx])) 
#                 newbranchList[newIdx] = 1       
#                 newbranchList.insert(newIdx + 1, 1)
#                 # update the previousLabels list with the elements from the nextLabels list,transformed in strings
#                 previousLabels[idx] = [str(l[0]) for l in nextLabels[idx]]
#                 newIdx += 2
#              # if the cell dissapears in the next frame, add the cell as a node 
#              elif nextLabels[idx] == [-1]:
#                 n = nodeList[idx].add_child(name=getNodeName(previousFrame, str(previousLabels[idx][0])), dist=branchList[idx]) 
#                 n.set_style(style)
#                 # remove the element with idx from the newnodeList and from the newbranchList
#                 newnodeList.remove(nodeList[idx])
#                 newbranchList.remove(branchList[idx])
#                 # mark the element with idx, with '-1' in the previousLabels list
#                 previousLabels[idx] = ['-1']    
#              # otherwise, increase the length of the branch by 1    
#              else:
#                 newbranchList[newIdx] += 1           
#                 previousLabels[idx] = [str(l) for l in nextLabels[idx]]  
#                 newIdx += 1
#           # creates a list formed only by 1-dimension lists 
#           newpreviousLabels = []
#           for sublist in previousLabels:   
#              for el in sublist:
#                 newpreviousLabels.append([str(el)])
#           previousLabels = newpreviousLabels             
#           nodeList = newnodeList[:]
#           branchList = newbranchList[:]
#           # update previousFrame              
#           previousFrame = frame  
#        return tree
    def _plotTree(self, tree, out_fn=None, rotation=90, show_leaf_name=False, 
                  show_branch_length=False, circularTree=False, show_division_nodes=True, 
                  distance_between_branches=4, show_border=False, width=1024):              
        ts = TreeStyle()   
        ts.show_scale = False
        ts.show_border = show_border
        ts.rotation = rotation
        ts.show_leaf_name = show_leaf_name
        ts.show_branch_length = show_branch_length
        if circularTree:
            ts.mode = 'c'
        else:
            ts.mode = 'r'
        ts.branch_vertical_margin = distance_between_branches
        
        
        def hideInternalNodesLayout(node):
            if not node.is_leaf():
                node.img_style["size"] = 0
        
        if show_division_nodes is False:
            ts.layout_fn = hideInternalNodesLayout
        
#        if out_fn is not None:        
#            scene, img = init_scene(tree, None, ts)
#            tree_item, n2i, n2f = render(tree, img)
#            scene.init_data(tree, img, n2i, n2f)
#            tree_item.setParentItem(scene.master_item)
#            scene.master_item.setPos(0,0)
#            scene.addItem(scene.master_item)            
#            save(scene, out_fn, w=width, h=None, units="mm")
#        else:
        scene, img = init_scene(tree, None, ts)
        tree_item, n2i, n2f = render(tree, img)
        scene.init_data(tree, img, n2i, n2f)
    
        tree_item.setParentItem(scene.master_item)
        scene.addItem(scene.master_item)
    
        size = tree_item.rect()
        w, h = size.width(), size.height()
    
        svg = QtSvg.QSvgGenerator()
        svg.setFileName("test.svg")
        svg.setSize(QtCore.QSize(w, h))
        svg.setViewBox(size)
        pp = QtGui.QPainter()
        pp.begin(svg)
        #pp.setRenderHint(QtGui.QPainter.Antialiasing)
        #pp.setRenderHint(QtGui.QPainter.TextAntialiasing)
        #pp.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        scene.render(pp, tree_item.rect(), tree_item.rect(), QtCore.Qt.KeepAspectRatio)
#            pp.end()
#            img = QtSvg.QGraphicsSvgItem("test.svg")
#            #img.setParentItem(scene.master_item)
#            #scene.removeItem(tree_item)
#            #tree_item.setVisible(False)
#        
#            print 'mainapp'
#            mainapp = _GUI(scene)
#            print 'mainapp.show()'
#            mainapp.show()
#            print 'show() successful'
#            _QApp.exec_()
#            print 'qexec()'
        return scene
            



class RotatedTextItem(QGraphicsRectItem):
    def __init__(self, text, size, color, rotation=90):
            QGraphicsRectItem.__init__(self)
            self.text_item = QGraphicsSimpleTextItem(text)
            self.text_item.setParentItem(self)
            self.text_item.setFont(QFont("arial", size))
            self.text_item.setBrush(QBrush(QColor(color)))
            self.rotate(rotation)
            self.setRect(self.text_item.boundingRect())
            self.setPen(QPen(Qt.NoPen))
           
    def rotate(self, rotation):
            "rotates item over its own center"
            rect = self.text_item.boundingRect()
            x =  rect.width()/2.
            y =  rect.height()/2.
            self.text_item.setTransform(QTransform().translate(x, y).rotate(rotation).translate(-x, -y))