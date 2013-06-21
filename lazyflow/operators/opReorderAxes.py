import copy
from functools import partial
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpReorderAxes(Operator):
    Input = InputSlot()
    AxisOrder = InputSlot(value='txyzc') # string: The desired output axis order
    Output = OutputSlot()

    def setupOutputs(self):
        output_order = self.AxisOrder.value
        input_order = self.Input.meta.getAxisKeys()
        input_tags = self.Input.meta.axistags
        tagged_input_shape = self.Input.meta.getTaggedShape()

        # Check for errors
        for a in set(input_order) - set(output_order):
            assert tagged_input_shape[a] <= 1, "OpReorderAxes: Cannot drop non-singleton axis '{}'".format( a )

        # Determine output shape/axistags
        output_shape = []
        output_tags = vigra.defaultAxistags(output_order)
        for a in output_order:
            if a in input_order:
                output_shape.append(tagged_input_shape[a])
                # Preserve full AxisInfo for retained axes
                output_tags[a] = input_tags[a]
            else:
                output_shape.append(1)

        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.axistags = output_tags
        self.Output.meta.shape = tuple(output_shape)
        if self.Output.meta.original_axistags is None:
            self.Output.meta.original_axistags = copy.copy(input_tags)
            self.Output.meta.original_shape = self.Input.meta.shape
            assert len(input_tags) == len(self.Input.meta.shape)

        # These map between input axis indexes and output axis indexes
        self._in_out_map = map( partial(_index, output_order), input_order ) # For "abcd" and "bcde" in_out = [-1, 0, 1, 2]
        self._out_in_map = map( partial(_index, input_order), output_order ) # For "abcd" and "bcde" out_in = [1, 2, 3, -1]    

    def execute(self, slot, subindex, out_roi, result):
        assert slot == self.Output, "Unknown output slot: {}".format( slot.name )
        out_roi_dict = dict( enumerate( zip(out_roi.start, out_roi.stop) ) )
        out_roi_dict[-1] = (0,1) # Input axes that are missing on the output map to roi of 0:1

        in_roi_pairs = map( out_roi_dict.__getitem__, self._in_out_map ) # e.g. [(0,1), (0,10), (0,20)]
        in_roi = zip( *in_roi_pairs ) # e.g. [(0,0,0), (1,10,20)]

        result_view_out = result.view( vigra.VigraArray )
        result_view_out.axistags = self.Output.meta.axistags
        result_view_in = result_view_out.withAxes( *self.Input.meta.getAxisKeys() )
        self.Input( *in_roi ).writeInto( result_view_in ).wait()
        return result

    def propagateDirty(self, inputSlot, subindex, in_roi):
        if inputSlot == self.AxisOrder:
            self.Output.setDirty()
        elif inputSlot == self.Input:
            in_roi_dict = dict( enumerate( zip(in_roi.start, in_roi.stop) ) )
            in_roi_dict[-1] = (0,1) # Output axes that are missing on the input map to roi 0:1

            out_roi_pairs = map( in_roi_dict.__getitem__, self._out_in_map ) # e.g. [(0,1), (0,10), (0,20)]
            out_roi = zip( *out_roi_pairs ) # e.g. [(0,0,0), (1,10,20)]
            self.Output.setDirty( *out_roi )
        else:
            assert False, "Unknown input slot: {}".format( inputSlot.name )

# Helper function: Like list.index(), but return -1 for missing elements instead of raising a ValueError
def _index(tup, element):
    try:
        return tup.index(element)
    except ValueError:
        return -1

