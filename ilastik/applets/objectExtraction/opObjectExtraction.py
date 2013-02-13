import numpy
import h5py
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion, List
import lazyflow.request

class OpLabelImage(Operator):
    name = "Label Image Accessor"
    BinaryImage = InputSlot()

    # List of background label in the order of channels of the binary
    # image; -1 if the label image should not be computed for that
    # channel
    BackgroundLabels = InputSlot(optional=True)
    defaultBackground = 0

    LabelImage = OutputSlot()

    # Pull the following output slot to compute the label image. This
    # slot is introduced in order to do a precomputation of the output
    # image and to write the results into a compressed hdf5 virtual
    # file instead of allocating space for all the requests.
    LabelImageComputation = OutputSlot(stype="float")

    def __init__(self, parent):
        super(OpLabelImage, self).__init__(parent)
        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)
        self._processedTimeSteps = set()
        self._lock = lazyflow.request.RequestLock()

    def setupOutputs(self):
        self.LabelImage.meta.assignFrom(self.BinaryImage.meta)
        self.LabelImage.meta.dtype = numpy.uint32
        self.LabelImageComputation.meta.dtype = numpy.float
        self.LabelImageComputation.meta.shape = [0]

        shape = self.LabelImage.meta.shape
        self._mem_h5.create_dataset('LabelImage', shape=shape,
                                    dtype=numpy.uint32, compression=1,
                                    chunks=True,
                                    )

    def cleanUp(self):
        self._mem_h5.close()
        super( OpLabelImage, self ).cleanUp()

    def _computeLabelImage(self, roi, destination):
        shape = self.BinaryImage.meta.shape
        channels = shape[-1]
        for t in range(roi.start[0], roi.stop[0]):
            if t not in self._processedTimeSteps:
                for c in range(channels):
                    print ("Calculating LabelImage at"
                           " t={}, c={}".format(t, c))
                    sroi = SubRegion(self.BinaryImage,
                                     start=[t,0,0,0,c],
                                     stop=[t+1,] + list(shape[1:-1]) + [c+1,])
                    a = self.BinaryImage.get(sroi).wait()
                    a = numpy.array(a[0,...,0], dtype=numpy.uint8)
                    if self.BackgroundLabels.ready():
                        backgroundLabel = self.BackgroundLabels.value[c]
                    else:
                        backgroundLabel = self.defaultBackground
                    if backgroundLabel != -1:
                        f = vigra.analysis.labelVolumeWithBackground
                        self._mem_h5['LabelImage'][t,...,c] = \
                            f(a, background_value=backgroundLabel)
                self._processedTimeSteps.add(t)

    def execute(self, slot, subindex, roi, destination):
        assert slot == self.LabelImage, "Unknown output slot"
        with self._lock:
            if slot is self.LabelImageComputation:
                self._computeLabelImage(roi, destination)

            elif slot is self.LabelImage:
                start, stop = roi.start[0], roi.stop[0]
                for t in range(start, stop):
                    slc = (slice(t, t + 1),) + roi.toSlice()[1:]
                    dslc = slice(t - start, t - start + 1)
                    if t not in self._processedTimeSteps:
                        self._computeLabelImage(roi, destination)
                    destination[dslc] = self._mem_h5['LabelImage'][slc]
                return destination

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.BinaryImage or slot is self.BackgroundLabels:
            self.LabelImage.setDirty(roi)
            start, stop = roi.start[0], roi.stop[0]
            for t in range(start, stop):
                try:
                    self._processedTimeSteps.remove(t)
                except KeyError:
                    continue
        else:
            print "Unknown dirty input slot: " + str(slot.name)


class OpRegionFeatures(Operator):
    RawImage = InputSlot()
    LabelImage = InputSlot()
    Output = OutputSlot(stype=Opaque, rtype=List)

    def __init__(self, features, parent):
        super(OpRegionFeatures, self).__init__(parent)
        self._cache = {}
        self.fixed = False
        self.features = features

    def setupOutputs(self):
        # number of time steps
        self.Output.meta.shape = self.LabelImage.meta.shape[0:1]
        self.Output.meta.dtype = object

    def extract(self, image, labels):
        image = numpy.asarray(image, dtype=numpy.float32)
        labels = numpy.asarray(labels, dtype=numpy.uint32)
        feats = vigra.analysis.extractRegionFeatures(image,
                                                     labels,
                                                     features=self.features,
                                                     ignoreLabel=0)
        return feats

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        feats = {}
        if len(roi) == 0:
            roi = range(self.LabelImage.meta.shape[0])
        for t in roi:
            if t in self._cache:
                feats_at = self._cache[t]
            elif self.fixed:
                feats_at = dict((f, numpy.asarray([[]])) for f in self.features)
            else:
                feats_at = []
                lshape = self.LabelImage.meta.shape
                numChannels = lshape[-1]
                for c in range(numChannels):
                    tcroi = SubRegion(self.LabelImage,
                                      start = [t,] + (len(lshape) - 2) * [0,] + [c,],
                                      stop = [t+1,] + list(lshape[1:-1]) + [c+1,])

                    image = self.RawImage.get(tcroi).wait()
                    axiskeys = self.RawImage.meta.getTaggedShape().keys()
                    assert axiskeys == list('txyzc'), "FIXME: OpRegionFeatures requires txyzc input data."
                    image = image[0,...,0] # assumes t,x,y,z,c

                    labels = self.LabelImage.get(tcroi).wait()
                    axiskeys = self.LabelImage.meta.getTaggedShape().keys()
                    assert axiskeys == list('txyzc'), "FIXME: OpRegionFeatures requires txyzc input data."
                    labels = labels[0,...,0] # assumes t,x,y,z,c
                    feats_at.append(self.extract(image, labels))
                self._cache[t] = feats_at
            feats[t] = feats_at
        return feats

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.LabelImage:
            self.Output.setDirty(List(self.Output,
                                      range(roi.start[0], roi.stop[0])))


class OpObjectCenterImage(Operator):
    """A cross in the center of each connected component."""
    BinaryImage = InputSlot()
    RegionCenters = InputSlot(rtype=List)
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
            centers = self.RegionCenters([t]).wait()
            for ch in range(roi.start[-1], roi.stop[-1]):
                centers = centers[t][ch]['RegionCenter']
                centers = numpy.asarray(centers, dtype=numpy.uint32)
                if centers.size:
                    centers = centers[1:,:]
                for center in centers:
                    x, y, z = center[0:3]
                    for dim in (1, 2, 3):
                        for offset in (-1, 0, 1):
                            c = [t, x, y, z, ch]
                            c[dim] += offset
                            c = tuple(c)
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

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()
    RegionCenters = OutputSlot(stype=Opaque, rtype=List)
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)

    default_features = [
        'Count',
        'RegionCenter',
        'Coord<ArgMaxWeight>',
        'Coord<Minimum>',
        'Coord<Maximum>',
    ]

    def __init__(self, parent):

        super(OpObjectExtraction, self).__init__(parent)

        # internal operators
        self._opLabelImage = OpLabelImage(parent=self)
        self._opRegFeats = OpRegionFeatures(features=self.default_features, parent=self)
        self._opObjectCenterImage = OpObjectCenterImage(parent=self)

        # connect internal operators
        self._opLabelImage.BinaryImage.connect(self.BinaryImage)
        self._opLabelImage.BackgroundLabels.connect(self.BackgroundLabels)

        self._opRegFeats.RawImage.connect(self.RawImage)
        self._opRegFeats.LabelImage.connect(self._opLabelImage.LabelImage)

        self._opObjectCenterImage.BinaryImage.connect(self.BinaryImage)
        self._opObjectCenterImage.RegionCenters.connect(self._opRegFeats.Output)

        # connect outputs
        self.LabelImage.connect(self._opLabelImage.LabelImage)
        self.ObjectCenterImage.connect(self._opObjectCenterImage.Output)
        self.RegionFeatures.connect(self._opRegFeats.Output)

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, inputSlot, subindex, roi):
        pass
