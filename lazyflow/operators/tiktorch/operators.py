from __future__ import absolute_import
from builtins import zip
from builtins import map
from builtins import range

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2021, the ilastik developers
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
#          http://ilastik.org/license/
###############################################################################
# Python
import copy
import logging

traceLogger = logging.getLogger("TRACE." + __name__)

# SciPy
import numpy

# lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal, OperatorWrapper
from lazyflow.roi import (
    sliceToRoi,
    roiToSlice,
    getIntersection,
    roiFromShape,
    nonzero_bounding_box,
    enlargeRoiForHalo,
    getIntersectingBlocks,
)

logger = logging.getLogger(__name__)


class OpTikTorchTrainClassifierBlocked(Operator):
    Images = InputSlot(level=1)
    Labels = InputSlot(level=1)
    nonzeroLabelBlocks = InputSlot(level=1)  # Used only in the pixelwise case.
    MaxLabel = InputSlot()
    ModelSession = InputSlot()
    BlockShape = InputSlot(level=1)

    UpdatedModelSession = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        for slot in [self.Images, self.Labels]:
            assert all(
                [s.meta.getAxisKeys()[-1] == "c" for s in slot]
            ), f"This opearator assumes channel is the last axis. problem: {slot}"

        self.ModelSession.meta.dtype = object
        self.ModelSession.meta.shape = (1,)

    def cleanUp(self):
        self.progressSignal.clean()
        super().cleanUp()

    def _collect_blocks(self, image_slot, label_slot, block_slicings):
        model = self.ModelSession.value
        image_data_blocks = []
        label_data_blocks = []
        block_ids = []
        for block_slicing in block_slicings:
            # Get labels
            block_label_roi = sliceToRoi(block_slicing, label_slot.meta.shape)
            block_label_data = label_slot(*block_label_roi).wait()

            bb_roi_within_block = numpy.array([[0] * len(block_label_data.shape), list(block_label_data.shape)])
            block_label_bb_roi = bb_roi_within_block + block_label_roi[0]

            # Ask for the halo needed by the classifier
            axiskeys = image_slot.meta.getAxisKeys()
            halo_shape = model.get_halo(axiskeys)
            assert len(halo_shape) == len(block_label_roi[0])
            assert halo_shape[-1] == 0, "Didn't expect a non-zero halo for channel dimension."

            # Expand block by halo, but keep clipped to image bounds
            padded_label_roi, bb_roi_within_padded = enlargeRoiForHalo(
                *block_label_bb_roi, shape=label_slot.meta.shape, sigma=halo_shape, window=1, return_result_roi=True
            )

            # Copy labels to new array, which has size == bounding-box + halo
            padded_label_data = numpy.zeros(padded_label_roi[1] - padded_label_roi[0], label_slot.meta.dtype)
            padded_label_data[roiToSlice(*bb_roi_within_padded)] = block_label_data[roiToSlice(*bb_roi_within_block)]

            padded_image_roi = numpy.array(padded_label_roi)
            assert (padded_image_roi[:, -1] == [0, 1]).all()
            num_channels = image_slot.meta.shape[-1]
            padded_image_roi[:, -1] = [0, num_channels]

            # Ensure the results are plain ndarray, not VigraArray,
            #  which some classifiers might have trouble with.
            padded_image_data = numpy.asarray(image_slot(*padded_image_roi).wait())

            image_data_blocks.append(padded_image_data)
            label_data_blocks.append(padded_label_data)
            block_ids.append(tuple(int(block_label_bb_roi[0][i]) for i, key in enumerate(axiskeys) if key != "c"))

        return image_data_blocks, label_data_blocks, block_ids

    def execute(self, slot, subindex, roi, result):
        model_session = self.ModelSession.value
        result[0] = model_session
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Labels:
            if not self.ModelSession.ready():
                return

            try:
                model_session = self.ModelSession.value
                image_slot = self.Images[subindex]
                label_slot = self.Labels[subindex]
                # todo: get block shape in a less hacky way
                block_shape = self.BlockShape[subindex].value
                block_starts = getIntersectingBlocks(block_shape, (roi.start, roi.stop))
                label_shape = label_slot.meta.shape
                axis_keys = label_slot.meta.getAxisKeys()
                block_slicings = [
                    [
                        slice(None)
                        if axis == "c"
                        else slice(dmax - dblock, dmax)
                        if dstart + dblock > dmax
                        else slice(dstart, dstart + dblock)
                        for dstart, dblock, dmax, axis in zip(block_start, block_shape, label_shape, axis_keys)
                    ]
                    for block_start in block_starts
                ]

                image_blocks, label_blocks, block_ids = self._collect_blocks(image_slot, label_slot, block_slicings)
                axistags = self.Images[0].meta.axistags

                model_session.update(image_blocks, label_blocks, axistags, block_ids)
            except Exception as e:
                logger.error(e, exc_info=True)
        else:
            self.UpdatedModelSession.setDirty()


class OpTikTorchClassifierPredict(Operator):
    Image = InputSlot()
    LabelsCount = InputSlot()
    ModelSession = InputSlot()
    BlockShape = InputSlot()

    PredictionMask = InputSlot(optional=True)

    PMaps = OutputSlot()

    def setupOutputs(self):
        assert self.Image.meta.getAxisKeys()[-1] == "c"
        nlabels = max(self.LabelsCount.value, 1)
        self.PMaps.meta.assignFrom(self.Image.meta)
        self.PMaps.meta.dtype = numpy.float32
        self.PMaps.meta.shape = self.Image.meta.shape[:-1] + (
            nlabels,
        )  # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)
        self.PMaps.meta.ideal_blockshape = self.BlockShape.value
        self.PMaps.meta.max_blockshape = self.BlockShape.value

    def propagateDirty(self, slot, subindex, roi):
        self.PMaps.setDirty()

    def execute(self, slot, subindex, roi, result):
        session = self.ModelSession.value

        # Training operator may return 'None' if there was no data to train with
        skip_prediction = session is None

        # Shortcut: If the mask is totally zero, skip this request entirely
        if not skip_prediction and self.PredictionMask.ready():
            mask_roi = numpy.array((roi.start, roi.stop))
            mask_roi[:, -1:] = [[0], [1]]
            start, stop = list(map(tuple, mask_roi))
            mask = self.PredictionMask(start, stop).wait()
            skip_prediction = not numpy.any(mask)

        if skip_prediction:
            result[:] = 0.0
            return result

        # make sure to only request channels we actually have in raw!
        # roi in execute is wrt output
        axiskeys = self.Image.meta.getAxisKeys()
        roistart = list(roi.start)
        prediction_channel_start = roistart[-1]
        roistart[-1] = 0
        raw_channels = self.Image.meta.shape[-1]
        roistop = list(roi.stop)
        prediction_channel_stop = roistop[-1]
        roistop[-1] = raw_channels
        upstream_roi = (roistart, roistop)

        halo = numpy.array(session.get_halos(axiskeys)[0])

        assert len(halo) == len(upstream_roi[0])
        assert axiskeys[-1] == "c"
        assert halo[-1] == 0, "Didn't expect a non-zero halo for channel dimension."

        # simply add halo to requested roi
        upstream_roi = numpy.array(upstream_roi)
        upstream_roi[0] -= halo
        upstream_roi[1] += halo

        # Extend block further to reach a valid shape
        min_shape = upstream_roi[1] - upstream_roi[0]
        for vs in session.get_input_shapes(axiskeys)[0]:
            if all(m <= v for m, v in zip(min_shape, vs)):
                valid_shape = numpy.array(vs)
                if any(m < v for m, v in zip(min_shape, vs)):
                    shape_diff = valid_shape - min_shape
                    upstream_roi[0] -= numpy.array([(a + 1) // 2 for a in shape_diff])
                    upstream_roi[1] += numpy.array([a // 2 for a in shape_diff])

                break
        else:
            raise ValueError(
                f"The requested roi {roi} with halo {halo} is too large for the "
                f"session's valid shapes: {session.get_input_shapes(axiskeys)}"
            )

        # Determine how to extract the data from the result (without halo, padding)
        downstream_roi = numpy.array((roi.start, roi.stop))
        predictions_roi = downstream_roi - upstream_roi[0]
        predictions_roi[0, -1] = prediction_channel_start
        predictions_roi[1, -1] = prediction_channel_stop

        # Limit upstream roi to self.Image.meta.shape and determine padding
        # todo: manage padding with tiktorch
        im_shape = self.Image.meta.shape
        padding = [(max(0, -a0), max(0, a1 - s)) for a0, a1, s in zip(*upstream_roi, im_shape)]
        upstream_roi = numpy.array([[max(0, a0), min(a1, s)] for a0, a1, s in zip(*upstream_roi, im_shape)]).T

        # Request all upstream channels
        input_channels = im_shape[-1]
        upstream_roi[:, -1] = [0, input_channels]
        padding[-1] = (0, 0)  # do not pad channels

        # Request the data
        input_data = self.Image(*upstream_roi).wait()
        axistags = self.Image.meta.axistags

        # Pad the data
        input_data = numpy.pad(input_data, padding, mode="reflect")

        try:
            result[...] = session.predict(input_data, predictions_roi, axistags)
        except Exception as e:
            logger.exception("Failed to predict")

        return result
