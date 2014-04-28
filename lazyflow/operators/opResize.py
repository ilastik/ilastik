import numpy
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpResize( Operator ):
    Input = InputSlot()
    ResizedShape = InputSlot()
    
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpResize, self ).__init__( *args, **kwargs )
        self._input_to_output_scales = None
    
    def setupOutputs(self):
        input_shape = self.Input.meta.shape
        output_shape = self.ResizedShape.value
        assert isinstance( output_shape, tuple )
        assert len(output_shape) == len(input_shape)
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.shape = output_shape

        self._input_to_output_scales = numpy.array( output_shape, dtype=numpy.float32 ) / input_shape
        
        axes = self.Input.meta.getAxisKeys()
        if 't' in axes:
            assert self._input_to_output_scales[ axes.index('t') ] == 1.0, \
                "Resizing the time dimension is not supported (yet)."
    
    def execute(self, slot, subindex, output_roi, result):
        # Special fast path if no resampling needed
        if self.Input.meta.shape == self.Output.meta.shape:
            self.Input(output_roi.start, output_roi.stop).writeInto(result).wait()
            return result

        # Map output_roi to input_roi
        output_roi = numpy.array( (output_roi.start, output_roi.stop) )
        input_roi = output_roi / self._input_to_output_scales

        # Convert to int (round start down, round stop up)
        input_roi[1] += 0.5
        input_roi = input_roi.astype(int)

        # Request input and resize it.
        # FIXME: This is not quite correct.  We should request a halo that is wide enough 
        #        for the BSpline used by resize(). See vigra docs for BSlineBase.radius()        
        input_data = self.Input( *input_roi ).wait()
        
        if self.Input.meta.dtype == numpy.float32:
            vigra.sampling.resize( input_data, out=result )
        else:
            input_data = input_data.astype( numpy.float32 )
            result_float = vigra.sampling.resize(input_data, shape=result.shape)
            result[:] = result_float.round()
        return result

    def propagateDirty(self, slot, subindex, input_roi):
        # FIXME: When execute() is fixed to use a halo, we should also 
        #        incorporate the halo into this dirty propagation logic.
        
        # Map input_roi to output_roi
        input_roi = numpy.array( (input_roi.start, input_roi.stop) )
        output_roi = input_roi * self._input_to_output_scales
        
        # Convert to int (round start down, round stop up)
        output_roi[1] += 0.5
        output_roi = output_roi.astype(int)

        self.Output.setDirty( *output_roi )
