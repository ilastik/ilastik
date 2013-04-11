#Python
import collections
from collections import defaultdict

#SciPy
import numpy as np
import vigra.analysis

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.stype import Opaque
from lazyflow.rtype import List
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpCachedLabelImage, OpMultiArraySlicer2, OpMultiArrayStacker, OpArrayCache, OpCompressedCache

#ilastik
try:
    from ilastik.plugins import pluginManager
except:
    print "Warning: could not import pluginManager"


# These features are always calculated, but not used for prediction.
# They are needed by other applets.
gui_features = ['Coord<Minimum>', 'Coord<Maximum>', 'RegionCenter']

# to distinguish them, their name gets this suffix
gui_features_suffix = '_gui_only'

class OpRegionFeatures3d(Operator):
    """
    Produces region features (i.e. a vigra.analysis.RegionFeatureAccumulator) for a 3d image.
    The image MUST have xyz axes, and is permitted to have t and c axes of dim 1.
    """
    RawVolume = InputSlot()
    LabelVolume = InputSlot()
    Features = InputSlot(rtype=List, stype=Opaque)

    Output = OutputSlot()

    MARGIN = 30

    applet = None

    def __init__(self, *args, **kwargs):
        super(OpRegionFeatures3d, self).__init__(*args, **kwargs)
                
        # determine the applet that can block other applets downstream
        temp = self.parent
        while temp is not None:
            if temp.name == "Object Classification Workflow":
                #FIXME probably dangerous comparison, is there a better way to determine the extraction applet?
                self.applet = temp.objectExtractionApplet
                break
            temp = temp.parent

    def enableDownstream(self, enable=True):
        self.applet.enableDownstream(enable=enable)

    def setupOutputs(self):
        assert self.LabelVolume.meta.shape == self.RawVolume.meta.shape, "different shapes for label volume {} and raw data {}".format(self.LabelVolume.meta.shape, self.RawVolume.meta.shape)
        assert self.LabelVolume.meta.axistags == self.RawVolume.meta.axistags

        taggedOutputShape = self.LabelVolume.meta.getTaggedShape()
        if 't' in taggedOutputShape.keys():
            assert taggedOutputShape['t'] == 1
        if 'c' in taggedOutputShape.keys():
            assert taggedOutputShape['c'] == 1
        assert set(taggedOutputShape.keys()) - set('tc') == set('xyz'), "Input volumes must have xyz axes."

        # Remove the spatial dims (keep t and c, if present)
        del taggedOutputShape['x']
        del taggedOutputShape['y']
        del taggedOutputShape['z']

        self.Output.meta.shape = tuple(taggedOutputShape.values())
        self.Output.meta.axistags = vigra.defaultAxistags("".join(taggedOutputShape.keys()))
        # The features for the entire block (in xyz) are provided for the requested tc coordinates.
        self.Output.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        assert len(roi.start) == len(roi.stop) == len(self.Output.meta.shape)
        assert slot == self.Output

        # Process ENTIRE volume
        rawVolume = self.RawVolume[:].wait()
        labelVolume = self.LabelVolume[:].wait()

        # Convert to 3D (preserve axis order)
        spatialAxes = self.RawVolume.meta.getTaggedShape().keys()
        spatialAxes = filter(lambda k: k in 'xyz', spatialAxes)

        rawVolume = rawVolume.view(vigra.VigraArray)
        rawVolume.axistags = self.RawVolume.meta.axistags
        rawVolume3d = rawVolume.withAxes(*spatialAxes)

        labelVolume = labelVolume.view(vigra.VigraArray)
        labelVolume.axistags = self.LabelVolume.meta.axistags
        labelVolume3d = labelVolume.withAxes(*spatialAxes)

        assert np.prod(roi.stop - roi.start) == 1
        acc = self._extract(rawVolume3d, labelVolume3d)
        result[tuple(roi.start)] = acc
        return result

    def compute_bboxes(self, i, image, labels, mins, maxs, axes):
        xAxis, yAxis, zAxis = axes
        #find the bounding box
        minx = max(mins[i][xAxis] - self.MARGIN, 0)
        miny = max(mins[i][yAxis] - self.MARGIN, 0)
        minz = max(mins[i][zAxis], 0)
        min_xyz = minx, miny, minz

        # Coord<Minimum> and Coord<Maximum> give us the [min,max]
        # coords of the object, but we want the bounding box: [min,max), so add 1
        maxx = min(maxs[i][xAxis] + 1 + self.MARGIN, image.shape[xAxis])
        maxy = min(maxs[i][yAxis] + 1 + self.MARGIN, image.shape[yAxis])
        maxz = min(maxs[i][zAxis] + 1, image.shape[zAxis])
        max_xyz = maxx, maxy, maxz

        #FIXME: there must be a better way
        key = 3 * [None]
        key[xAxis] = slice(minx, maxx, None)
        key[yAxis] = slice(miny, maxy, None)
        key[zAxis] = slice(minz, maxz, None)
        key = tuple(key)

        ccbbox = labels[key]
        rawbbox = image[key]
        ccbboxobject = np.where(ccbbox == i, 1, 0)

        #find the context area around the object
        bboxshape = 3*[None]
        bboxshape[xAxis] = maxx - minx
        bboxshape[yAxis] = maxy - miny
        bboxshape[zAxis] = maxz - minz
        bboxshape = tuple(bboxshape)
        passed = np.zeros(bboxshape, dtype=bool)

        for iz in range(maxz - minz):
            #FIXME: shoot me, axistags
            bboxkey = 3*[None]
            bboxkey[xAxis] = slice(None, None, None)
            bboxkey[yAxis] = slice(None, None, None)
            bboxkey[zAxis] = iz
            bboxkey = tuple(bboxkey)
            #TODO: Ulli once mentioned that distance transform can be made anisotropic in 3D
            dt = vigra.filters.distanceTransform2D(np.asarray(ccbbox[bboxkey], dtype=np.float32))
            passed[bboxkey] = dt < self.MARGIN

        ccbboxexcl = passed - ccbboxobject

        return min_xyz, max_xyz, rawbbox, passed, ccbboxexcl, ccbboxobject

    def _extract(self, image, labels):
        assert len(image.shape) == len(labels.shape) == 3, "Images must be 3D.  Shapes were: {} and {}".format(image.shape, labels.shape)

        axes = (image.axistags.index('x'),
                image.axistags.index('y'),
                image.axistags.index('z'))

        image = np.asarray(image, dtype=np.float32)
        labels = np.asarray(labels, dtype=np.uint32)

        extrafeats = vigra.analysis.extractRegionFeatures(image, labels,
                                                          gui_features,
                                                          ignoreLabel=0)
        mins = extrafeats["Coord<Minimum >"]
        maxs = extrafeats["Coord<Maximum >"]
        nobj = mins.shape[0]

        feature_names = self.Features([]).wait()

        # do global features
        global_features = defaultdict(list)
        for plugin_name, feature_list in feature_names.iteritems():
            plugin = pluginManager.getPluginByName(plugin_name, "ObjectFeatures")
            feats = plugin.plugin_object.execute(image, labels, feature_list)
            global_features = dict(global_features.items() + feats.items())

        # local features: loop over all objects
        def dictextend(a, b):
            for key in b:
                a[key].append(b[key])
            return a

        local_features = defaultdict(list)
        for i in range(1, nobj):
            print "processing object {}".format(i)
            min_xyz, max_xyz, rawbbox, passed, ccbboxexcl, ccbboxobject = self.compute_bboxes(i, image, labels, mins, maxs, axes)

            for plugin_name, feature_list in feature_names.iteritems():
                plugin = pluginManager.getPluginByName(plugin_name, "ObjectFeatures")
                feats = plugin.plugin_object.execute_local(image, feature_list, axes, min_xyz, max_xyz, rawbbox, passed, ccbboxexcl, ccbboxobject)
                local_features = dictextend(local_features, feats)

        for key, value in local_features.iteritems():
            local_features[key] = np.vstack(list(v.reshape(1, -1) for v in value))

        all_features = dict(global_features.items() + local_features.items())

        for key, value in all_features.iteritems():
            if value.shape[0] != nobj - 1:
                raise Exception('feature {} does not have enough rows')

            # because object classification operator expects nobj to
            # include background. we should change that assumption.
            value = np.vstack((np.zeros(value.shape[1]),
                               value))

            value = value.astype(np.float32)

            assert value.dtype == np.float32
            assert value.shape[0] == nobj
            assert value.ndim == 2

            all_features[key] = value

        # add features needed by downstream applets. these should be
        # removed before classification.
        extrafeats = dict((k.replace(' ', '') + gui_features_suffix, v)
                          for k, v in extrafeats.iteritems())

        # downstream applets (i.e. object labeling) may now be used
        self.enableDownstream()
      
        return dict(all_features.items() + extrafeats.items())

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Features:
            self.Output.setDirty(slice(None))
        else:
            axes = self.RawVolume.meta.getTaggedShape().keys()
            dirtyStart = collections.OrderedDict(zip(axes, roi.start))
            dirtyStop = collections.OrderedDict(zip(axes, roi.stop))

            # Remove the spatial dims (keep t and c, if present)
            del dirtyStart['x']
            del dirtyStart['y']
            del dirtyStart['z']

            del dirtyStop['x']
            del dirtyStop['y']
            del dirtyStop['z']

            self.Output.setDirty(dirtyStart.values(), dirtyStop.values())

class OpRegionFeatures(Operator):
    RawImage = InputSlot()
    LabelImage = InputSlot()
    Features = InputSlot(rtype=List, stype=Opaque)
    Output = OutputSlot()

    # Schematic:
    #
    # RawImage ----> opRawTimeSlicer ----> opRawChannelSlicer -----
    #                                                              \
    # LabelImage --> opLabelTimeSlicer --> opLabelChannelSlicer --> opRegionFeatures3dBlocks --> opChannelStacker --> opTimeStacker -> Output

    def __init__(self, *args, **kwargs):
        super(OpRegionFeatures, self).__init__(*args, **kwargs)

        # Distribute the raw data
        self.opRawTimeSlicer = OpMultiArraySlicer2(parent=self)
        self.opRawTimeSlicer.AxisFlag.setValue('t')
        self.opRawTimeSlicer.Input.connect(self.RawImage)
        assert self.opRawTimeSlicer.Slices.level == 1

        self.opRawChannelSlicer = OperatorWrapper(OpMultiArraySlicer2, parent=self)
        self.opRawChannelSlicer.AxisFlag.setValue('c')
        self.opRawChannelSlicer.Input.connect(self.opRawTimeSlicer.Slices)
        assert self.opRawChannelSlicer.Slices.level == 2

        # Distribute the labels
        self.opLabelTimeSlicer = OpMultiArraySlicer2(parent=self)
        self.opLabelTimeSlicer.AxisFlag.setValue('t')
        self.opLabelTimeSlicer.Input.connect(self.LabelImage)
        assert self.opLabelTimeSlicer.Slices.level == 1

        self.opLabelChannelSlicer = OperatorWrapper(OpMultiArraySlicer2, parent=self)
        self.opLabelChannelSlicer.AxisFlag.setValue('c')
        self.opLabelChannelSlicer.Input.connect(self.opLabelTimeSlicer.Slices)
        assert self.opLabelChannelSlicer.Slices.level == 2

        class OpWrappedRegionFeatures3d(Operator):
            """
            This quick hack is necessary because there's not currently a way to wrap an OperatorWrapper.
            We need to double-wrap OpRegionFeatures3d, so we need this operator to provide the first level of wrapping.
            """
            RawVolume = InputSlot(level=1)
            LabelVolume = InputSlot(level=1)
            Features = InputSlot(rtype=List, stype=Opaque, level=1)
            Output = OutputSlot(level=1)

            def __init__(self, *args, **kwargs):
                super(OpWrappedRegionFeatures3d, self).__init__(*args, **kwargs)
                self._innerOperator = OperatorWrapper(OpRegionFeatures3d, operator_args=[], parent=self)
                self._innerOperator.RawVolume.connect(self.RawVolume)
                self._innerOperator.LabelVolume.connect(self.LabelVolume)
                self._innerOperator.Features.connect(self.Features)
                self.Output.connect(self._innerOperator.Output)

            def setupOutputs(self):
                pass

            def execute(self, slot, subindex, roi, destination):
                assert False, "Shouldn't get here."

            def propagateDirty(self, slot, subindex, roi):
                pass # Nothing to do...

        # Wrap OpRegionFeatures3d TWICE.
        self.opRegionFeatures3dBlocks = OperatorWrapper(OpWrappedRegionFeatures3d, operator_args=[], parent=self)
        assert self.opRegionFeatures3dBlocks.RawVolume.level == 2
        assert self.opRegionFeatures3dBlocks.LabelVolume.level == 2
        self.opRegionFeatures3dBlocks.RawVolume.connect(self.opRawChannelSlicer.Slices)
        self.opRegionFeatures3dBlocks.LabelVolume.connect(self.opLabelChannelSlicer.Slices)
        self.opRegionFeatures3dBlocks.Features.connect(self.Features)

        assert self.opRegionFeatures3dBlocks.Output.level == 2
        self.opChannelStacker = OperatorWrapper(OpMultiArrayStacker, parent=self)
        self.opChannelStacker.AxisFlag.setValue('c')

        assert self.opChannelStacker.Images.level == 2
        self.opChannelStacker.Images.connect(self.opRegionFeatures3dBlocks.Output)

        self.opTimeStacker = OpMultiArrayStacker(parent=self)
        self.opTimeStacker.AxisFlag.setValue('t')

        assert self.opChannelStacker.Output.level == 1
        assert self.opTimeStacker.Images.level == 1
        self.opTimeStacker.Images.connect(self.opChannelStacker.Output)

        # Connect our outputs
        self.Output.connect(self.opTimeStacker.Output)

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...

class OpCachedRegionFeatures(Operator):
    RawImage = InputSlot()
    LabelImage = InputSlot()
    CacheInput = InputSlot(optional=True)
    Features = InputSlot(rtype=List, stype=Opaque)

    Output = OutputSlot()
    CleanBlocks = OutputSlot()

    # Schematic:
    #
    # RawImage -----   blockshape=(t,c)=(1,1)
    #               \                        \
    # LabelImage ----> OpRegionFeatures ----> OpArrayCache --> Output
    #                                                     \
    #                                                      --> CleanBlocks

    def __init__(self, *args, **kwargs):
        super(OpCachedRegionFeatures, self).__init__(*args, **kwargs)

        # Hook up the labeler
        self._opRegionFeatures = OpRegionFeatures(parent=self)
        self._opRegionFeatures.RawImage.connect(self.RawImage)
        self._opRegionFeatures.LabelImage.connect(self.LabelImage)
        self._opRegionFeatures.Features.connect(self.Features)

        # Hook up the cache.
        self._opCache = OpArrayCache(parent=self)
        self._opCache.Input.connect(self._opRegionFeatures.Output)

        # Hook up our output slots
        self.Output.connect(self._opCache.Output)
        self.CleanBlocks.connect(self._opCache.CleanBlocks)

    def setupOutputs(self):
        assert self.LabelImage.meta.shape == self.RawImage.meta.shape
        assert self.LabelImage.meta.axistags == self.RawImage.meta.axistags

        # Every value in the regionfeatures output is cached seperately as it's own "block"
        blockshape = (1,) * len(self._opRegionFeatures.Output.meta.shape)
        self._opCache.blockShape.setValue(blockshape)

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.CacheInput
        slicing = roiToSlice(roi.start, roi.stop)
        self._opCache.Input[ slicing ] = value

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...

class OpAdaptTimeListRoi(Operator):
    """
    Adapts the tc array output from OpRegionFeatures to an Output slot that is called with a
    'List' rtype, where the roi is a list of time slices, and the output is a
    dict-of-lists (dict by time, list by channels).
    """
    Input = InputSlot()
    Output = OutputSlot(stype=Opaque, rtype=List)

    def setupOutputs(self):
        # Number of time steps
        self.Output.meta.shape = self.Input.meta.getTaggedShape()['t']
        self.Output.meta.dtype = object

    def execute(self, slot, subindex, roi, destination):
        assert slot == self.Output, "Unknown output slot"
        taggedShape = self.Input.meta.getTaggedShape()
        numChannels = taggedShape['c']
        channelIndex = taggedShape.keys().index('c')

        # Special case: An empty roi list means "request everything"
        if len(roi) == 0:
            roi = range(taggedShape['t'])

        taggedShape['t'] = 1
        timeIndex = taggedShape.keys().index('t')

        result = {}
        for t in roi:
            result[t] = []
            start = [0] * len(taggedShape)
            stop = taggedShape.values()
            start[timeIndex] = t
            stop[timeIndex] = t + 1
            a = self.Input(start, stop).wait()
            # Result is provided as a list of arrays by channel
            channelResults = np.split(a, numChannels, channelIndex)
            for channelResult in channelResults:
                # Extract from 1x1 ndarray
                result[t].append(channelResult.flat[0])
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.Input
        timeIndex = self.Input.meta.axistags.index('t')
        self.Output.setDirty(List(self.Output, range(roi.start[timeIndex], roi.stop[timeIndex])))

class OpObjectCenterImage(Operator):
    """A cross in the center of each connected component."""
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
        key = [coords[i] - roi.start[i] for i in range(len(roi.start))]
        return tuple(key)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        result[:] = 0
        for t in range(roi.start[0], roi.stop[0]):
            obj_features = self.RegionCenters([t]).wait()
            for ch in range(roi.start[-1], roi.stop[-1]):
                centers = obj_features[t][ch]['RegionCenter' + gui_features_suffix]
                if centers.size:
                    centers = centers[1:, :]
                for center in centers:
                    x, y, z = center[0:3]
                    c = (t, x, y, z, ch)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi, c)] = 255

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.RegionCenters:
            self.Output.setDirty(slice(None))


class OpObjectExtraction(Operator):
    name = "Object Extraction"

    RawImage = InputSlot()
    BinaryImage = InputSlot()
    BackgroundLabels = InputSlot()
    Features = InputSlot(rtype=List, stype=Opaque)

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)

    BlockwiseRegionFeatures = OutputSlot() # For compatibility with tracking workflow, the RegionFeatures output
                                           # has rtype=List, indexed by t.
                                           # For other workflows, output has rtype=ArrayLike, indexed by (t,c)

    LabelInputHdf5 = InputSlot(optional=True)
    LabelOutputHdf5 = OutputSlot()
    CleanLabelBlocks = OutputSlot()

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
        self._opLabelImage = OpCachedLabelImage(parent=self)
        self._opRegFeats = OpCachedRegionFeatures(parent=self)
        self._opRegFeatsAdaptOutput = OpAdaptTimeListRoi(parent=self)
        self._opObjectCenterImage = OpObjectCenterImage(parent=self)

        # connect internal operators
        self._opLabelImage.Input.connect(self.BinaryImage)
        self._opLabelImage.InputHdf5.connect(self.LabelInputHdf5)
        self._opLabelImage.BackgroundLabels.connect(self.BackgroundLabels)

        self._opRegFeats.RawImage.connect(self.RawImage)
        self._opRegFeats.LabelImage.connect(self._opLabelImage.Output)
        self._opRegFeats.Features.connect(self.Features)
        self.RegionFeaturesCleanBlocks.connect(self._opRegFeats.CleanBlocks)

        self._opRegFeatsAdaptOutput.Input.connect(self._opRegFeats.Output)

        self._opObjectCenterImage.BinaryImage.connect(self.BinaryImage)
        self._opObjectCenterImage.RegionCenters.connect(self._opRegFeatsAdaptOutput.Output)

        self._opCenterCache = OpCompressedCache(parent=self)
        self._opCenterCache.Input.connect(self._opObjectCenterImage.Output)

        # connect outputs
        self.LabelImage.connect(self._opLabelImage.Output)
        self.ObjectCenterImage.connect(self._opCenterCache.Output)
        self.RegionFeatures.connect(self._opRegFeatsAdaptOutput.Output)
        self.BlockwiseRegionFeatures.connect(self._opRegFeats.Output)
        self.LabelOutputHdf5.connect(self._opLabelImage.OutputHdf5)
        self.CleanLabelBlocks.connect(self._opLabelImage.CleanBlocks)

    def setupOutputs(self):
        taggedShape = self.RawImage.meta.getTaggedShape()
        for k in taggedShape.keys():
            if k == 't' or k == 'c':
                taggedShape[k] = 1
            else:
                taggedShape[k] = 256
        self._opCenterCache.BlockShape.setValue(tuple(taggedShape.values()))

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, inputSlot, subindex, roi):
        pass

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.LabelInputHdf5 or slot == self.RegionFeaturesCacheInput, "Invalid slot for setInSlot(): {}".format(slot.name)
        # Nothing to do here.
        # Our Input slots are directly fed into the cache,
        #  so all calls to __setitem__ are forwarded automatically
