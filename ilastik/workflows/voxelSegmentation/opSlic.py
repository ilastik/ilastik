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
from lazyflow.operators import OpBlockedArrayCache, OpReorderAxes
from lazyflow.roi import roiToSlice
from lazyflow.utility.helpers import bigintprod


import vigra

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
            n_segments = numpy.int64(bigintprod(input_data.shape) / 2500)

        logger.debug(
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
        # import IPython; IPython.embed()

        return result

    def propagateDirty(self, slot, subindex, roi):
        # For some operators, a dirty in one part of the image only causes changes in nearby regions.
        # But for superpixel operators, changes in one corner can affect results in the opposite corner.
        # Therefore, everything is dirty.
        self.Output.setDirty()


class OpSlicBoundariesCached(Operator):
    SegmentationInput = InputSlot()
    BoundariesOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.opReorderInput = OpReorderAxes(parent=self, AxisOrder="tzyxc", Input=self.SegmentationInput)
        self.opSlic = OpSlicBoundaries(parent=self)
        self.opSlic.SegmentationInput.connect(self.opReorderInput.Output)
        self.opReorderOutput = OpReorderAxes(parent=self, Input=self.opSlic.BoundariesOutput)
        self.BoundariesOutput.connect(self.opReorderOutput.Output)

    def setupOutputs(self):
        axes = self.SegmentationInput.meta.getAxisKeys()
        self.opReorderOutput.AxisOrder.setValue(axes)

    def execute(self, slot, subindex, roi, result):
        assert False, "Should not be here, everything connected internally!"

    def propagateDirty(self, slot, subindex, roi):
        self.BoundariesOutput.setDirty()


class OpSlicBoundaries(Operator):
    SegmentationInput = InputSlot()
    BoundariesOutput = OutputSlot()

    def setupOutputs(self):
        self.BoundariesOutput.meta.assignFrom(self.SegmentationInput.meta)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.BoundariesOutput

        # breakpoint()
        result = vigra.taggedView(result, self.BoundariesOutput.meta.axistags)
        # Iterate over time slices to avoid connected component problems.
        for t_index, t in enumerate(range(roi.start[0], roi.stop[0])):
            t_slice_roi = roi.copy()
            t_slice_roi.start[0] = t
            t_slice_roi.stop[0] = t + 1
            for z_index, z in enumerate(range(t_slice_roi.start[1], t_slice_roi.stop[1])):
                z_slice_roi = t_slice_roi.copy()
                z_slice_roi.start[1] = z
                z_slice_roi.stop[1] = z + 1
                data_slice = self.SegmentationInput(z_slice_roi.start, z_slice_roi.stop).wait().squeeze()
                assert len(data_slice.shape) == 2
                boundaries = skimage.segmentation.find_boundaries(data_slice)
                result[t_index, z_index, ..., 0] = boundaries

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

        self.opSlicBoundaries = OpSlicBoundariesCached(parent=self)
        self.opSlicBoundaries.SegmentationInput.connect(self.opCache.Output)

        self.opBoundariesCache = OpBlockedArrayCache(parent=self)
        self.opBoundariesCache.Input.connect(self.opSlicBoundaries.BoundariesOutput)
        self.BoundariesOutput.connect(self.opBoundariesCache.Output)
        self.BoundariesCleanBlocks.connect(self.opBoundariesCache.CleanBlocks)

    def setInSlot(self, slot, subindex, roi, value):
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
