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
                annotation_filepath = str(lane_grp["annotation_filepath"].value)
                opLaneView.AnnotationFilepath.setValue( annotation_filepath )
        
        # Now load the regular carving data.
        super( SplitBodyCarvingSerializer, self )._deserializeFromHdf5( topGroup, groupVersion, hdf5File, projectFilePath )
        

        
        
