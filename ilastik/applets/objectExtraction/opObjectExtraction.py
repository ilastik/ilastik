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
#Python
from __future__ import division
from builtins import range
from copy import copy, deepcopy
import collections
from functools import partial

# SciPy
import numpy
import vigra.analysis

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.request import Request, RequestPool
from lazyflow.stype import Opaque
from lazyflow.rtype import List, SubRegion
from lazyflow.roi import roiToSlice, sliceToRoi
from lazyflow.operators import OpLabelVolume, OpCompressedCache, OpBlockedArrayCache
from itertools import groupby, count

import logging
logger = logging.getLogger(__name__)

#ilastik
try:
    from ilastik.plugins import pluginManager
except:
    logger.warning('could not import pluginManager')

from ilastik.applets.base.applet import DatasetConstraintError

# These features are always calculated, but not used for prediction.
# They are needed by our gui, or by downstream applets.
default_features = {'Coord<Minimum>':{}, 'Coord<Maximum>':{}, 'RegionCenter': {}, 'Count':{}}

# to distinguish them, they go in their own category with this name
default_features_key = 'Default features'


def max_margin(d, default=(0, 0, 0)):
    """find any parameter named 'margin' in the nested feature
    dictionary 'd' and return the max.

    return 'default' if none are found.

    >>> max_margin({'plugin_one' : {'feature_one' : {'margin' : 10}}})
    [10, 10, 10]

    >>> max_margin({"p1": {"f1":{"margin":(10, 5, 2)}}})
    [10, 5, 2]

    """
    margin = default
    for features in d.values():
        for params in features.values():
            try:
                pmargin = params['margin']
                if not isinstance(pmargin, collections.Iterable):
                    pmargin = len(default)*[pmargin]
                margin = [max(x) for x in zip(margin, pmargin)]
            except (ValueError, KeyError):
                continue
    return margin


def make_bboxes(binary_bbox, margin):
    """Return binary label arrays for an object with margin.

    Needed to compute features in the object neighborhood

    Returns (the object + context, context only)

    """
    # object and context
    max_margin = numpy.max(margin).astype(numpy.float32)
    scaled_margin = (max_margin // margin)
    if len(margin) > 2:
        dt = vigra.filters.distanceTransform(numpy.asarray(binary_bbox, dtype=numpy.float32),
                                               background=True,
                                               pixel_pitch=numpy.asarray(scaled_margin).astype(numpy.float64))
    else:
        dt = vigra.filters.distanceTransform(numpy.asarray(binary_bbox.squeeze(), dtype=numpy.float32),
                                               pixel_pitch=numpy.asarray(scaled_margin).astype(numpy.float64))
        dt = dt.reshape(dt.shape + (1,))

    assert dt.ndim == 3
    passed = numpy.asarray(dt < max_margin).astype(numpy.bool)

    # context only
    context = numpy.asarray(passed) ^ numpy.asarray(binary_bbox).astype(numpy.bool)
    return passed, context


class OpCachedRegionFeatures(Operator):
    """Caches the region features computed by OpRegionFeatures."""
    RawImage = InputSlot()
    LabelImage = InputSlot()
    CacheInput = InputSlot(optional=True)
    Features = InputSlot(rtype=List, stype=Opaque)

    Output = OutputSlot()
    CleanBlocks = OutputSlot()

    # Schematic:
    #
    # RawImage -----   blockshape=(t,)=(1,)
    #               \                        \
    # LabelImage ----> OpRegionFeatures ----> OpBlockedArrayCache --> Output
    #                                                            \
    #                                                             --> CleanBlocks

    def __init__(self, *args, **kwargs):
        super(OpCachedRegionFeatures, self).__init__(*args, **kwargs)

        # Hook up the actual region features operator
        self._opRegionFeatures = OpRegionFeatures(parent=self)
        self._opRegionFeatures.RawVolume.connect(self.RawImage)
        self._opRegionFeatures.LabelVolume.connect(self.LabelImage)
        self._opRegionFeatures.Features.connect(self.Features)

        # Hook up the cache.
        self._opCache = OpBlockedArrayCache(parent=self)
        self._opCache.name = "OpCachedRegionFeatures._opCache"
        self._opCache.Input.connect(self._opRegionFeatures.Output)

        # Hook up our output slots
        self.Output.connect(self._opCache.Output)
        self.CleanBlocks.connect(self._opCache.CleanBlocks)

    def setupOutputs(self):
        assert self.LabelImage.meta.axistags == self.RawImage.meta.axistags

        taggedOutputShape = self.LabelImage.meta.getTaggedShape()
        taggedRawShape = self.RawImage.meta.getTaggedShape()

        if not numpy.all(list(taggedOutputShape.get(k, 0) == taggedRawShape.get(k, 0)
                           for k in "txyz")):
            raise DatasetConstraintError( "Object Extraction",
                                          "Raw Image and Label Image shapes do not match.\n"\
                                          "Label Image shape: {}. Raw Image shape: {}"\
                                          "".format(self.LabelImage.meta.shape, self.RawVolume.meta.shape))


        # Every value in the regionfeatures output is cached seperately as it's own "block"
        blockshape = (1,) * len(self._opRegionFeatures.Output.meta.shape)
        self._opCache.BlockShape.setValue(blockshape)

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.CacheInput
        slicing = roiToSlice(roi.start, roi.stop)
        self._opCache.Input[ slicing ] = value

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...

class OpAdaptTimeListRoi(Operator):
    """Adapts the t array output from OpRegionFeatures to an Output
    slot that is called with a 'List' rtype, where the roi is a list
    of time slices, and the output is a dictionary of (time,
    featuredict) pairs.

    """
    Input = InputSlot()
    Output = OutputSlot(stype=Opaque, rtype=List)

    def setupOutputs(self):
        # Number of time steps
        self.Output.meta.shape = (self.Input.meta.getTaggedShape()['t'],)
        self.Output.meta.dtype = object

    def execute(self, slot, subindex, roi, destination):
        assert slot == self.Output, "Unknown output slot"
        taggedShape = self.Input.meta.getTaggedShape()

        # Special case: An empty roi list means "request everything"
        if len(roi) == 0:
            roi = list(range(taggedShape['t']))

        taggedShape['t'] = 1
        timeIndex = list(taggedShape.keys()).index('t')

        # Get time ranges with consecutive numbers
        time_ranges = [list(g) for _, g in groupby(roi, key=lambda n, c=count(): n - next(c))]

        result = {}             
        for time_range in time_ranges:
            start = [time_range[0]]
            stop = [time_range[-1]+1]
                  
            val = self.Input(start, stop).wait()
      
            for i, t in enumerate(time_range):
                result[t] = val[i]

        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.Input
        timeIndex = self.Input.meta.axistags.index('t')
        self.Output.setDirty(List(self.Output, list(range(roi.start[timeIndex], roi.stop[timeIndex]))))

class OpObjectCenterImage(Operator):
    """Produceds an image with a cross in the center of each connected
    component.

    """
    BinaryImage = InputSlot()
    RegionCenters = InputSlot(rtype=List, stype=Opaque)
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.BinaryImage.meta)

    @staticmethod
    def __contained_in_subregion(roi, coords):
        b = True
        for i in range(len(coords)):
            b = b and (roi.start[i] <= coords[i] and coords[i] < roi.stop[i])
        return b

    @staticmethod
    def __make_key(roi, coords):
        key = [int(coords[i] - roi.start[i]) for i in range(len(roi.start))]
        return tuple(key)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        
        result[:] = 0
        ndim = 3
        taggedShape = self.BinaryImage.meta.getTaggedShape()
        if 'z' not in taggedShape or taggedShape['z']==1:
            ndim = 2
        for t in range(roi.start[0], roi.stop[0]):
            obj_features = self.RegionCenters([t]).wait()
            #FIXME: this assumes that channel is the last axis
            for ch in range(roi.start[-1], roi.stop[-1]):
                centers = obj_features[t][default_features_key]['RegionCenter']
                if centers.size:
                    centers = centers[1:, :]
                for center in centers:
                    if ndim==3:
                        x, y, z = center[0:3]
                        c = (t, x, y, z, ch)
                    elif ndim==2:
                        x, y = center[0:2]
                        c = (t, x, y, 0, ch)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi, c)] = 1

        return result

    def propagateDirty(self, slot, subindex, roi):
        # the roi here is a list of time steps
        if slot is self.RegionCenters:
            roi = list(roi)
            t = roi[0]
            T = t + 1
            a = t
            for b in roi[1:]:
                assert b-1 == a, "List roi must be contiguous"
                a = b
                T += 1
            time_index = self.BinaryImage.meta.axistags.index('t')
            stop = numpy.asarray(self.BinaryImage.meta.shape, dtype=numpy.int)
            start = numpy.zeros_like(stop)
            stop[time_index] = T
            start[time_index] = t
            
            roi = SubRegion(self.Output, tuple(start), tuple(stop))
            self.Output.setDirty(roi)
                                  

class OpObjectExtraction(Operator):
    """The top-level operator for the object extraction applet.

    Computes object features and object center images.

    """
    name = "Object Extraction"

    RawImage = InputSlot()
    BinaryImage = InputSlot()
    BackgroundLabels = InputSlot(optional=True)

    # Bypass cache (for headless mode)
    BypassModeEnabled = InputSlot(value=False)
    
    # which features to compute.
    # nested dictionary with format:
    # dict[plugin_name][feature_name][parameter_name] = parameter_value
    # for example {"Standard Object Features": {"Mean in neighborhood":{"margin": (5, 5, 2)}}}
    Features = InputSlot(rtype=List, stype=Opaque, value={})

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()

    # the computed features.
    # dict[time_slice][plugin_name][feature_name] = feature_value
    # by requesting from this slot with indices, the corresponding indices will be added to the dict
    # -> RegionFeatures[0].wait() -> {0: {...}}
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)

    BlockwiseRegionFeatures = OutputSlot() # For compatibility with tracking workflow, the RegionFeatures output
                                           # has rtype=List, indexed by t.
                                           # For other workflows, output has rtype=ArrayLike, indexed by (t)

    CleanLabelBlocks = OutputSlot()
    LabelImageCacheInput = InputSlot()

    RegionFeaturesCacheInput = InputSlot(optional=True)
    RegionFeaturesCleanBlocks = OutputSlot()

    # Schematic:
    #
    # BackgroundLabels              LabelImage
    #                 \            /
    # BinaryImage ---> opLabelImage ---> opRegFeats ---> opRegFeatsAdaptOutput ---> RegionFeatures
    #                                   /                                     \
    # RawImage--------------------------                      BinaryImage ---> opObjectCenterImage --> opCenterCache --> ObjectCenterImage

    def __init__(self, *args, **kwargs):

        super(OpObjectExtraction, self).__init__(*args, **kwargs)

        # internal operators
        #TODO BinaryImage is not binary in some workflows, could be made more
        # efficient
        self._opLabelVolume = OpLabelVolume(parent=self)
        self._opLabelVolume.name = "OpObjectExtraction._opLabelVolume"        
        self._opRegFeats = OpCachedRegionFeatures(parent=self)
        self._opRegFeatsAdaptOutput = OpAdaptTimeListRoi(parent=self)
        self._opObjectCenterImage = OpObjectCenterImage(parent=self)

        # connect internal operators
        self._opLabelVolume.Input.connect(self.BinaryImage)
        self._opLabelVolume.Background.connect(self.BackgroundLabels)
        self._opLabelVolume.BypassModeEnabled.connect(self.BypassModeEnabled)

        self._opRegFeats.RawImage.connect(self.RawImage)
        self._opRegFeats.LabelImage.connect(self._opLabelVolume.CachedOutput)
        self._opRegFeats.Features.connect(self.Features)
        self.RegionFeaturesCleanBlocks.connect(self._opRegFeats.CleanBlocks)

        self._opRegFeats.CacheInput.connect(self.RegionFeaturesCacheInput)

        self._opRegFeatsAdaptOutput.Input.connect(self._opRegFeats.Output)

        self._opObjectCenterImage.BinaryImage.connect(self.BinaryImage)
        self._opObjectCenterImage.RegionCenters.connect(self._opRegFeatsAdaptOutput.Output)

        self._opCenterCache = OpCompressedCache(parent=self)
        self._opCenterCache.name = "OpObjectExtraction._opCenterCache"
        self._opCenterCache.Input.connect(self._opObjectCenterImage.Output)

        # connect outputs
        self.LabelImage.connect(self._opLabelVolume.CachedOutput)
        self.ObjectCenterImage.connect(self._opCenterCache.Output)
        self.RegionFeatures.connect(self._opRegFeatsAdaptOutput.Output)
        self.BlockwiseRegionFeatures.connect(self._opRegFeats.Output)
        self.CleanLabelBlocks.connect(self._opLabelVolume.CleanBlocks)

        # As soon as input data is available, check its constraints
        self.RawImage.notifyReady( self._checkConstraints )
        self.BinaryImage.notifyReady( self._checkConstraints )

    def _checkConstraints(self, *args):
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
            

    def setupOutputs(self):
        # Setup LabelImageCacheInput for the serialization of the compressed cache
        self._opLabelVolume._opLabel._cache.Input.connect(self.LabelImageCacheInput)
                
        taggedShape = self.RawImage.meta.getTaggedShape()
        for k in list(taggedShape.keys()):
            if k == 't' or k == 'c':
                taggedShape[k] = 1
            # else:
            #     taggedShape[k] = 256
        self._opCenterCache.BlockShape.setValue(tuple(taggedShape.values()))

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, inputSlot, subindex, roi):
        pass

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.RegionFeaturesCacheInput or \
        slot == self.LabelImageCacheInput, "Invalid slot for setInSlot(): {}".format(slot.name)
        # Nothing to do here.
        # Our Input slots are directly fed into the cache,
        #  so all calls to __setitem__ are forwarded automatically


class OpRegionFeatures(Operator):
    """Produces region features for time-stacked 3d+c volumes

    The image's axes are extended to the full xyzc shape, one t-slice at a
    time.

    Inputs:

    * RawVolume : the raw data on which to compute features

    * LabelVolume : a volume of connected components for each object
      in the raw data.

    * Features : a nested dictionary of features to compute.
      Features[plugin name][feature name][parameter name] = parameter value

    Outputs:

    * Output : a nested dictionary of features.
      Output[plugin name][feature name] = numpy.ndarray

    """
    RawVolume = InputSlot()
    LabelVolume = InputSlot()
    Features = InputSlot(rtype=List, stype=Opaque)

    Output = OutputSlot()

    def setupOutputs(self):
        if self.LabelVolume.meta.axistags != self.RawVolume.meta.axistags:
            raise Exception('raw and label axis tags do not match')

        taggedOutputShape = self.LabelVolume.meta.getTaggedShape()
        taggedRawShape = self.RawVolume.meta.getTaggedShape()

        if not numpy.all(list(taggedOutputShape.get(k, 0) == taggedRawShape.get(k, 0)
                           for k in "txyz")):
            raise Exception("shapes do not match. label volume shape: {}."
                            " raw data shape: {}".format(
                                self.LabelVolume.meta.shape,
                                self.RawVolume.meta.shape))

        self.Output.meta.shape = (taggedOutputShape['t'],)
        self.Output.meta.axistags = vigra.defaultAxistags('t')
        # The features for the entire block (in xyz) are provided for the requested tc coordinates.
        self.Output.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        assert len(roi.start) == len(roi.stop) == len(self.Output.meta.shape)
        assert slot == self.Output

        t_ind = self.RawVolume.meta.axistags.index('t')
        assert t_ind < len(self.RawVolume.meta.shape)

        def compute_features_for_time_slice(res_t_ind, t):
            # Process entire spatial volume
            s = [slice(None) for i in range(len(self.RawVolume.meta.shape))]
            s[t_ind] = slice(t, t+1)
            s = tuple(s)

            # Request in parallel
            raw_req = self.RawVolume[s]
            label_req = self.LabelVolume[s]

            raw_req.submit()
            label_req.submit()

            # Get results
            rawVolume = raw_req.wait()
            labelVolume = label_req.wait()

            rawVolume = vigra.taggedView(rawVolume, axistags=self.RawVolume.meta.axistags)
            labelVolume = vigra.taggedView(labelVolume, axistags=self.LabelVolume.meta.axistags)
    
            # Convert to 4D (preserve axis order)
            axes4d = list(self.RawVolume.meta.getTaggedShape().keys())
            axes4d = [k for k in axes4d if k in 'xyzc']
            rawVolume = rawVolume.withAxes(*axes4d)
            labelVolume = labelVolume.withAxes(*axes4d)
            acc = self._extract(rawVolume, labelVolume)
            
            # Copy into the result
            result[res_t_ind] = acc            

        # loop over requested time slices
        pool = RequestPool()
        for res_t_ind, t in enumerate(range(roi.start[t_ind], roi.stop[t_ind])):
            pool.add( Request( partial(compute_features_for_time_slice, res_t_ind, t) ) )
        
        pool.wait()
        return result

    def compute_extent(self, i, image, mincoords, maxcoords, axes, margin):
        """Make a slicing to extract object i from the image."""
        #find the bounding box (margin is always 'xyz' order)
        result = [None] * 3
        minx = max(mincoords[i][axes.x] - margin[axes.x], 0)
        miny = max(mincoords[i][axes.y] - margin[axes.y], 0)

        # Coord<Minimum> and Coord<Maximum> give us the [min,max]
        # coords of the object, but we want the bounding box: [min,max), so add 1
        maxx = min(maxcoords[i][axes.x] + 1 + margin[axes.x], image.shape[axes.x])
        maxy = min(maxcoords[i][axes.y] + 1 + margin[axes.y], image.shape[axes.y])

        result[axes.x] = slice(minx, maxx)
        result[axes.y] = slice(miny, maxy)

        try:
            minz = max(mincoords[i][axes.z] - margin[axes.z], 0)
            maxz = min(maxcoords[i][axes.z] + 1 + margin[axes.z], image.shape[axes.z])
        except:
            minz = 0
            maxz = 1

        result[axes.z] = slice(minz, maxz)

        return result

    def compute_rawbbox(self, image, extent, axes):
        """essentially returns image[extent], preserving all channels."""
        key = copy(extent)
        key.insert(axes.c, slice(None))
        return image[tuple(key)]

    def _augmentFeatureNames(self, features):
        # Take a dictionary of feature names, augment it by default features and set to Features() slot
        
        feature_names = features
        feature_names_with_default = deepcopy(feature_names)

        #expand the feature list by our default features
        logger.debug("attaching default features {} to vigra features {}".format(default_features, feature_names))
        plugin = pluginManager.getPluginByName("Standard Object Features", "ObjectFeatures")
        all_default_props = plugin.plugin_object.fill_properties(default_features) #fill in display name and such
        feature_names_with_default[default_features_key] = all_default_props

        if not "Standard Object Features" in list(feature_names.keys()):
            # The user has not selected any standard features. Add them now
            feature_names_with_default["Standard Object Features"] = {}

        for default_feature_name, default_feature_props in default_features.items():
            if default_feature_name not in feature_names_with_default["Standard Object Features"]:
                # this feature has not been selected by the user, add it now.
                feature_names_with_default["Standard Object Features"][default_feature_name] = all_default_props[default_feature_name]
                feature_names_with_default["Standard Object Features"][default_feature_name]["selected"] = False

        return feature_names_with_default

    def _extract(self, image, labels):
        if not (image.ndim == labels.ndim == 4):
            raise Exception("both images must be 4D. raw image shape: {}"
                            " label image shape: {}".format(image.shape, labels.shape))

        # FIXME: maybe simplify? taggedShape should be easier here
        class Axes(object):
            x = image.axistags.index('x')
            y = image.axistags.index('y')
            z = image.axistags.index('z')
            c = image.axistags.index('c')
        axes = Axes()

        slc3d = [slice(None)] * 4 # FIXME: do not hardcode
        slc3d[axes.c] = 0

        labels = labels[slc3d]

        #These are the feature names, selected by the user and the default feature names.
        feature_names = deepcopy(self.Features([]).wait())
        feature_names = self._augmentFeatureNames(feature_names)

        # do global features
        logger.debug("Computing global and default features")
        global_features = {}
        pool = RequestPool()

        def compute_for_one_plugin(plugin_name, feature_dict):
            plugin_inner = pluginManager.getPluginByName(plugin_name, "ObjectFeatures")
            global_features[plugin_name] = plugin_inner.plugin_object.compute_global(image, labels, feature_dict, axes)

        for plugin_name, feature_dict in feature_names.items():
            if plugin_name != default_features_key:
                pool.add(Request(partial(compute_for_one_plugin, plugin_name, feature_dict)))

        pool.wait()

        extrafeats = {}
        for feat_key in default_features:
            try:
                sel = feature_names["Standard Object Features"][feat_key]["selected"]
            except KeyError:
                # we don't always set this property to True, sometimes it's just not there. The only important
                # thing is that it's not False
                sel = True
            if not sel:
                # This feature has not been selected by the user. Remove it from the computed dict into a special dict
                # for default features
                feature = global_features["Standard Object Features"].pop(feat_key)
            else:
                feature = global_features["Standard Object Features"][feat_key]
            extrafeats[feat_key] = feature

        extrafeats = dict((k.replace(' ', ''), v)
                          for k, v in extrafeats.items())
        
        mincoords = extrafeats["Coord<Minimum>"].astype(int)
        maxcoords = extrafeats["Coord<Maximum>"].astype(int)
        nobj = mincoords.shape[0]
        
        # local features: loop over all objects
        def dictextend(a, b):
            for key in b:
                a[key].append(b[key])
            return a
        

        local_features = collections.defaultdict(lambda: collections.defaultdict(list))
        margin = max_margin(feature_names)
        has_local_features = {}
        for plugin_name, feature_dict in feature_names.items():
            has_local_features[plugin_name] = False
            for features in feature_dict.values():
                if 'margin' in features:
                    has_local_features[plugin_name] = True
                    break
            
                            
        if numpy.any(margin) > 0:
            #starting from 0, we stripped 0th background object in global computation
            for i in range(0, nobj):
                logger.debug("processing object {}".format(i))
                extent = self.compute_extent(i, image, mincoords, maxcoords, axes, margin)
                rawbbox = self.compute_rawbbox(image, extent, axes)
                #it's i+1 here, because the background has label 0
                binary_bbox = numpy.where(labels[tuple(extent)] == i+1, 1, 0).astype(numpy.bool)
                for plugin_name, feature_dict in feature_names.items():
                    if not has_local_features[plugin_name]:
                        continue
                    plugin = pluginManager.getPluginByName(plugin_name, "ObjectFeatures")
                    feats = plugin.plugin_object.compute_local(rawbbox, binary_bbox, feature_dict, axes)
                    local_features[plugin_name] = dictextend(local_features[plugin_name], feats)

        logger.debug("computing done, removing failures")
        # remove local features that failed
        for pname, pfeats in local_features.items():
            for key in list(pfeats.keys()):
                value = pfeats[key]
                try:
                    pfeats[key] = numpy.vstack(list(v.reshape(1, -1) for v in value))
                except:
                    logger.warning('feature {} failed'.format(key))
                    del pfeats[key]

        # merge the global and local features
        logger.debug("removed failed, merging")
        all_features = {}
        plugin_names = set(global_features.keys()) | set(local_features.keys())
        for name in plugin_names:
            d1 = global_features.get(name, {})
            d2 = local_features.get(name, {})
            all_features[name] = dict(list(d1.items()) + list(d2.items()))
        all_features[default_features_key]=extrafeats

        # reshape all features
        for pfeats in all_features.values():
            for key, value in pfeats.items():
                if value.shape[0] != nobj:
                    raise Exception('feature {} does not have enough rows, {} instead of {}'.format(key, value.shape[0], nobj))

                # because object classification operator expects nobj to
                # include background. FIXME: we should change that assumption.
                value = numpy.vstack((numpy.zeros(value.shape[1]),
                                   value))
                value = value.astype(numpy.float32) #turn Nones into numpy.NaNs

                assert value.dtype == numpy.float32
                assert value.shape[0] == nobj+1
                assert value.ndim == 2

                pfeats[key] = value
        logger.debug("merged, returning")
        return all_features

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Features:
            self.Output.setDirty(slice(None))
        else:
            axes = list(self.RawVolume.meta.getTaggedShape().keys())
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

            self.Output.setDirty(list(dirtyStart.values()), list(dirtyStop.values()))
