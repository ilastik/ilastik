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
from ilastik.applets.base.appletSerializer import getOrCreateGroup, deleteIfPresent
from ilastik.workflows.carving.carvingSerializer import CarvingSerializer
from opSplitBodyCarving import OpSplitBodyCarving

class SplitBodyCarvingSerializer(CarvingSerializer):
    
    def __init__(self, topLevelOperator, *args, **kwargs):
        super( SplitBodyCarvingSerializer, self ).__init__(topLevelOperator, *args, **kwargs)
        self._topLevelOperator = topLevelOperator

        # Set up dirty tracking...
        def setDirty(*args):
            self.__dirty = True

        def doMulti(slot, index, size):
            slot[index].notifyDirty(setDirty)
            slot[index].notifyValueChanged(setDirty)

        topLevelOperator.AnnotationFilepath.notifyInserted(doMulti)
        topLevelOperator.AnnotationFilepath.notifyRemoved(setDirty)

        
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        split_settings_grp = getOrCreateGroup(topGroup, "split_settings")

        for laneIndex in range(len( self._topLevelOperator )):
            lane_grp = getOrCreateGroup(split_settings_grp, "{}".format( laneIndex ))
            opLaneView = self._topLevelOperator.getLane(laneIndex)
            if opLaneView.AnnotationFilepath.ready():
                annotation_filepath = opLaneView.AnnotationFilepath.value
                deleteIfPresent( lane_grp, "annotation_filepath" )
                lane_grp.create_dataset("annotation_filepath", data=annotation_filepath)

        # Now save the regular the carving data.        
        super( SplitBodyCarvingSerializer, self )._serializeToHdf5( topGroup, hdf5File, projectFilePath )
        self.__dirty = False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        try:
            split_settings_grp = topGroup["split_settings"]
        except KeyError:
            pass
        else:
            for laneIndex, grp_name in enumerate( sorted(split_settings_grp.keys()) ):
                opLaneView = self._topLevelOperator.getLane(laneIndex)
                lane_grp = split_settings_grp[grp_name]
                try:
                    annotation_filepath = lane_grp["annotation_filepath"].value
                except KeyError:
                    pass
                else:
                    opLaneView.AnnotationFilepath.setValue( annotation_filepath )
        
        # Now load the regular carving data.
        super( SplitBodyCarvingSerializer, self )._deserializeFromHdf5( topGroup, groupVersion, hdf5File, projectFilePath )
        self.__dirty = False
        

    def isDirty(self):
        return self.__dirty or super( SplitBodyCarvingSerializer, self ).isDirty()
        
