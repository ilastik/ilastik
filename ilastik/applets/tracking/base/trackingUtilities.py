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
from builtins import range
import h5py
import numpy as np
import os.path as path
import vigra

import logging
logger = logging.getLogger(__name__)

def relabel(volume, replace):
    mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
    mp[1:] = 1
    labels = np.sort(vigra.analysis.unique(volume))
    for label in labels:
        if label > 0:
            try:
                r = replace[label]
                mp[label] = r
            except:                
                pass
#    mp[replace.keys()] = replace.values()
    return mp[volume]

def get_dict_value(dic, key, default=[]):
    if key not in dic:
        return default
    else:
        return dic[key]

def write_dict_value(dic, key, value):
    if len(value) == 0:
        return
    else:
        dic[key] = value
    return dic

def write_events(events_at, directory, t, labelImage):
        fn =  directory + "/" + str(t).zfill(5)  + ".h5"
        
        logger.info( "-- Writing results to " + path.basename(fn) ) 
        if len(events_at) == 0:
            dis = []
            app = []
            mov = []
            div = []
            merger = []
            res = {}
        else:        
            dis = get_dict_value(events_at, "dis", [])
            app = get_dict_value(events_at, "app", [])
            mov = get_dict_value(events_at, "mov", [])
            div = get_dict_value(events_at, "div", [])
            merger = get_dict_value(events_at, "merger", [])
            res = get_dict_value(events_at, "res", {})
        try:
            with LineageH5(fn, 'w-') as f_curr:
                # delete old label image
                if "segmentation" in list(f_curr.keys()):
                    del f_curr["segmentation"]
                
                seg = f_curr.create_group("segmentation")            
                # write label image
                seg.create_dataset("labels", data = labelImage, dtype=np.uint32, compression=1)
                
                # delete old tracking
                if "tracking" in list(f_curr.keys()):
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
                if len(res):
                    rg = tg.create_group("ResolvedMergers")
                    rg.attrs["Format"] = "old cell label (current file), new cell labels of resolved cells (current file)"
                    for k, v in res.items():
                        rg.create_dataset(str(k), data=v[:-1], dtype=np.uint32, compression=1)
        except IOError:                    
            raise IOError("File " + str(fn) + " exists already. Please choose a different folder or delete the file(s).")
                
    
        logger.info( "-> results successfully written" )


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
        if "tracking" in list(self.keys()):
            del self["tracking"]
        self.create_group("tracking")

    def has_tracking( self ):
        if "tracking" in list(self.keys()):
            return True
        else:
            return False
            
    def add_move( self, from_id, to_id):
        n_moves = self[self.mov_ds].shape[0];
        movs = self.get_moves()
        new = np.vstack([movs, (from_id, to_id)])
        self.update_moves(new)

    def update_moves( self, mov_pairs ):
        if path.basename(self.mov_ds) in list(self[self.track_gn].keys()):
            del self[self.mov_ds]
        if len(mov_pairs) > 0:
            self[self.track_gn].create_dataset("Moves", data=np.asarray( mov_pairs, dtype=np.int32))

    def get_moves( self ):
        if self.has_tracking() and path.basename(self.mov_ds) in list(self[self.track_gn].keys()):
            return self[self.mov_ds].value
        else:
            return np.empty(0)
    def get_move_energies( self ):
        if path.basename(self.mov_ener_ds) in list(self[self.track_gn].keys()):
            e = self[self.mov_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)
        

    def get_divisions( self ):
        if self.has_tracking() and path.basename(self.div_ds) in list(self[self.track_gn].keys()):
            return self[self.div_ds].value
        else:
            return np.empty(0)

    def update_divisions( self, div_triples ):
        if path.basename(self.div_ds) in list(self[self.track_gn].keys()):
            del self[self.div_ds]
        if len(div_triples) > 0:
            self[self.track_gn].create_dataset("Splits", data=np.asarray( div_triples, dtype=np.int32))

    def get_division_energies( self ):
        if path.basename(self.div_ener_ds) in list(self[self.track_gn].keys()):
            e = self[self.div_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)

    def get_disappearances( self ):
        if self.has_tracking() and path.basename(self.dis_ds) in list(self[self.track_gn].keys()):
            dis = self[self.dis_ds].value
            if isinstance(dis, np.ndarray):
                return dis
            else:
                return np.array([dis])
        else:
            return np.empty(0)

    def update_disappearances( self, dis_singlets ):
        if path.basename(self.dis_ds) in list(self[self.track_gn].keys()):
            del self[self.dis_ds]
        if len(dis_singlets) > 0:
            self[self.track_gn].create_dataset("Disappearances", data=np.asarray( dis_singlets, dtype=np.int32))
        
    def get_disappearance_energies( self ):
        if path.basename(self.dis_ener_ds) in list(self[self.track_gn].keys()):
            e = self[self.dis_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)


    def get_appearances( self ):
        if self.has_tracking() and path.basename(self.app_ds) in list(self[self.track_gn].keys()):
            app = self[self.app_ds].value
            if isinstance(app, np.ndarray):
                return app
            else:
                return np.array([app])
        else:
            return np.empty(0)

    def update_appearances( self, app_singlets ):
        if path.basename(self.app_ds) in list(self[self.track_gn].keys()):
            del self[self.app_ds]
        if len(app_singlets) > 0:
            self[self.track_gn].create_dataset("Appearances", data=np.asarray( app_singlets, dtype=np.int32))

    def get_appearance_energies( self ):
        if path.basename(self.app_ener_ds) in list(self[self.track_gn].keys()):
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
