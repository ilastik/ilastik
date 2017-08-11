from builtins import zip
from builtins import range
import numpy as np
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestPool
from lazyflow.roi import roiToSlice

class OpSimpleStacker(Operator):
    """
    Stack arrays on an axis
    The axis must already exist in each of the inputs,
    and the inputs must already be in the same axis order.
    """
    Images = InputSlot(level=1)
    AxisFlag = InputSlot() # For example: 'z', or 'c'
    Output = OutputSlot()

    def __input__(self, *args, **kwargs):
        super(OpSimpleStacker, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        if len(self.Images) == 0:
            self.Output.meta.NOTREADY = True
            return

        # Sanity check
        stacked_axiskey = self.AxisFlag.value
        nonstacked_tagged_shape = self.Images[0].meta.getTaggedShape()
        del nonstacked_tagged_shape[stacked_axiskey]
        nonstacked_shape = tuple(nonstacked_tagged_shape.values())

        input_axes = self.Images[0].meta.getAxisKeys()
        first_dtype = self.Images[0].meta.dtype
        for slot in self.Images[1:]:
            assert stacked_axiskey in slot.meta.getAxisKeys(), \
                "Can't stack on an axis that doesn't exist yet."
            assert input_axes == slot.meta.getAxisKeys(), \
                "All stacked images must have the same axis order: {} != {}"\
                .format(input_axes, slot.meta.getAxisKeys())
            assert slot.meta.dtype == first_dtype, \
                "Can't stack images with different dtypes"

            tagged_shape = slot.meta.getTaggedShape()
            del tagged_shape[stacked_axiskey]
            assert tuple(tagged_shape.values()) == nonstacked_shape, \
                "Can't stack images whose shapes differ (other than the stacked axis itself)"

        stacked_sizes = []
        stacked_channel_names = []
        for slot_index, slot in enumerate(self.Images):
            stacked_sizes.append( slot.meta.getTaggedShape()[stacked_axiskey] )
            if slot.meta.channel_names:
                stacked_channel_names += slot.meta.channel_names
            else:
                slot_stacked_size = slot.meta.getTaggedShape()[stacked_axiskey]
                stacked_channel_names += ['stacked-image-{}-{}'.format(slot_index, i) for i in range(slot_stacked_size)]


        # Compute output ranges for each input.
        # For example, if inputs have length 10, 15, 20,
        # stacked_output_ranges = [(0, 10), (10, 25), (25, 45)]
        stacked_range_stops = [0] + list(np.add.accumulate(stacked_sizes))
        self.stacked_output_ranges = list(zip(stacked_range_stops[:-1], stacked_range_stops[1:]))

        # Assign output metadata
        self.Output.meta.assignFrom( self.Images[0].meta )
        stacked_axisindex = self.Images[0].meta.getAxisKeys().index(stacked_axiskey)
        output_shape = list(nonstacked_shape)
        output_shape.insert( stacked_axisindex, sum(stacked_sizes) )
        self.Output.meta.shape = tuple(output_shape)
        self.Output.meta.channel_names = stacked_channel_names
        ideal_blockshape = self.Output.meta.ideal_blockshape
        if ideal_blockshape is not None:
            ideal_blockshape = tuple(ideal_blockshape[:stacked_axisindex]) + (1,) + tuple(ideal_blockshape[stacked_axisindex+1:])
            self.Output.meta.ideal_blockshape = ideal_blockshape

        max_blockshape = self.Output.meta.max_blockshape
        if max_blockshape is not None:
            max_blockshape = max_blockshape[:stacked_axisindex] + (1,) + max_blockshape[stacked_axisindex+1:]
            self.Output.meta.max_blockshape = max_blockshape

    def execute(self, slot, subindex, roi, result):
        stacked_axisindex = self.Images[0].meta.getAxisKeys().index(self.AxisFlag.value)

        pool = RequestPool()
        for slot, (slot_output_start, slot_output_stop) in zip(self.Images, self.stacked_output_ranges):
            if roi.start[stacked_axisindex] >= slot_output_start and roi.stop[stacked_axisindex] <= slot_output_stop:
                output_roi = roi.copy()
                output_roi.start[stacked_axisindex] = max(slot_output_start, roi.start[stacked_axisindex])
                output_roi.stop[stacked_axisindex] = min(slot_output_stop, roi.stop[stacked_axisindex])

                request_roi = roi.copy()
                request_roi.start[stacked_axisindex] = output_roi.start[stacked_axisindex] - slot_output_start
                request_roi.stop[stacked_axisindex] = output_roi.stop[stacked_axisindex] - slot_output_start

                result_roi = roi.copy()
                result_roi.start = output_roi.start - roi.start
                result_roi.stop = output_roi.stop - roi.start

                req = slot(request_roi.start, request_roi.stop)
                req.writeInto( result[roiToSlice(result_roi.start, result_roi.stop)] )
                pool.add( req )
        pool.wait()

    def propagateDirty(self, slot, subindex, roi):
        if not self.Output.ready():
            return
        if slot is self.AxisFlag:
            self.Output.setDirty()
        elif slot is self.Images:
            stacked_axisindex = self.Images[0].meta.getAxisKeys().index(self.AxisFlag.value)
            output_range = self.stacked_output_ranges[subindex[0]]
            roi = roi.copy()
            roi.start[stacked_axisindex] = output_range[0]
            roi.stop[stacked_axisindex] = output_range[1]
            self.Output.setDirty(roi.start, roi.stop)
        else:
            assert False, "Unknown output slot: {}".format(slot.name)

if __name__ == "__main__":
    pass
