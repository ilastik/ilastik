from builtins import range
import numpy as np
import math
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion, List
from lazyflow.operators import OpBlockedArrayCache
from lazyflow.roi import roiToSlice
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction    ,\
    default_features_key, OpAdaptTimeListRoi
from ilastik.applets.trackingFeatureExtraction import config
from ilastik.applets.trackingFeatureExtraction.trackingFeatures import FeatureManager

import logging
import collections
from ilastik.applets.base.applet import DatasetConstraintError
logger = logging.getLogger(__name__)




class OpDivisionFeatures(Operator):
    """Computes division features on a 5D volume."""    
    LabelVolume = InputSlot()
    DivisionFeatureNames = InputSlot(rtype=List, stype=Opaque)
    RegionFeaturesVigra = InputSlot()
    
    BlockwiseDivisionFeatures = OutputSlot()
        
    def __init__(self, *args, **kwargs):
        super(OpDivisionFeatures, self).__init__(*args, **kwargs)
                
    def setupOutputs(self):
        taggedShape = self.LabelVolume.meta.getTaggedShape()        

        if set(taggedShape.keys()) != set('txyzc'):
            raise Exception("Input volumes must have txyzc axes.")

        self.BlockwiseDivisionFeatures.meta.shape = tuple([taggedShape['t']])
        self.BlockwiseDivisionFeatures.meta.axistags = vigra.defaultAxistags("t")
        self.BlockwiseDivisionFeatures.meta.dtype = object        
        
        ndim = 3
        if np.any(list(taggedShape.get(k, 0) == 1 for k in "xyz")):
            ndim = 2
            
        self.featureManager = FeatureManager(scales=config.image_scale, n_best=config.n_best_successors, com_name_cur=config.com_name_cur,
                    com_name_next=config.com_name_next, size_name=config.size_name, delim=config.delim, template_size=config.template_size, 
                    ndim=ndim, size_filter=config.size_filter,squared_distance_default=config.squared_distance_default)


    def execute(self, slot, subindex, roi, result):
        assert len(roi.start) == len(roi.stop) == len(self.BlockwiseDivisionFeatures.meta.shape)
        assert slot == self.BlockwiseDivisionFeatures
        taggedShape = self.LabelVolume.meta.getTaggedShape()
        timeIndex = list(taggedShape.keys()).index('t')
        
        import time
        start = time.time()
        
        vroi_start = len(self.LabelVolume.meta.shape) * [0,]
        vroi_stop = list(self.LabelVolume.meta.shape)
        
        assert len(roi.start) == 1
        froi_start = roi.start[0]
        froi_stop = roi.stop[0]
        vroi_stop[timeIndex] = roi.stop[0]
        
        assert timeIndex == 0
        vroi_start[timeIndex] = roi.start[0]
        if roi.stop[0] + 1 < self.LabelVolume.meta.shape[timeIndex]:
            vroi_stop[timeIndex] = roi.stop[0]+1
            froi_stop = roi.stop[0]+1
        vroi = [slice(vroi_start[i],vroi_stop[i]) for i in range(len(vroi_start))]
        
        feats = self.RegionFeaturesVigra[slice(froi_start, froi_stop)].wait()
        labelVolume = self.LabelVolume[vroi].wait()
        divisionFeatNames = self.DivisionFeatureNames[()].wait()[config.features_division_name] 
        
        for t in range(roi.stop[0]-roi.start[0]):
            result[t] = {}
            feats_cur = feats[t][config.features_vigra_name]
            if t+1 < froi_stop-froi_start:                
                feats_next = feats[t+1][config.features_vigra_name]
                                
                img_next = labelVolume[t+1,...]
            else:
                feats_next = None
                img_next = None
            res = self.featureManager.computeFeatures_at(feats_cur, feats_next, img_next, divisionFeatNames)
            result[t][config.features_division_name] = res 
        
        stop = time.time()
        logger.debug("TIMING: computing division features took {:.3f}s".format(stop-start))
        return result
    
    
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.DivisionFeatureNames:
            self.BlockwiseDivisionFeatures.setDirty(slice(None))
        elif slot is self.RegionFeaturesVigra:
            self.BlockwiseDivisionFeatures.setDirty(roi)
        else:
            axes = list(self.LabelVolume.meta.getTaggedShape().keys())
            dirtyStart = collections.OrderedDict(list(zip(axes, roi.start)))
            dirtyStop = collections.OrderedDict(list(zip(axes, roi.stop)))

            # Remove the spatial and channel dims (keep t, if present)
            del dirtyStart['x']
            del dirtyStart['y']
            del dirtyStart['z']
            del dirtyStart['c']

            del dirtyStop['x']
            del dirtyStop['y']
            del dirtyStop['z']
            del dirtyStop['c']

            self.BlockwiseDivisionFeatures.setDirty(list(dirtyStart.values()), list(dirtyStop.values()))
    
    
class OpTrackingFeatureExtraction(Operator):
    name = "Tracking Feature Extraction"

    TranslationVectors = InputSlot(optional=True)
    RawImage = InputSlot()
    BinaryImage = InputSlot()

    # which features to compute.
    # nested dictionary with format:
    # dict[plugin_name][feature_name][parameter_name] = parameter_value
    # for example {"Standard Object Features": {"Mean in neighborhood":{"margin": (5, 5, 2)}}}
    FeatureNamesVigra = InputSlot(rtype=List, stype=Opaque, value={})
    
    FeatureNamesDivision = InputSlot(rtype=List, stype=Opaque, value={})
 
    # Bypass cache (for headless mode)
    BypassModeEnabled = InputSlot(value=False)        

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()
 
    # the computed features.
    # nested dictionary with format:
    # dict[plugin_name][feature_name] = feature_value
    RegionFeaturesVigra = OutputSlot(stype=Opaque, rtype=List)    
    RegionFeaturesDivision = OutputSlot(stype=Opaque, rtype=List)
    RegionFeaturesAll = OutputSlot(stype=Opaque, rtype=List)
    
    ComputedFeatureNamesAll = OutputSlot(rtype=List, stype=Opaque)
    ComputedFeatureNamesNoDivisions = OutputSlot(rtype=List, stype=Opaque)

    BlockwiseRegionFeaturesVigra = OutputSlot() # For compatibility with tracking workflow, the RegionFeatures output
                                                # has rtype=List, indexed by t.
                                                # For other workflows, output has rtype=ArrayLike, indexed by (t)
    BlockwiseRegionFeaturesDivision = OutputSlot() 
    
    CleanLabelBlocks = OutputSlot()
    LabelImageCacheInput = InputSlot(optional=True)

    RegionFeaturesCacheInputVigra = InputSlot(optional=True)
    RegionFeaturesCleanBlocksVigra = OutputSlot()
    
    RegionFeaturesCacheInputDivision = InputSlot(optional=True)
    RegionFeaturesCleanBlocksDivision = OutputSlot()
    
        
    def __init__(self, parent):
        super(OpTrackingFeatureExtraction, self).__init__(parent)
        self._default_features = None
        # internal operators
        self._objectExtraction = OpObjectExtraction(parent=self)
                
        self._opDivFeats = OpCachedDivisionFeatures(parent=self)
        self._opDivFeatsAdaptOutput = OpAdaptTimeListRoi(parent=self)        

        # connect internal operators
        self._objectExtraction.RawImage.connect(self.RawImage)
        self._objectExtraction.BinaryImage.connect(self.BinaryImage)
        self._objectExtraction.BypassModeEnabled.connect(self.BypassModeEnabled)
        self._objectExtraction.Features.connect(self.FeatureNamesVigra)
        self._objectExtraction.RegionFeaturesCacheInput.connect(self.RegionFeaturesCacheInputVigra)
        self._objectExtraction.LabelImageCacheInput.connect(self.LabelImageCacheInput)
        self.CleanLabelBlocks.connect(self._objectExtraction.CleanLabelBlocks)
        self.RegionFeaturesCleanBlocksVigra.connect(self._objectExtraction.RegionFeaturesCleanBlocks)
        self.ObjectCenterImage.connect(self._objectExtraction.ObjectCenterImage)
        self.LabelImage.connect(self._objectExtraction.LabelImage)
        self.BlockwiseRegionFeaturesVigra.connect(self._objectExtraction.BlockwiseRegionFeatures)     
        self.RegionFeaturesVigra.connect(self._objectExtraction.RegionFeatures)    
                
        self._opDivFeats.LabelImage.connect(self.LabelImage)
        self._opDivFeats.DivisionFeatureNames.connect(self.FeatureNamesDivision)
        self._opDivFeats.CacheInput.connect(self.RegionFeaturesCacheInputDivision)
        self._opDivFeats.RegionFeaturesVigra.connect(self._objectExtraction.BlockwiseRegionFeatures)
        self.RegionFeaturesCleanBlocksDivision.connect(self._opDivFeats.CleanBlocks)        
        self.BlockwiseRegionFeaturesDivision.connect(self._opDivFeats.Output)
        
        self._opDivFeatsAdaptOutput.Input.connect(self._opDivFeats.Output)
        self.RegionFeaturesDivision.connect(self._opDivFeatsAdaptOutput.Output)
        
        # As soon as input data is available, check its constraints
        self.RawImage.notifyReady( self._checkConstraints )
        self.BinaryImage.notifyReady( self._checkConstraints )

        # FIXME this shouldn't be done in post-filtering, but in reading the config or around that time
        self.RawImage.notifyReady( self._filterFeaturesByDim )
    
    def setDefaultFeatures(self, feats):
        self._default_features = feats

    def setupOutputs(self, *args, **kwargs):
        self.ComputedFeatureNamesAll.meta.assignFrom(self.FeatureNamesVigra.meta)
        self.ComputedFeatureNamesNoDivisions.meta.assignFrom(self.FeatureNamesVigra.meta)
        self.RegionFeaturesAll.meta.assignFrom(self.RegionFeaturesVigra.meta)

    def execute(self, slot, subindex, roi, result):
        if slot == self.ComputedFeatureNamesAll:
            feat_names_vigra = self.FeatureNamesVigra([]).wait()
            feat_names_div = self.FeatureNamesDivision([]).wait()        
            for plugin_name in list(feat_names_vigra.keys()):
                assert plugin_name not in feat_names_div, "feature name dictionaries must be mutually exclusive"
            for plugin_name in list(feat_names_div.keys()):
                assert plugin_name not in feat_names_vigra, "feature name dictionaries must be mutually exclusive"
            result = dict(list(feat_names_vigra.items()) + list(feat_names_div.items()))

            return result
        elif slot == self.ComputedFeatureNamesNoDivisions:
            feat_names_vigra = self.FeatureNamesVigra([]).wait()
            result = dict(list(feat_names_vigra.items()))

            return result
        elif slot == self.RegionFeaturesAll:
            feat_vigra = self.RegionFeaturesVigra(roi).wait()
            feat_div = self.RegionFeaturesDivision(roi).wait()
            assert np.all(list(feat_vigra.keys()) == list(feat_div.keys()))
            result = {}        
            for t in list(feat_vigra.keys()):
                for plugin_name in list(feat_vigra[t].keys()):
                    assert plugin_name not in feat_div[t], "feature dictionaries must be mutually exclusive"
                for plugin_name in list(feat_div[t].keys()):
                    assert plugin_name not in feat_vigra[t], "feature dictionaries must be mutually exclusive"                    
                result[t] = dict(list(feat_div[t].items()) + list(feat_vigra[t].items()))            
            return result
        else:
            assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        if  slot == self.BypassModeEnabled:
            pass
        elif slot == self.FeatureNamesVigra or slot == self.FeatureNamesDivision:
            self.ComputedFeatureNamesAll.setDirty(roi)
            self.ComputedFeatureNamesNoDivisions.setDirty(roi)

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.RegionFeaturesCacheInputVigra or \
            slot == self.RegionFeaturesCacheInputDivision or \
            slot == self.LabelImageCacheInput, "Invalid slot for setInSlot(): {}".format(slot.name)
           
    def _checkConstraints(self, *args):
        if self.RawImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            if 't' not in rawTaggedShape or rawTaggedShape['t'] < 2:
                msg = "Raw image must have a time dimension with at least 2 images.\n"\
                    "Your dataset has shape: {}".format(self.RawImage.meta.shape)
                    
        if self.BinaryImage.ready():
            rawTaggedShape = self.BinaryImage.meta.getTaggedShape()
            if 't' not in rawTaggedShape or rawTaggedShape['t'] < 2:
                msg = "Binary image must have a time dimension with at least 2 images.\n"\
                    "Your dataset has shape: {}".format(self.BinaryImage.meta.shape)
                    
        if self.RawImage.ready() and self.BinaryImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            binTaggedShape = self.BinaryImage.meta.getTaggedShape()
            rawTaggedShape['c'] = None
            binTaggedShape['c'] = None
            if dict(rawTaggedShape) != dict(binTaggedShape):
                logger.info("Raw data and other data must have equal dimensions (different channels are okay).\n"\
                      "Your datasets have shapes: {} and {}".format( self.RawImage.meta.shape, self.BinaryImage.meta.shape ))
                
                msg = "Raw data and other data must have equal dimensions (different channels are okay).\n"\
                      "Your datasets have shapes: {} and {}".format( self.RawImage.meta.shape, self.BinaryImage.meta.shape )
                raise DatasetConstraintError( "Object Extraction", msg )

    def _filterFeaturesByDim(self, *args):
        # Remove 2D-only features from 3D datasets
        # Features look as follows:
        # dict[plugin_name][feature_name][parameter_name] = parameter_value
        # for example {"Standard Object Features": {"Mean in neighborhood":{"margin": (5, 5, 2)}}}

        # FIXME: this is a hacky solution because we overwrite the INPUT slot FeatureNamesVigra depending on the data shape.
        # We store the _default_features separately because if the user switches from a 3D to a 2D dataset the value of
        # FeatureNamesVigra would not be populated with all the features again, but only those that work for 3D.

        if self.RawImage.ready() and self.FeatureNamesVigra.ready():

            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            filtered_features_dict = {}
            if rawTaggedShape['z']>1:
                # Filter out the 2D-only features, which helpfully have "2D" in their plugin name
                current_dict = self._default_features
                for plugin in list(current_dict.keys()):
                    if not "2D" in plugin:
                        filtered_features_dict[plugin] = current_dict[plugin]

                self.FeatureNamesVigra.setValue(filtered_features_dict)
            else:
                # Filter out the 2D-only features, which helpfully have "2D" in their plugin name
                current_dict = self._default_features
                for plugin in list(current_dict.keys()):
                    if not "3D" in plugin:
                        filtered_features_dict[plugin] = current_dict[plugin]

                self.FeatureNamesVigra.setValue(filtered_features_dict)
                # self.FeatureNamesVigra.setValue(self._default_features)

class OpCachedDivisionFeatures(Operator):
    """Caches the division features computed by OpDivisionFeatures."""    
    LabelImage = InputSlot()
    CacheInput = InputSlot(optional=True)
    DivisionFeatureNames = InputSlot(rtype=List, stype=Opaque)
    RegionFeaturesVigra = InputSlot()

    Output = OutputSlot()
    CleanBlocks = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpCachedDivisionFeatures, self).__init__(*args, **kwargs)

        # Hook up the labeler
        self._opDivisionFeatures = OpDivisionFeatures(parent=self)        
        self._opDivisionFeatures.LabelVolume.connect(self.LabelImage)
        self._opDivisionFeatures.DivisionFeatureNames.connect(self.DivisionFeatureNames)
        self._opDivisionFeatures.RegionFeaturesVigra.connect(self.RegionFeaturesVigra)

        # Hook up the cache.
        self._opCache = OpBlockedArrayCache(parent=self)
        self._opCache.name = "OpCachedDivisionFeatures._opCache"
        self._opCache.Input.connect(self._opDivisionFeatures.BlockwiseDivisionFeatures)

        # Hook up our output slots
        self.Output.connect(self._opCache.Output)
        self.CleanBlocks.connect(self._opCache.CleanBlocks)

    def setupOutputs(self):        
        taggedOutputShape = self.LabelImage.meta.getTaggedShape()        

        if 't' not in list(taggedOutputShape.keys()) or taggedOutputShape['t'] < 2:
            raise DatasetConstraintError( "Tracking Feature Extraction",
                                          "Label Image must have a time axis with more than 1 image.\n"\
                                          "Label Image shape: {}"\
                                          "".format(self.LabelImage.meta.shape))

        
        # Every value in the region features output is cached separately as it's own "block"
        blockshape = (1,) * len(self._opDivisionFeatures.BlockwiseDivisionFeatures.meta.shape)
        self._opCache.BlockShape.setValue(blockshape)

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.CacheInput
        slicing = roiToSlice(roi.start, roi.stop)
        self._opCache.Input[ slicing ] = value

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...

    
