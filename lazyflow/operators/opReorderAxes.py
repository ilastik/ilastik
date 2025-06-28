from builtins import map
from builtins import zip
import lazyflow.utility.resolution

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
import collections
import copy
import logging
import numpy
import vigra

from functools import partial
from lazyflow.graph import Operator, InputSlot, OutputSlot


logger = logging.getLogger(__name__)


class OpReorderAxes(Operator):
    Input = InputSlot()
    AxisOrder = InputSlot()  # string: The desired output axis order
    Output = OutputSlot()

    def __init__(self, graph=None, parent=None, Input=None, AxisOrder="tzyxc"):
        super().__init__(graph=graph, parent=parent)
        self.Input.setOrConnectIfAvailable(Input)
        self.AxisOrder.setOrConnectIfAvailable(AxisOrder)

    def setupOutputs(self):
        if "c" not in self.AxisOrder.value:
            # This is helpful in order to convert our internal axis order to 'tczyx'
            logger.debug("Reordering an array without an explicit channel axis.")

        if self._cleaningUp:
            self.Output.meta.NOTREADY = True
            return
        output_order = "".join(self.AxisOrder.value)
        input_order = self.Input.meta.getAxisKeys()
        input_tags = self.Input.meta.axistags
        tagged_input_shape = self.Input.meta.getTaggedShape()

        tagged_ideal_blockshape = None
        if self.Input.meta.ideal_blockshape is not None:
            assert len(input_order) == len(self.Input.meta.ideal_blockshape)
            tagged_ideal_blockshape = collections.OrderedDict(list(zip(input_order, self.Input.meta.ideal_blockshape)))

        tagged_max_blockshape = None
        if self.Input.meta.max_blockshape is not None:
            assert len(input_order) == len(self.Input.meta.max_blockshape)
            tagged_max_blockshape = collections.OrderedDict(list(zip(input_order, self.Input.meta.max_blockshape)))

        # Check for errors
        self._invalid_axes = []
        for a in set(input_order) - set(output_order):
            if tagged_input_shape[a] > 1:
                # It looks like someone is attempting to drop a NON-singleton axis,
                #   which is an error.
                # But maybe they're about to change BOTH Input and AxisOrder, which
                #   could result in a valid output_order.
                # Instead of asserting here, we'll keep track of the invalid axes.
                # We'll assert if the user actually attempts to call exceute()
                #   without fixing the axis order.
                self._invalid_axes.append(a)

        # Determine output shape/axistags
        output_shape = []
        def_output_tags = vigra.defaultAxistags(str(output_order))
        output_tags = lazyflow.utility.resolution.unitTags(def_output_tags)
        if not isinstance(input_tags, lazyflow.utility.resolution.unitTags):
            input_tags = lazyflow.utility.resolution.unitTags(input_tags)
        ideal_blockshape = []
        max_blockshape = []
        for a in output_order:
            if a in input_order:
                output_shape.append(tagged_input_shape[a])
                # Preserve full AxisInfo for retained axes
                output_tags[a] = input_tags[a]
                tag = input_tags.getUnitTag(a)
                output_tags.setUnitTag(a, tag)
                output_tags[a].resolution = input_tags[a].resolution

                if tagged_ideal_blockshape:
                    ideal_blockshape.append(tagged_ideal_blockshape[a])
                if tagged_max_blockshape:
                    max_blockshape.append(tagged_max_blockshape[a])
            else:
                output_shape.append(1)
                if tagged_ideal_blockshape:
                    ideal_blockshape.append(1)
                if tagged_max_blockshape:
                    max_blockshape.append(1)

        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.axistags = output_tags
        self.Output.meta.shape = tuple(output_shape)
        if self.Output.meta.original_axistags is None:
            assert len(input_tags) == len(self.Input.meta.shape)
            otags = copy.copy(input_tags)
            oshape = self.Input.meta.shape
            if not otags.axisTypeCount(vigra.AxisType.Channels):
                otags.insertChannelAxis()
                oshape += (1,)
            self.Output.meta.original_axistags = otags
            self.Output.meta.original_shape = oshape
        if tagged_ideal_blockshape:
            self.Output.meta.ideal_blockshape = ideal_blockshape
        if tagged_max_blockshape:
            self.Output.meta.max_blockshape = max_blockshape

        # These map between input axis indexes and output axis indexes
        # (Used to translate between input/output rois in execute() and propagateDirty())
        self._in_out_map = list(
            map(partial(_index, output_order), input_order)
        )  # For "abcd" and "bcde" in_out = [-1, 0, 1, 2]
        self._out_in_map = list(
            map(partial(_index, input_order), output_order)
        )  # For "abcd" and "bcde" out_in = [1, 2, 3, -1]

        # Find the 'common' axes shared by both the input and output
        input_common_axes = [a for a in input_order if a in output_order]  # Ordered by appearance on the input
        output_common_axes = [a for a in output_order if a in input_order]  # Ordered by appearance on the output

        # These are used by execute() to create a view of the 'result' array for the input to write into
        self._out_squeeze_slicing = tuple(slice(None) if a in input_order else 0 for a in output_order)
        self._common_axis_transpose_order = list(map(output_common_axes.index, input_common_axes))
        self._in_unsqueeze_slicing = tuple(slice(None) if a in output_order else numpy.newaxis for a in input_order)

    def execute(self, slot, subindex, out_roi, result):
        assert slot == self.Output, "Unknown output slot: {}".format(slot.name)
        assert len(self._invalid_axes) == 0, (
            "Can't exceute this OpReorderAxes because you are attempting to drop "
            "the following non-singleton axes: {}.".format(self._invalid_axes)
        )
        out_roi_dict = dict(enumerate(zip(out_roi.start, out_roi.stop)))
        out_roi_dict[-1] = (0, 1)  # Input axes that are missing on the output map to roi of 0:1

        in_roi_pairs = list(map(out_roi_dict.__getitem__, self._in_out_map))  # e.g. [(0,1), (0,10), (0,20)]
        in_roi = list(zip(*in_roi_pairs))  # e.g. [(0,0,0), (1,10,20)]

        # Create a view of the result that can be written to by the input slot.
        #   1) Drop (singleton) result axes that aren't used by the input
        #   2) Transpose such that 'common' axes are in the order expected by input
        #   3) Insert (singleton) axes that the

        # For example, if input is 'txyc' and output is 'yxzc'
        #  ('result' has axes 'yxzc')
        #   1) Drop 'z' axis: result[:,:,0,:] # view has axes 'yxc'
        #   2) Transpose 'common' axes to the order they appear on the input: 'yxc' -> 'xyc'
        #   3) Insert 't' axis: result[newaxis, :,:,:] # now has axes 'txyc'

        # Perform the transformations described above using predetermined slicings and transpose order.
        # This should be faster than using VigraArray.withAxes()
        result_squeezed = result[self._out_squeeze_slicing]  # (1)
        result_reordered = numpy.transpose(result_squeezed, self._common_axis_transpose_order)  # (2)
        result_input_view = result_reordered[self._in_unsqueeze_slicing]  # (3)

        # Now write into the special result view
        self.Input(*in_roi).writeInto(result_input_view).wait()
        return result

    def propagateDirty(self, inputSlot, subindex, in_roi):
        if inputSlot == self.AxisOrder:
            self.Output.setDirty()
        elif inputSlot == self.Input:
            # If this assertion triggers, it usually means that some upstream propagateDirty()
            # function is calling setDirty() with the wrong ROI.
            assert (
                len(in_roi.start) == len(in_roi.stop) == len(self.Input.meta.shape)
            ), "The dirty ROI ({}) appears incorrect for the InputSlot, which has shape {}.".format(
                in_roi, self.Input.meta.shape
            )

            in_roi_dict = dict(enumerate(zip(in_roi.start, in_roi.stop)))
            in_roi_dict[-1] = (0, 1)  # Output axes that are missing on the input map to roi 0:1

            out_roi_pairs = list(map(in_roi_dict.__getitem__, self._out_in_map))  # e.g. [(0,1), (0,10), (0,20)]
            out_roi = list(zip(*out_roi_pairs))  # e.g. [(0,0,0), (1,10,20)]
            self.Output.setDirty(*out_roi)
        else:
            assert False, "Unknown input slot: {}".format(inputSlot.name)


# Helper function: Like list.index(), but return -1 for missing elements instead of raising a ValueError
def _index(tup, element):
    try:
        return tup.index(element)
    except ValueError:
        return -1
