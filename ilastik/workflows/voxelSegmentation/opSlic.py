"""
This file defines a simple operator for computing SLIC superpixels using scikit-image.
This example demonstrates how blockwise access to a 'global' operation
(such as superpixel generation) can cause undesirable results, and how
a cache can be used to force every request to be taken from a global result.
See the __main__ section, below.
It also includes a brief demonstration of lazyflow's OperatorWrapper mechanism.
"""
import logging

import numpy

import skimage.segmentation

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache
from lazyflow.roi import roiToSlice


logger = logging.getLogger(__name__)


class OpSlic(Operator):
    """
    Computes SLIC superpixels for any requested region of the image.
    Every request is considered independently, so it isn't desirable to
    concatenate the results of several requests into one large image.
    (If you do, the final image will appear 'quilted'.)
    """

    Input = InputSlot()

    # These are the slic parameters.
    # Here we give default values, but they can be changed.
    NumSegments = InputSlot()
    Compactness = InputSlot(value=0.4)
    MaxIter = InputSlot(value=10)

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint16

        tagged_shape = self.Input.meta.getTaggedShape()
        assert "c" in tagged_shape, "We assume the image has an explicit channel axis."
        assert next(reversed(tagged_shape))[0] == "c", "This code assumes that channel is the LAST axis."

        # Output will have exactly one channel, regardless of input channels
        tagged_shape["c"] = 1
        self.Output.meta.shape = tuple(tagged_shape.values())

    def execute(self, slot, subindex, roi, result):
        input_data = self.Input(roi.start, roi.stop).wait()
        assert slot == self.Output

        n_segments = self.NumSegments.value

        if n_segments == 0:
            # If the number of supervoxels was not given, use a default proportional to the number of voxels
            n_segments = numpy.int(numpy.prod(input_data.shape) / 2500)

        print(
            "calling skimage.segmentation.slic with {}".format(
                dict(
                    n_segments=n_segments,
                    compactness=self.Compactness.value,
                    max_iter=self.MaxIter.value,
                    multichannel=True,
                    enforce_connectivity=True,
                    convert2lab=False,
                )
            )
        )
        slic_sp = skimage.segmentation.slic(
            input_data,
            n_segments=n_segments,
            compactness=self.Compactness.value,
            max_iter=self.MaxIter.value,
            multichannel=True,
            enforce_connectivity=True,
            convert2lab=False,
        )  # Use with caution.
        # This would cause slic() to have special behavior for 3-channel data,
        # in which case we better really be dealing with RGB channels
        # (not, say 3 unrelated image features).

        # slic_sp has no channel axis, so insert that axis before copying to 'result'
        result[:] = slic_sp[..., None]
        print("got {} different supervoxels".format(numpy.max(result)))
        # import IPython; IPython.embed()

        return result

    def propagateDirty(self, slot, subindex, roi):
        # For some operators, a dirty in one part of the image only causes changes in nearby regions.
        # But for superpixel operators, changes in one corner can affect results in the opposite corner.
        # Therefore, everything is dirty.
        self.Output.setDirty()


class OpSlicBoundaries(Operator):
    SegmentationInput = InputSlot()
    BoundariesOutput = OutputSlot()

    def setupOutputs(self):
        self.BoundariesOutput.meta.assignFrom(self.SegmentationInput.meta)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.BoundariesOutput
        print("computing boundaries")
        slic_sp = self.SegmentationInput(roi.start, roi.stop).wait()
        boundaries = numpy.empty(slic_sp.shape[:3])

        for i in range(len(slic_sp)):
            # import IPython; IPython.embed()
            # print(slic_sp[i].shape)
            # print(boundaries[i].shape)
            reshaped_slic = slic_sp[i].reshape(boundaries[i].shape)
            boundaries[i] = skimage.segmentation.find_boundaries(reshaped_slic)

        # print(result.shape)
        # print(boundaries.shape)
        result[:] = boundaries[..., None]
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.BoundariesOutput.setDirty()


class OpSlicCached(Operator):
    """
    Computes SLIC superpixels and cache the result for the entire image.
    """

    # Same slots as OpSlic
    Input = InputSlot()
    NumSegments = InputSlot(value=0)
    Compactness = InputSlot(value=0.4)
    MaxIter = InputSlot(value=10)

    CacheInput = InputSlot(optional=True)
    Output = OutputSlot()
    CacheBoundariesInput = InputSlot(optional=True)
    BoundariesOutput = OutputSlot()

    CleanBlocks = OutputSlot()
    BoundariesCleanBlocks = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpSlicCached, self).__init__(*args, **kwargs)
        # This operator does no computation on its own.
        # Instead, it owns a little internal pipeline:
        #
        # Input --> OpSlic --> OpCache --> Output
        #

        # Feed all inputs directly into the operator that actually computes the slic superpixels
        self.opSlic = OpSlic(parent=self)
        self.opSlic.NumSegments.connect(self.NumSegments)
        self.opSlic.Compactness.connect(self.Compactness)
        self.opSlic.MaxIter.connect(self.MaxIter)
        self.opSlic.Input.connect(self.Input)

        self.opCache = OpBlockedArrayCache(parent=self)
        self.opCache.Input.connect(self.opSlic.Output)
        self.Output.connect(self.opCache.Output)
        self.CleanBlocks.connect(self.opCache.CleanBlocks)

        self.opSlicBoundaries = OpSlicBoundaries(parent=self)
        self.opSlicBoundaries.SegmentationInput.connect(self.opCache.Output)

        self.opBoundariesCache = OpBlockedArrayCache(parent=self)
        self.opBoundariesCache.Input.connect(self.opSlicBoundaries.BoundariesOutput)
        self.BoundariesOutput.connect(self.opBoundariesCache.Output)
        self.BoundariesCleanBlocks.connect(self.opBoundariesCache.CleanBlocks)

    def setInSlot(self, slot, subindex, roi, value):
        print("in setinslot")
        # Write the data into the cache
        if slot is self.CacheInput:
            slicing = roiToSlice(roi.start, roi.stop)
            self.opCache.Input[slicing] = value
        if slot is self.CacheBoundariesInput:
            slicing = roiToSlice(roi.start, roi.stop)
            self.opBoundariesCache.Input[slicing] = value

    def setupOutputs(self):
        # The cache is capable of requesting and storing results in small blocks,
        # but we want to force the entire image to be handled and stored at once.
        # Therefore, we set the 'block shape' to be the entire image -- there will only be one block stored in the cache.
        # (Note: The OpBlockedArrayCache.innerBlockshape slot is deprecated and ignored.)
        self.opCache.BlockShape.setValue(self.Input.meta.shape)
        self.opBoundariesCache.BlockShape.setValue(self.Input.meta.shape)

    def execute(self, slot, subindex, roi, result):
        # When an output slot is accessed, it asks for data from it's upstream connection (if any)
        # If it has no upstream connection, then it will call it's own operator's execute() function.
        # In this case, there is only one output slot, and it already has an upstream connection.
        # Therefore, this execute() function will never be accessed -- no slots would ever call it.
        assert False, "This function will never be called."

    def propagateDirty(self, slot, subindex, roi):
        # There's nothing to do here -- our Input slot is already directly connected to a
        # little pipeline that will propagate 'dirty notifications' all the way to the output.
        pass
