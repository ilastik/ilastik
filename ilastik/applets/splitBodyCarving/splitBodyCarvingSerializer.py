# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from ilastik.applets.base.appletSerializer import getOrCreateGroup, deleteIfPresent
from ilastik.workflows.carving.carvingSerializer import CarvingSerializer
from opSplitBodyCarving import OpSplitBodyCarving

class SplitBodyCarvingSerializer(CarvingSerializer):
    
    def __init__(self, topLevelOperator, *args, **kwargs):
        super( SplitBodyCarvingSerializer, self ).__init__(topLevelOperator, *args, **kwargs)
        self._topLevelOperator = topLevelOperator
        
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
        

        
        
