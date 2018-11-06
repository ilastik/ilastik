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
from typing import TYPE_CHECKING

from builtins import range
from ilastik.applets.base.appletSerializer import (
    AppletSerializer, getOrCreateGroup, deleteIfPresent, SerialSlot
)
import numpy

from lazyflow.roi import roiFromShape, roiToSlice

import logging
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .opCarving import OpCarving


class CarvingSerializer(AppletSerializer):
    def __init__(self, operator: 'OpCarving', groupName):
        super().__init__(groupName, slots=[
            SerialSlot(operator.ObjectPrefix)
        ])
        self._o = operator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        obj = getOrCreateGroup(topGroup, "objects")
        for imageIndex, opCarving in enumerate( self._o.innerOperators ):
            mst = opCarving._mst

            # Populate a list of objects to save:
            objects_to_save = set(list(mst.object_names.keys()))
            objects_already_saved = set(list(topGroup["objects"]))
            # 1.) all objects that are in mst.object_names that are not in saved
            objects_to_save = objects_to_save.difference(objects_already_saved)

            # 2.) add opCarving._dirtyObjects:
            objects_to_save = objects_to_save.union(opCarving._dirtyObjects)

            for name in objects_to_save:
                logger.info( "[CarvingSerializer] serializing %s" % name )
               
                if name in obj and name in mst.object_seeds_fg_voxels: 
                    #group already exists
                    logger.info( "  -> changed" )
                elif name not in mst.object_seeds_fg_voxels:
                    logger.info( "  -> deleted" )
                else:
                    logger.info( "  -> added" )
                    
                g = getOrCreateGroup(obj, name)
                deleteIfPresent(g, "fg_voxels")
                deleteIfPresent(g, "bg_voxels")
                deleteIfPresent(g, "sv")
                deleteIfPresent(g, "bg_prio")
                deleteIfPresent(g, "no_bias_below")
                
                if not name in mst.object_seeds_fg_voxels:
                    #this object was deleted
                    deleteIfPresent(obj, name)
                    continue
               
                v = mst.object_seeds_fg_voxels[name]
                v = [v[i][:,numpy.newaxis] for i in range(3)]
                v = numpy.concatenate(v, axis=1)
                g.create_dataset("fg_voxels", data=v)
                v = mst.object_seeds_bg_voxels[name]
                v = [v[i][:,numpy.newaxis] for i in range(3)]
                v = numpy.concatenate(v, axis=1)
                g.create_dataset("bg_voxels", data=v)
                g.create_dataset("sv", data=mst.object_lut[name])
                
                d1 = numpy.asarray(mst.bg_priority[name], dtype=numpy.float32)
                d2 = numpy.asarray(mst.no_bias_below[name], dtype=numpy.int32)
                g.create_dataset("bg_prio", data=d1)
                g.create_dataset("no_bias_below", data=d2)
                
            opCarving._dirtyObjects = set()
        
            # save current seeds
            deleteIfPresent(topGroup, "fg_voxels")
            deleteIfPresent(topGroup, "bg_voxels")

            fg_voxels, bg_voxels = opCarving.get_label_voxels()
            if fg_voxels is None:
                return

            if fg_voxels[0].shape[0] > 0:
                v = [fg_voxels[i][:,numpy.newaxis] for i in range(3)]
                v = numpy.concatenate(v, axis=1)
                topGroup.create_dataset("fg_voxels", data = v)

            if bg_voxels[0].shape[0] > 0:
                v = [bg_voxels[i][:,numpy.newaxis] for i in range(3)]
                v = numpy.concatenate(v, axis=1)
                topGroup.create_dataset("bg_voxels", data = v)

            logger.info( "saved seeds" )
        
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        obj = topGroup["objects"]
        for imageIndex, opCarving in enumerate( self._o.innerOperators ):
            mst = opCarving._mst 
            
            for i, name in enumerate(obj):
                logger.info( " loading object with name='%s'" % name )
                try:
                    g = obj[name]
                    fg_voxels = g["fg_voxels"]
                    bg_voxels = g["bg_voxels"]
                    fg_voxels = [fg_voxels[:,k] for k in range(3)]
                    bg_voxels = [bg_voxels[:,k] for k in range(3)]
                    
                    sv = g["sv"].value
                  
                    mst.object_names[name]           = i+1 
                    mst.object_seeds_fg_voxels[name] = fg_voxels
                    mst.object_seeds_bg_voxels[name] = bg_voxels
                    mst.object_lut[name]             = sv
                    mst.bg_priority[name]            = g["bg_prio"].value
                    mst.no_bias_below[name]          = g["no_bias_below"].value
                    
                    logger.info( "[CarvingSerializer] de-serializing %s, with opCarving=%d, mst=%d" % (name, id(opCarving), id(mst)) )
                    logger.info( "  %d voxels labeled with green seed" % fg_voxels[0].shape[0] ) 
                    logger.info( "  %d voxels labeled with red seed" % bg_voxels[0].shape[0] ) 
                    logger.info( "  object is made up of %d supervoxels" % sv.size )
                    logger.info( "  bg priority = %f" % mst.bg_priority[name] )
                    logger.info( "  no bias below = %d" % mst.no_bias_below[name] )
                except Exception as e:
                    logger.info( 'object %s could not be loaded due to exception: %s'% (name,e) )

            shape = opCarving.opLabelArray.Output.meta.shape
            dtype = opCarving.opLabelArray.Output.meta.dtype

            fg_voxels = None
            if "fg_voxels" in list(topGroup.keys()):
                fg_voxels = topGroup["fg_voxels"]
                fg_voxels = [fg_voxels[:,k] for k in range(3)]

            bg_voxels = None
            if "bg_voxels" in list(topGroup.keys()):
                bg_voxels = topGroup["bg_voxels"]
                bg_voxels = [bg_voxels[:,k] for k in range(3)]

            # Determine boundings box of seeds so that we can send the smallest
            # possible array to the WriteSeeds slot. 

            # Start with inverse roi
            total_roi = roiFromShape(opCarving.opLabelArray.Output.meta.shape)
            bounding_box_roi = numpy.array( [ total_roi[1][1:4], total_roi[0][1:4] ] )
            if fg_voxels is not None and len(fg_voxels[0]) > 0:
                fg_bounding_box_start = numpy.array( list(map( numpy.min, fg_voxels )) )
                fg_bounding_box_stop = 1 + numpy.array( list(map( numpy.max, fg_voxels )) )
                bounding_box_roi[0] = numpy.minimum( bounding_box_roi[0], fg_bounding_box_start )
                bounding_box_roi[1] = numpy.maximum( bounding_box_roi[1], fg_bounding_box_stop )

            if bg_voxels is not None and len(bg_voxels[0]) > 0:
                bg_bounding_box_start = numpy.array( list(map( numpy.min, bg_voxels )) )
                bg_bounding_box_stop = 1 + numpy.array( list(map( numpy.max, bg_voxels )) )
                bounding_box_roi[0] = numpy.minimum( bounding_box_roi[0], bg_bounding_box_start )
                bounding_box_roi[1] = numpy.maximum( bounding_box_roi[1], bg_bounding_box_stop )
            
            if (bounding_box_roi[1] > bounding_box_roi[0]).all():
                z = numpy.zeros(bounding_box_roi[1] - bounding_box_roi[0], dtype=dtype)
                if fg_voxels is not None:
                    fg_voxels = fg_voxels - numpy.array( [bounding_box_roi[0]] ).transpose()
                    z[list(fg_voxels)] = 2 #fg_voxels is a 3xn numpy array, break it up into a list with three entries
                if bg_voxels is not None:
                    bg_voxels = bg_voxels - numpy.array( [bounding_box_roi[0]] ).transpose()
                    z[list(bg_voxels)] = 1

                bounding_box_slicing = roiToSlice( bounding_box_roi[0], bounding_box_roi[1] )
                opCarving.WriteSeeds[(slice(0,1),) + bounding_box_slicing + (slice(0,1),)] = z[numpy.newaxis, :,:,:, numpy.newaxis]
                logger.info( "restored seeds" )
                
            opCarving._buildDone()
           
    def isDirty(self):
        for index, innerOp in enumerate(self._o.innerOperators):
            if len(innerOp._dirtyObjects) > 0:
                return True
            if innerOp.has_seeds:
                return True
        return False
    
    #this is present only for the serializer AppletInterface
    def unload(self):
        pass
