from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, SerialHdf5BlockSlot

class SplitBodyPostprocessingSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = []
# NOTE: Ideally, we would store the final segmentation output so it can be deserialized into the cache,
#       but the split-body carving workflow relies on the GUI to load the annotation info, which means that the 
#       cache can't be loaded during deserialization.
#       The right way to fix this is to either:
#       (1) re-implement the annotation loading code as part of the operator itself 
#             so it is loaded during deserialization (not deferred to the gui)
#       OR
#       (2) (easier) Cache the annotation points/body ids so that the operators are fully configured by deserialization.
#
#        ... anyway, once that is finished, this line will cause the cache to be saved and loaded.       
#
#        slots = [SerialHdf5BlockSlot(operator.FinalSegmentationHdf5CacheOutput,
#                                     operator.FinalSegmentationHdf5CacheInput,
#                                     operator.FinalSegmentationCleanBlocks,
#                                     name="CachedFinalSegmentation")
#                ]

        super(self.__class__, self).__init__(projectFileGroupName, slots=slots)
