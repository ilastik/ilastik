from __future__ import division
from builtins import map
from builtins import zip

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
# 		   http://ilastik.org/license/
###############################################################################
# Built-in
import logging
import collections

# Third-party
import numpy
import vigra

# Lazyflow
from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.roi import (
    TinyVector,
    getIntersectingBlocks,
    getIntersectingRois,
    getBlockBounds,
    roiToSlice,
    getIntersection,
    roiFromShape,
)
from lazyflow.operators.opCompressedCache import OpUnmanagedCompressedCache
from lazyflow.rtype import SubRegion
from lazyflow.utility.data_semantics import ImageTypes

logger = logging.getLogger(__name__)


class OpCompressedUserLabelArray(OpUnmanagedCompressedCache):
    """
    A subclass of OpUnmanagedCompressedCache that is suitable for storing user-drawn label pixels.
    (This is not a 'managed' cache because its data must never be deleted by the memory manager.)
    Note that setInSlot has special functionality (only non-zero pixels are written, and there is also an "eraser" pixel value).

    See note below about blockshape changes.
    """

    # Input = InputSlot()
    shape = InputSlot(optional=True)  # Should not be used.
    eraser = InputSlot()
    deleteLabel = InputSlot(optional=True)
    blockShape = InputSlot()  # If the blockshape is changed after labels have been stored, all cache data is lost.

    # Output = OutputSlot()
    # nonzeroValues = OutputSlot()
    # nonzeroCoordinates = OutputSlot()
    nonzeroBlocks = OutputSlot()
    # maxLabel = OutputSlot()

    Projection2D = OutputSlot(allow_mask=True)  # A somewhat magic output that returns a projection of all
    # label data underneath a given roi, from all slices.
    # If, for example, a 256x1x256 tile is requested from this slot,
    # It will return a projection of ALL labels that fall within the 256 x ... x 256 tile.
    # (The projection axis is *inferred* from the shape of the requested data).
    # The projection data is float32 between 0.0 and 1.0, where:
    # - Exactly 0.0 means "no labels under this pixel"
    # - 1/256.0 means "labels in the first slice"
    # - ...
    # - 1.0 means "last slice"
    # The output is suitable for display in a colortable.

    def __init__(self, *args, **kwargs):
        self._blockshape = None
        self._label_to_purge = 0
        super(OpCompressedUserLabelArray, self).__init__(*args, **kwargs)

        # ignoring the ideal chunk shape is ok because we use the input only
        # to get the volume shape
        self._ignore_ideal_blockshape = True

    def clearLabel(self, label_value):
        """
        Clear (reset to 0) all pixels of the given label value.
        Unlike using the deleteLabel slot, this function does not "shift down" all labels above this label value.
        """
        self._purge_label(label_value, False)

    def mergeLabels(self, from_label, into_label):
        self._purge_label(from_label, True, into_label)

    def setupOutputs(self):
        # Due to a temporary naming clash, pass our subclass blockshape to the superclass
        # TODO: Fix this by renaming the BlockShape slots to be consistent.
        self.BlockShape.setValue(self.blockShape.value)

        super(OpCompressedUserLabelArray, self).setupOutputs()
        if self.Output.meta.NOTREADY:
            self.nonzeroBlocks.meta.NOTREADY = True
            self.Projection2D.meta.NOTREADY = True
            return
        self.nonzeroBlocks.meta.dtype = object
        self.nonzeroBlocks.meta.shape = (1,)

        # Overwrite the Output metadata (should be uint8 no matter what the input data is...)
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint8
        self.Output.meta.shape = self.Input.meta.shape[:-1] + (1,)
        self.Output.meta.drange = (0, 255)
        self.Output.meta.data_semantics = ImageTypes.Labels

        # is_blocked_cache attribute indicates that this cache gives block-wise
        # updates when written to. Attribute used in LabelExplorerWidget.
        self.Output.meta.is_blocked_cache = True
        self.Output.meta.ideal_blockshape = self.BlockShape.value
        self.OutputHdf5.meta.assignFrom(self.Output.meta)

        # The Projection2D slot is a strange beast:
        # It appears to have the same output shape as any other output slot,
        #  but it can only be accessed in 2D slices.
        self.Projection2D.meta.assignFrom(self.Output.meta)
        self.Projection2D.meta.dtype = numpy.float32
        self.Projection2D.meta.drange = (0.0, 1.0)

        # Overwrite the blockshape
        if self._blockshape is None:
            self._blockshape = numpy.minimum(self.BlockShape.value, self.Output.meta.shape)
        elif self.blockShape.value != self._blockshape:
            nonzero_blocks_destination = [None]
            self._execute_nonzeroBlocks(nonzero_blocks_destination)
            nonzero_blocks = nonzero_blocks_destination[0]
            if len(nonzero_blocks) > 0:
                raise RuntimeError(
                    "You are not permitted to reconfigure the labeling operator after you've already stored labels in it."
                )

        # Overwrite chunkshape now that blockshape has been overwritten
        self._chunkshape = self._chooseChunkshape(self._blockshape)

        self._eraser_magic_value = self.eraser.value

        # Are we being told to delete a label?
        if self.deleteLabel.ready():
            new_purge_label = self.deleteLabel.value
            if self._label_to_purge != new_purge_label:
                self._label_to_purge = new_purge_label
                if self._label_to_purge > 0:
                    self._purge_label(self._label_to_purge, True)

    def _purge_label(self, label_to_purge, decrement_remaining, replacement_value=0):
        """
        Scan through all labeled pixels.
        (1) Reassign all pixels of the given value (set to replacement_value)
        (2) If decrement_remaining=True, decrement all labels above that
            value so the set of stored labels remains consecutive.
            Note that the decrement is performed AFTER replacement.
        """
        changed_block_rois = []
        # stored_block_rois = self.CleanBlocks.value
        stored_block_roi_destination = [None]
        self.execute(self.CleanBlocks, (), SubRegion(self.Output, (0,), (1,)), stored_block_roi_destination)
        stored_block_rois = stored_block_roi_destination[0]

        for block_roi in stored_block_rois:
            # Get data
            block_shape = numpy.subtract(block_roi[1], block_roi[0])
            block = self.Output.stype.allocateDestination(SubRegion(self.Output, *roiFromShape(block_shape)))

            self.execute(self.Output, (), SubRegion(self.Output, *block_roi), block)

            # Locate pixels to change
            matching_label_coords = numpy.nonzero(block == label_to_purge)

            # Change the data
            block[matching_label_coords] = replacement_value
            coords_to_decrement = block > label_to_purge
            if decrement_remaining:
                block[coords_to_decrement] -= numpy.uint8(1)

            # Update cache with the new data (only if something really changed)
            if len(matching_label_coords[0]) > 0 or (decrement_remaining and coords_to_decrement.sum() > 0):
                super(OpCompressedUserLabelArray, self)._setInSlotInput(
                    self.Input, (), SubRegion(self.Output, *block_roi), block, store_zero_blocks=False
                )
                changed_block_rois.append(block_roi)

        for block_roi in changed_block_rois:
            # FIXME: Shouldn't this dirty notification be handled in OpUnmanagedCompressedCache?
            self.Output.setDirty(*block_roi)

    def execute(self, slot, subindex, roi, destination):
        if slot == self.Output:
            self._executeOutput(roi, destination)
        elif slot == self.nonzeroBlocks:
            self._execute_nonzeroBlocks(destination)
        elif slot == self.Projection2D:
            self._executeProjection2D(roi, destination)
        else:
            return super(OpCompressedUserLabelArray, self).execute(slot, subindex, roi, destination)

    def _executeOutput(self, roi, destination):
        assert len(roi.stop) == len(
            self.Output.meta.shape
        ), "roi: {} has the wrong number of dimensions for Output shape: {}".format(roi, self.Output.meta.shape)
        assert numpy.less_equal(
            roi.stop, self.Output.meta.shape
        ).all(), "roi: {} is out-of-bounds for Output shape: {}".format(roi, self.Output.meta.shape)

        block_starts = getIntersectingBlocks(self._blockshape, (roi.start, roi.stop))
        self._copyData(roi, destination, block_starts)
        return destination

    def _execute_nonzeroBlocks(self, destination):
        stored_block_rois_destination = [None]
        self._executeCleanBlocks(stored_block_rois_destination)
        stored_block_rois = stored_block_rois_destination[0]
        block_slicings = [roiToSlice(*block_roi) for block_roi in stored_block_rois]
        destination[0] = block_slicings

    def _executeProjection2D(self, roi, destination):
        assert sum(TinyVector(destination.shape) > 1) <= 2, "Projection result must be exactly 2D"

        # First, we have to determine which axis we are projecting along.
        # We infer this from the shape of the roi.
        # For example, if the roi is of shape
        #  zyx = (1,256,256), then we know we're projecting along Z
        # If more than one axis has a width of 1, then we choose an
        #  axis according to the following priority order: zyxt
        tagged_input_shape = self.Output.meta.getTaggedShape()
        tagged_result_shape = collections.OrderedDict(list(zip(list(tagged_input_shape.keys()), destination.shape)))
        nonprojection_axes = []
        for key in list(tagged_input_shape.keys()):
            if key == "c" or tagged_input_shape[key] == 1 or tagged_result_shape[key] > 1:
                nonprojection_axes.append(key)

        possible_projection_axes = set(tagged_input_shape) - set(nonprojection_axes)
        if len(possible_projection_axes) == 0:
            # If the image is 2D to begin with,
            #   then the projection is simply the same as the normal output,
            #   EXCEPT it is made binary
            self.Output(roi.start, roi.stop).writeInto(destination).wait()

            # make binary
            numpy.greater(destination, 0, out=destination)
            return

        for k in "zyxt":
            if k in possible_projection_axes:
                projection_axis_key = k
                break

        # Now we know which axis we're projecting along.
        # Proceed with the projection, working blockwise to avoid unecessary work in unlabeled blocks

        projection_axis_index = self.Output.meta.getAxisKeys().index(projection_axis_key)
        projection_length = tagged_input_shape[projection_axis_key]
        input_roi = roi.copy()
        input_roi.start[projection_axis_index] = 0
        input_roi.stop[projection_axis_index] = projection_length

        destination[:] = 0.0

        # Get the logical blocking.
        block_starts = getIntersectingBlocks(self._blockshape, (input_roi.start, input_roi.stop))

        # (Parallelism wouldn't help here: h5py will serialize these requests anyway)
        block_starts = list(map(tuple, block_starts))
        for block_start in block_starts:
            if block_start not in self._cacheFiles:
                # No label data in this block.  Move on.
                continue

            entire_block_roi = getBlockBounds(self.Output.meta.shape, self._blockshape, block_start)

            # This block's portion of the roi
            intersecting_roi = getIntersection((input_roi.start, input_roi.stop), entire_block_roi)

            # Compute slicing within the deep array and slicing within this block
            deep_relative_intersection = numpy.subtract(intersecting_roi, input_roi.start)
            block_relative_intersection = numpy.subtract(intersecting_roi, block_start)
            block_relative_intersection_slicing = roiToSlice(*block_relative_intersection)

            block = self._getBlockDataset(entire_block_roi)
            deep_data = None
            if self.Output.meta.has_mask:
                deep_data = numpy.ma.masked_array(
                    block["data"][block_relative_intersection_slicing],
                    mask=block["mask"][block_relative_intersection_slicing],
                    fill_value=block["fill_value"][()],
                    shrink=False,
                )
            else:
                deep_data = block[block_relative_intersection_slicing]

            # make binary and convert to float (must copy)
            deep_data_float = deep_data.astype(numpy.float32)
            deep_data_float[deep_data_float.nonzero()] = 1

            # multiply by slice-index
            deep_data_view = numpy.rollaxis(deep_data_float, projection_axis_index, 0)

            min_deep_slice_index = deep_relative_intersection[0][projection_axis_index]
            max_deep_slice_index = deep_relative_intersection[1][projection_axis_index]

            def calc_color_value(slice_index):
                # Note 1: We assume that the colortable has at least 256 entries in it,
                #           so, we try to ensure that all colors are above 1/256
                #           (we don't want colors in low slices to be rounded to 0)
                # Note 2: Ideally, we'd use a min projection in the code below, so that
                #           labels in the "back" slices would appear occluded.  But the
                #           min projection would favor 0.0.  Instead, we invert the
                #           relationship between color and slice index, do a max projection,
                #           and then re-invert the colors after everything is done.
                #           Hence, this function starts with (1.0 - ...)
                return (1.0 - ((float(slice_index) / projection_length))) * (1.0 - (1.0 / 255)) + (1.0 / 255.0)

            min_color_value = calc_color_value(min_deep_slice_index)
            max_color_value = calc_color_value(max_deep_slice_index)

            num_slices = max_deep_slice_index - min_deep_slice_index
            deep_data_view *= numpy.linspace(min_color_value, max_color_value, num=num_slices)[
                (slice(None),) + (None,) * (deep_data_view.ndim - 1)
            ]

            # Take the max projection of this block's data.
            block_max_projection = deep_data_float.max(axis=projection_axis_index)
            block_max_projection = numpy.ma.expand_dims(block_max_projection, axis=projection_axis_index)

            # Merge this block's projection into the overall projection.
            destination_relative_intersection = numpy.array(deep_relative_intersection)
            destination_relative_intersection[:, projection_axis_index] = (0, 1)
            destination_relative_intersection_slicing = roiToSlice(*destination_relative_intersection)

            destination_subview = destination[destination_relative_intersection_slicing]
            numpy.maximum(block_max_projection, destination_subview, out=destination_subview)

            # Invert the nonzero pixels so increasing colors correspond to increasing slices.
            # See comment in calc_color_value(), above.
            destination_subview[destination_subview.nonzero()] -= 1
            destination_subview[()] = -destination_subview

        return

    def _copyData(self, roi, destination, block_starts):
        """
        Copy data from each block into the destination array.
        For blocks that aren't currently stored, just write zeros.
        """
        # (Parallelism not needed here: h5py will serialize these requests anyway)
        block_starts = list(map(tuple, block_starts))
        for block_start in block_starts:
            entire_block_roi = getBlockBounds(self.Output.meta.shape, self._blockshape, block_start)

            # This block's portion of the roi
            intersecting_roi = getIntersection((roi.start, roi.stop), entire_block_roi)

            # Compute slicing within destination array and slicing within this block
            destination_relative_intersection = numpy.subtract(intersecting_roi, roi.start)
            block_relative_intersection = numpy.subtract(intersecting_roi, block_start)
            destination_relative_intersection_slicing = roiToSlice(*destination_relative_intersection)
            block_relative_intersection_slicing = roiToSlice(*block_relative_intersection)

            if block_start in self._cacheFiles:
                # Copy from block to destination
                dataset = self._getBlockDataset(entire_block_roi)

                if self.Output.meta.has_mask:
                    destination[destination_relative_intersection_slicing] = dataset["data"][
                        block_relative_intersection_slicing
                    ]
                    destination.mask[destination_relative_intersection_slicing] = dataset["mask"][
                        block_relative_intersection_slicing
                    ]
                    destination.fill_value = dataset["fill_value"][()]
                else:
                    destination[destination_relative_intersection_slicing] = dataset[
                        block_relative_intersection_slicing
                    ]
            else:
                # Not stored yet.  Overwrite with zeros.
                destination[destination_relative_intersection_slicing] = 0

    def propagateDirty(self, slot, subindex, roi):
        # There should be no way to make the output dirty except via setInSlot()
        pass

    def setInSlot(self, slot, subindex, roi, new_pixels):
        if slot is self.Input:
            self._setInSlotInput(slot, subindex, roi, new_pixels)
        else:
            # We don't yet support the InputHdf5 slot in this function.
            assert False, "Unsupported slot for setInSlot: {}".format(slot.name)

    def _setInSlotInput(self, slot, subindex, roi, new_pixels):
        """
        Since this is a label array, inserting pixels has a special meaning:
        We only overwrite the new non-zero pixels. In the new data, zeros mean "don't change".

        So, here's what each pixel we're adding means:
        0: don't change
        1: change to 1
        2: change to 2
        ...
        N: change to N
        eraser_magic_value: change to 0
        """
        if isinstance(new_pixels, vigra.VigraArray):
            new_pixels = new_pixels.view(numpy.ndarray)

        # Get logical blocking.
        block_rois = getIntersectingRois(self.Output.meta.shape, self._blockshape, (roi.start, roi.stop))
        # Convert to tuples
        block_rois = [(tuple(start), tuple(stop)) for start, stop in block_rois]

        max_label = 0
        for block_roi in block_rois:
            roi_within_data = numpy.array(block_roi) - roi.start
            new_block_pixels = new_pixels[roiToSlice(*roi_within_data)]

            # Shortcut: Nothing to change if this block is all zeros.
            if not new_block_pixels.any():
                continue

            block_slot_roi = SubRegion(self.Output, *block_roi)

            # Extract the data to modify
            original_block_data = self.Output.stype.allocateDestination(block_slot_roi)
            self.execute(self.Output, (), block_slot_roi, original_block_data)

            # Reset the pixels we need to change (so we can use |= below)
            original_block_data[new_block_pixels.nonzero()] = 0

            # Update
            original_block_data |= new_block_pixels

            # Replace 'eraser' values with zeros.
            cleaned_block_data = original_block_data.copy()
            cleaned_block_data[original_block_data == self._eraser_magic_value] = 0

            # Set in the cache (our superclass).
            super(OpCompressedUserLabelArray, self)._setInSlotInput(
                slot, subindex, block_slot_roi, cleaned_block_data, store_zero_blocks=False
            )

            max_label = max(max_label, cleaned_block_data.max())

            # We could wait to send out one big dirty notification (instead of one per block),
            # But that might result in a lot of unnecessarily dirty pixels in cases when the
            # new_pixels were mostly empty (such as when importing labels from disk).
            # That's bad for downstream operators like OpFeatureMatrixCache
            # So instead, we only send notifications for the blocks that were touched.
            # During labeling, it makes no difference.
            # During project import, this is slightly worse.
            # But during label import from disk, this is very important.a
            # FIXME: Shouldn't this notification be triggered from within OpUnmanagedCompressedCache?
            self.Output.setDirty(*block_roi)

        return max_label  # Internal use: Return max label

    def ingestData(self, slot):
        """
        Read the data from the given slot and copy it into this cache.
        The rules about special pixel meanings apply here, just like setInSlot

        Returns: the max label found in the slot.
        """
        assert self._blockshape is not None
        assert self.Output.meta.shape[:-1] == slot.meta.shape[:-1], "{} != {}".format(
            self.Output.meta.shape, slot.meta.shape
        )
        max_label = 0

        # Get logical blocking.
        block_starts = getIntersectingBlocks(self._blockshape, roiFromShape(self.Output.meta.shape))
        block_starts = list(map(tuple, block_starts))

        # Write each block
        for block_start in block_starts:
            block_roi = getBlockBounds(self.Output.meta.shape, self._blockshape, block_start)

            # Request the block data
            block_data = slot(*block_roi).wait()

            # Write into the array
            subregion_roi = SubRegion(self.Output, *block_roi)
            cleaned_block_max = self._setInSlotInput(self.Input, (), subregion_roi, block_data)

            max_label = max(max_label, cleaned_block_max)

        return max_label
