import h5py
import numpy as np
import os.path as path
import pgmlink


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
#    mp[replace.keys()] = replace.values()
    return mp[volume]
    
    
def relabelMergers(volume, merger):
    mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)    
    mp[:] = 0
    labels = np.unique(volume)
    for label in labels:
        if label > 0:
            if label in merger:
                mp[label] = merger[label]
            else:
                mp[label] = 1
    return mp[volume]


def write_events(events, directory, t, labelImage, mergers=None):
        fn =  directory + "/" + str(t).zfill(5)  + ".h5"
        
        dis = []
        app = []
        div = []
        mov = []
        merger = []       
            
        print "-- Writing results to " + path.basename(fn)
        if mergers is not None:
            for m in mergers[t].keys():
                merger.append((m,mergers[t][m],0.0))
                 
        for event in events:
            if event.type == pgmlink.EventType.Appearance:
                app.append((event.traxel_ids[0], event.energy))
            if event.type == pgmlink.EventType.Disappearance:
                dis.append((event.traxel_ids[0], event.energy))
            if event.type == pgmlink.EventType.Division:
                div.append((event.traxel_ids[0], event.traxel_ids[1], event.traxel_ids[2], event.energy))
            if event.type == pgmlink.EventType.Move:
                mov.append((event.traxel_ids[0], event.traxel_ids[1], event.energy))
#            if event.type == pgmlink.EventType.Merger:
#                merger.append((event.traxel_ids[0], event.traxel_ids[1], event.energy))
    
        # convert to ndarray for better indexing
        dis = np.asarray(dis)
        app = np.asarray(app)
        div = np.asarray(div)
        mov = np.asarray(mov)
        merger = np.asarray(merger)
    
        
        
        # write only if file exists
        with LineageH5(fn, 'a') as f_curr:
            # delete old label image
            if "segmentation" in f_curr.keys():
                del f_curr["segmentation"]
            
            seg = f_curr.create_group("segmentation")            
            # write label image
#            seg.create_dataset("labels", data = labelImage[t,...,0], dtype=np.uint32, compression=1)
            seg.create_dataset("labels", data = labelImage, dtype=np.uint32, compression=1)
            
            # delete old tracking
            if "tracking" in f_curr.keys():
                del f_curr["tracking"]

            tg = f_curr.create_group("tracking")            
            
            # write associations
            if len(app):
                ds = tg.create_dataset("Appearances", data=app[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "cell label appeared in current file"    
                ds = tg.create_dataset("Appearances-Energy", data=app[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"    
            if len(dis):
                ds = tg.create_dataset("Disappearances", data=dis[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "cell label disappeared in current file"
                ds = tg.create_dataset("Disappearances-Energy", data=dis[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"    
            if len(mov):
                ds = tg.create_dataset("Moves", data=mov[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "from (previous file), to (current file)"    
                ds = tg.create_dataset("Moves-Energy", data=mov[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"                
            if len(div):
                ds = tg.create_dataset("Splits", data=div[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "ancestor (previous file), descendant (current file), descendant (current file)"    
                ds = tg.create_dataset("Splits-Energy", data=div[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"
            if len(merger):
                ds = tg.create_dataset("Mergers", data=merger[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "descendant (current file), number of objects"    
                ds = tg.create_dataset("Mergers-Energy", data=merger[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"
    
        print "-> results successfully written"


class LineageTrees():

    def createLineageTrees(self, fn=None, width=None, height=None, circular=False, withAppearing=True, from_t=0, to_t=0):
        from ete2 import Tree, NodeStyle, AttrFace
        
        tree = Tree()        
        style = self.getNodeStyle()
        divisionStyle = self.getNodeStyle()
        
        invisibleNodeStyle = NodeStyle()
        invisibleNodeStyle["hz_line_color"] = "white"
        invisibleNodeStyle["vt_line_color"] = "white"
        invisibleNodeStyle["fgcolor"] = "white"
        
        distanceFromRoot = 0
        
        nodeMap = {}
        branchSize = {}
        
        # add all nodes which appear in the first frame
        for event in self.mainOperator.innerOperators[0].events[from_t]:
            if event.type != pgmlink.EventType.Appearance:
                label = event.traxel_ids[0]
                appNode = tree.add_child(name=self.getNodeName(0, label), dist=distanceFromRoot )
                nodeMap[str(self.getNodeName(0, label))] = appNode
                branchSize[str(self.getNodeName(0, label))] = 0                    
                # making the branches to the root node invisible
                n = appNode
                while n:
                    n.set_style(invisibleNodeStyle)
                    n = n.up
                appNode.set_style(invisibleNodeStyle)
                name = AttrFace("name")
                name.fsize = 6
        
        # add all lineages
        for t, events_at in enumerate(self.mainOperator.innerOperators[0].events[from_t:to_t+1]):
            t = t+1            
            for event in events_at:
                if event.type == pgmlink.EventType.Appearance and withAppearing:
                    label = event.traxel_ids[0]
                    appNode = tree.add_child(name=self.getNodeName(t, label), dist=distanceFromRoot + t)
                    nodeMap[str(self.getNodeName(t, label))] = appNode
                    branchSize[str(self.getNodeName(t, label))] = 0                    
                    # making the branches to the root node invisible
                    n = appNode
                    while n:
                        n.set_style(invisibleNodeStyle)
                        n = n.up
                    appNode.set_style(invisibleNodeStyle)
                    name = AttrFace("name")
                    name.fsize = 6

                elif event.type == pgmlink.EventType.Disappearance:
                    label = event.traxel_ids[0]
                    if str(self.getNodeName(t-1,str(label))) not in nodeMap.keys():
                        continue
                    if branchSize[str(self.getNodeName(t-1,str(label)))] == 0:
                        del nodeMap[str(self.getNodeName(t-1,str(label)))]
                        del branchSize[str(self.getNodeName(t-1,str(label)))]
                        continue
                    newNode = nodeMap[str(self.getNodeName(t-1,str(label)))].add_child(
                        name = self.getNodeName(t-1,str(label)),dist = branchSize[str(self.getNodeName(t-1,str(label)))])                     
                    newNode.set_style(style)
                    del nodeMap[str(self.getNodeName(t-1,str(label)))]
                    del branchSize[str(self.getNodeName(t-1,str(label)))]
                    
                elif event.type == pgmlink.EventType.Division:
                    labelOld = event.traxel_ids[0]
                    labelNew1 = event.traxel_ids[1]
                    labelNew2 = event.traxel_ids[2]                    
                    if str(self.getNodeName(t-1,str(labelOld))) not in nodeMap.keys():
                        continue
                    newNode = nodeMap[str(self.getNodeName(t-1,str(labelOld)))].add_child(
                            name = self.getNodeName(t-1,str(self.getNodeName(t-1,str(labelOld)))),
                            dist = branchSize[str(self.getNodeName(t-1,str(labelOld)))] )
                    del nodeMap[str(self.getNodeName(t-1,str(labelOld)))]
                    del branchSize[str(self.getNodeName(t-1,str(labelOld)))]
                    newNode.set_style(divisionStyle)
                    nodeMap[str(self.getNodeName(t,str(labelNew1)))] = newNode
                    nodeMap[str(self.getNodeName(t,str(labelNew2)))] = newNode
                    branchSize[str(self.getNodeName(t,str(labelNew1)))] = 1
                    branchSize[str(self.getNodeName(t,str(labelNew2)))] = 1                    
                    
                elif event.type == pgmlink.EventType.Move:
                    labelOld = event.traxel_ids[0]
                    labelNew = event.traxel_ids[1]
                    if str(self.getNodeName(t-1,str(labelOld))) not in nodeMap.keys():
                        continue
                    nodeMap[str(self.getNodeName(t,str(labelNew)))] = nodeMap[str(self.getNodeName(t-1,str(labelOld)))]
                    del nodeMap[str(self.getNodeName(t-1,str(labelOld)))]
                    branchSize[str(self.getNodeName(t,str(labelNew)))] = branchSize[str(self.getNodeName(t-1,str(labelOld)))] + 1 
                    del branchSize[str(self.getNodeName(t-1,str(labelOld)))]
                
                else:
                    raise Exception, "lineage tree generation not implemented for event type " + str(event.type)

        for label in nodeMap.keys():            
            newNode = nodeMap[label].add_child(name = label,dist = branchSize[label])
        
        self.plotTree(tree, out_fn=fn, rotation=270, show_leaf_name=False, 
                  show_branch_length=False, circularTree=circular, show_division_nodes=False, 
                  distance_between_branches=4, width=width, height=height)
    
    
    def getNodeStyle(self, line_width=1, branch_type=0, node_color='DimGray', node_size=6, node_shape='circle'):
        from ete2 import NodeStyle
    
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
    
    def getNodeName(self, frame, label):        
        name = "%s/%s" %(frame,label)     
        return name

    def plotTree(self, tree, out_fn=None, rotation=270, show_leaf_name=False, 
                  show_branch_length=False, circularTree=False, show_division_nodes=True, 
                  distance_between_branches=4, show_border=False, width=None, height=None):            
        from ete2 import TreeStyle        
        from PyQt4 import QtSvg, QtCore, QtGui
        from ete2.treeview import qt4_render, drawer, main
        
          
        ts = TreeStyle()   
        ts.show_scale = False
        ts.show_border = show_border
        ts.orientation = 1 # 0, tree is drawn from left-to-right. 1, tree is drawn from right-to-left
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
        
        if out_fn is not None:        
            scene  = qt4_render._TreeScene()
            img = ts
            
            tree_item, n2i, n2f = qt4_render.render(tree, img)
            scene.init_data(tree, img, n2i, n2f)
            tree_item.setParentItem(scene.master_item)
            scene.master_item.setPos(0,0)
            scene.addItem(scene.master_item)      
            main.save(scene, out_fn, w=width, h=height, dpi=600)    
              
        else:
            scene, img = drawer.init_scene(tree, None, ts)
            tree_item, n2i, n2f = qt4_render.render(tree, img)
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
            scene.render(pp, tree_item.rect(), tree_item.rect(), QtCore.Qt.KeepAspectRatio)


class LineageH5( h5py.File ):
    mov_ds = "/tracking/Moves"
    mov_ener_ds = "/tracking/Moves-Energy"
    app_ds = "/tracking/Appearances"
    app_ener_ds = "/tracking/Appearances-Energy"
    dis_ds = "/tracking/Disappearances"
    dis_ener_ds = "/tracking/Disappearances-Energy"
    div_ds = "/tracking/Splits"
    div_ener_ds = "/tracking/Splits-Energy"
    merg_ds = "/tracking/Mergers"
    merg_ener_ds = "/tracking/Mergers-Energy"
    feat_gn = "/features"
    track_gn = "/tracking/"    

    @property
    def x_scale( self ):
        return self._x_scale
    @x_scale.setter
    def x_scale( self, scale ):
        self._x_scale = scale

    @property
    def y_scale( self ):
        return self._y_scale
    @y_scale.setter
    def y_scale( self, scale ):
        self._y_scale = scale

    @property
    def z_scale( self ):
        return self._z_scale
    @z_scale.setter
    def z_scale( self, scale ):
        self._z_scale = scale
        
    # timestep will be set in loaded traxels accordingly
    def __init__( self, *args, **kwargs):
        h5py.File.__init__(self, *args, **kwargs)
        if "timestep" in kwargs:
            self.timestep = kwargs["timestep"]
        else:
            self.timestep = 0
        
        self._x_scale = 1.0
        self._y_scale = 1.0
        self._z_scale = 1.0

    def init_tracking( self, div=np.empty(0), mov=np.empty(0), dis=np.empty(0), app=np.empty(0)):
        if "tracking" in self.keys():
            del self["tracking"]
        self.create_group("tracking")

    def has_tracking( self ):
        if "tracking" in self.keys():
            return True
        else:
            return False
            
    def add_move( self, from_id, to_id):
        n_moves = self[self.mov_ds].shape[0];
        movs = self.get_moves()
        new = np.vstack([movs, (from_id, to_id)])
        self.update_moves(new)

    def update_moves( self, mov_pairs ):
        if path.basename(self.mov_ds) in self[self.track_gn].keys():
            del self[self.mov_ds]
        if len(mov_pairs) > 0:
            self[self.track_gn].create_dataset("Moves", data=np.asarray( mov_pairs, dtype=np.int32))

    def get_moves( self ):
        if self.has_tracking() and path.basename(self.mov_ds) in self[self.track_gn].keys():
            return self[self.mov_ds].value
        else:
            return np.empty(0)
    def get_move_energies( self ):
        if path.basename(self.mov_ener_ds) in self[self.track_gn].keys():
            e = self[self.mov_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)
        

    def get_divisions( self ):
        if self.has_tracking() and path.basename(self.div_ds) in self[self.track_gn].keys():
            return self[self.div_ds].value
        else:
            return np.empty(0)

    def update_divisions( self, div_triples ):
        if path.basename(self.div_ds) in self[self.track_gn].keys():
            del self[self.div_ds]
        if len(div_triples) > 0:
            self[self.track_gn].create_dataset("Splits", data=np.asarray( div_triples, dtype=np.int32))

    def get_division_energies( self ):
        if path.basename(self.div_ener_ds) in self[self.track_gn].keys():
            e = self[self.div_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)

    def get_disappearances( self ):
        if self.has_tracking() and path.basename(self.dis_ds) in self[self.track_gn].keys():
            dis = self[self.dis_ds].value
            if isinstance(dis, np.ndarray):
                return dis
            else:
                return np.array([dis])
        else:
            return np.empty(0)

    def update_disappearances( self, dis_singlets ):
        if path.basename(self.dis_ds) in self[self.track_gn].keys():
            del self[self.dis_ds]
        if len(dis_singlets) > 0:
            self[self.track_gn].create_dataset("Disappearances", data=np.asarray( dis_singlets, dtype=np.int32))
        
    def get_disappearance_energies( self ):
        if path.basename(self.dis_ener_ds) in self[self.track_gn].keys():
            e = self[self.dis_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)


    def get_appearances( self ):
        if self.has_tracking() and path.basename(self.app_ds) in self[self.track_gn].keys():
            app = self[self.app_ds].value
            if isinstance(app, np.ndarray):
                return app
            else:
                return np.array([app])
        else:
            return np.empty(0)

    def update_appearances( self, app_singlets ):
        if path.basename(self.app_ds) in self[self.track_gn].keys():
            del self[self.app_ds]
        if len(app_singlets) > 0:
            self[self.track_gn].create_dataset("Appearances", data=np.asarray( app_singlets, dtype=np.int32))

    def get_appearance_energies( self ):
        if path.basename(self.app_ener_ds) in self[self.track_gn].keys():
            e = self[self.app_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)

    def rm_appearance( self, id ):
        apps = self.get_appearances()
        if not id in apps:
            raise Exception("LineageH5::rm_appearance(): id %d not an appearance" % id)
        filtered = apps[apps!=id]
        b = np.empty(dtype=apps.dtype, shape=(filtered.shape[0], 1))
        b[:,0] = filtered[:]
        self.update_appearances( b )

    def rm_disappearance( self, id ):
        diss = self.get_disappearances()
        if not id in diss:
            raise Exception("LineageH5::rm_disappearance(): id %d not an disappearance" % id)
        filtered = diss[diss!=id]
        b = np.empty(dtype=diss.dtype, shape=(filtered.shape[0], 1))
        b[:,0] = filtered[:]
        self.update_disappearances( b )

    def get_ids( self ):
        features_group = self[self.feat_gn]
        labelcontent = features_group["labelcontent"].value
        valid_labels = (np.arange(len(labelcontent))+1)[labelcontent==1]
        return valid_labels

    def Traxels( self , timestep=None, position='mean', add_features_as_meta=True):
        return self.Tracklets( timestep, position, add_features_as_meta )
