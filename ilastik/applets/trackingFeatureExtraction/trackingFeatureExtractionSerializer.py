from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot,\
    deleteIfPresent, getOrCreateGroup, SerialBlockSlot, SerialDictSlot, SerialObjectFeatureNamesSlot
from ilastik.applets.objectExtraction.objectExtractionSerializer import ObjectExtractionSerializer,\
    SerialObjectFeaturesSlot

import numpy as np
import collections

class TrackingFeatureExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):             
        slots = [
            SerialBlockSlot(operator.LabelImage,
                            operator.LabelImageCacheInput,
                            operator.CleanLabelBlocks,
                            name='LabelImage_v2',
                            subname='labelimage{:03d}',
                            selfdepends=False,
                            shrink_to_bb=False,
                            compression_level=1),
            SerialObjectFeatureNamesSlot(operator.FeatureNamesVigra),
            SerialObjectFeatureNamesSlot(operator.FeatureNamesDivision),
            SerialObjectFeaturesSlot(operator.BlockwiseRegionFeaturesVigra,
                                     operator.RegionFeaturesCacheInputVigra,
                                     operator.RegionFeaturesCleanBlocksVigra,
                                     name="RegionFeaturesVigra"),
            SerialObjectFeaturesSlot(operator.BlockwiseRegionFeaturesDivision,
                                     operator.RegionFeaturesCacheInputDivision,
                                     operator.RegionFeaturesCleanBlocksDivision,
                                     name="RegionFeaturesDivision"),
        ]
   
        super(TrackingFeatureExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
        
