###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2016, the ilastik developers
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
#		   http://ilastik.org/license/
###############################################################################
from __future__ import division
from builtins import zip
from builtins import range
import copy
import collections

import numpy
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from .opReorderAxes import OpReorderAxes
from lazyflow.utility import OrderedSignal

class OpResize5D( Operator ):
    """
    Resize a 5D image.
    Notes:
        - Input must be 5D, tzyxc
        - Resizing is performed across zyx dimensions only. time dimension may not be resized.
    """
    Input = InputSlot()
    ResizedShape = InputSlot()
    
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpResize5D, self ).__init__( *args, **kwargs )
        self._input_to_output_scales = None
        self.progressSignal = OrderedSignal()
    
    def setupOutputs(self):
        assert self.Input.meta.getAxisKeys() == list('tzyxc')
        input_shape = self.Input.meta.shape
        output_shape = self.ResizedShape.value
        assert isinstance( output_shape, tuple )
        assert len(output_shape) == len(input_shape)
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.shape = output_shape

        self._input_to_output_scales = numpy.array( output_shape, dtype=numpy.float32 ) / input_shape
        
        axes = self.Input.meta.getAxisKeys()
        if 'c' in axes:
            assert self._input_to_output_scales[ axes.index('c') ] == 1.0, \
                "Resizing the channel dimension is not supported."
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
        input_roi = output_roi // self._input_to_output_scales

        # Convert to int (round start down, round stop up)
        input_roi[1] += 0.5
        input_roi = input_roi.astype(int)

        t_start = output_roi[0][0]
        t_stop = output_roi[1][0]
        
        def process_timestep( t ):
            # Request input and resize it.            
            # FIXME: This is not quite correct.  We should request a halo that is wide enough 
            #        for the BSpline used by resize(). See vigra docs for BSlineBase.radius()        
            step_input_roi = copy.copy(input_roi)
            step_input_roi[0][0] = t
            step_input_roi[1][0] = t+1

            step_input_data = self.Input( *step_input_roi ).wait()
            step_input_data = vigra.taggedView( step_input_data, 'tzyxc' )
            
            step_shape_4d = numpy.array(step_input_data[0].shape)
            step_shape_4d_nochannel = step_shape_4d[:-1]
            squeezed_slicing = numpy.where(step_shape_4d_nochannel == 1, 0, slice(None))
            squeezed_slicing = tuple(squeezed_slicing) + (slice(None),)
            
            step_input_squeezed = step_input_data[0][squeezed_slicing]
            result_step = result[t][squeezed_slicing]
            # vigra assumes wrong axis order if we don't specify one explicitly here...
            result_step = vigra.taggedView( result_step, step_input_squeezed.axistags )
            
            if self.Input.meta.dtype == numpy.float32:
                vigra.sampling.resize( step_input_squeezed, out=result_step )
            else:
                step_input_squeezed = step_input_squeezed.astype( numpy.float32 )
                result_float = vigra.sampling.resize(step_input_squeezed, shape=result_step.shape[:-1])
                result_step[:] = result_float.round()

        # FIXME: Progress here will not be correct for multiple threads.
        self.progressSignal(0)        

        # FIXME: request pool...
        for t in range( t_start, t_stop ):
            process_timestep( t )
            progress = 100*(t-t_start)//(t_stop-t_start)
            self.progressSignal( int(progress) )
        self.progressSignal(100)

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

class OpResize(Operator):
    Input = InputSlot()
    ResizedShape = InputSlot()
    
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpResize, self ).__init__(*args, **kwargs)
        self._op5_in = OpReorderAxes( parent=self )
        self._op5_in.Input.connect( self.Input )
        self._op5_in.AxisOrder.setValue( 'tzyxc' )
        
        self._opResize5D = OpResize5D( parent=self )
        self._opResize5D.Input.connect( self._op5_in.Output )
        # ResizedShape is configured below (must be reordered for 5D)
        
        self._op5_out = OpReorderAxes( parent=self )
        self._op5_out.Input.connect( self._opResize5D.Output )
        # AxisOrder is configured below
        self.Output.connect( self._op5_out.Output )
        
        self.progressSignal = self._opResize5D.progressSignal

    def setupOutputs(self):
        axes = self.Input.meta.getAxisKeys()
        self._op5_out.AxisOrder.setValue( "".join( axes ) )

        # Reorder the shape for 5D        
        orig_shape = self.ResizedShape.value
        tagged_shape = collections.OrderedDict( list(zip( self.Input.meta.getAxisKeys(), orig_shape )) )
        for k in 'tzyxc':
            if k not in tagged_shape:
                tagged_shape[k] = 1
        
        reordered_shape = [tagged_shape[k] for k in 'tzyxc']
        self._opResize5D.ResizedShape.setValue( tuple(reordered_shape) )
    
    def propagateDirty(self, slot, subindex, input_roi):
        pass

    def execute(self, slot, subindex, output_roi, result):
        assert False, "Shouldn't get here."
