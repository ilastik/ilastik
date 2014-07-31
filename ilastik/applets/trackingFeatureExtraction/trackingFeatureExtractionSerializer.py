from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot,\
    deleteIfPresent, getOrCreateGroup, SerialHdf5BlockSlot, SerialDictSlot
from ilastik.applets.objectExtraction.objectExtractionSerializer import ObjectExtractionSerializer,\
    SerialObjectFeaturesSlot

import numpy as np
import collections

class TrackingFeatureExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):             
        slots = [
            SerialHdf5BlockSlot(operator.LabelOutputHdf5,
                                operator.LabelInputHdf5,
                                operator.CleanLabelBlocks,
                                name="LabelImage"),
            SerialDictSlot(operator.FeatureNamesVigra, transform=str),
            SerialDictSlot(operator.FeatureNamesDivision, transform=str),
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
        
