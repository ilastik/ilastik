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
#		   http://ilastik.org/license/
###############################################################################
import os
import collections
import warnings
import numpy

from lazyflow.utility import format_known_keys
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiFromShape
from lazyflow.operators.generic import OpSubRegion, OpPixelOperator
from lazyflow.operators.valueProviders import OpMetadataInjector
from lazyflow.operators.opReorderAxes import OpReorderAxes

from .opExportSlot import OpExportSlot

class OpFormattedDataExport(Operator):
    """
    Wraps OpExportSlot, but with optional preprocessing:
    - cut out a subregion
    - renormalize the data
    - convert to a different dtype
    - transpose axis order
    """
    TransactionSlot = InputSlot() # To apply all settings in one 'transaction', 
                                  # disconnect this slot and reconnect it when all slots are ready
                                  # This avoids multiple calls to setupOutputs when setting several optional slots in a row.

    Input = InputSlot()

    # Subregion params: 'None' can be provided for any axis, in which case it means 'full range' for that axis
    RegionStart = InputSlot(optional=True)
    RegionStop = InputSlot(optional=True)

    # Normalization params    
    InputMin = InputSlot(optional=True)
    InputMax = InputSlot(optional=True)
    ExportMin = InputSlot(optional=True)
    ExportMax = InputSlot(optional=True)

    ExportDtype = InputSlot(optional=True)
    OutputAxisOrder = InputSlot(optional=True)
    
    # File settings
    OutputFilenameFormat = InputSlot(value=os.path.expanduser('~')+os.sep+'RESULTS_{roi}') # A format string allowing {roi}, {x_start}, {x_stop}, etc.
    OutputInternalPath = InputSlot(value='exported_data')
    OutputFormat = InputSlot(value='hdf5')

    ConvertedImage = OutputSlot() # Not yet re-ordered
    ImageToExport = OutputSlot() # Preview of the pre-processed image that will be exported
    ExportPath = OutputSlot() # Location of the saved file after export is complete.
    FormatSelectionErrorMsg = OutputSlot() # True or False depending on whether or not the currently selected format can support the current export data.
    
    ALL_FORMATS = OpExportSlot.ALL_FORMATS
    
    # Simplified block diagram:                                          -> ConvertedImage                -> FormatSelectionErrorMsg
    #                                                                   /                                /
    # Input -> opSubRegion -> opDrangeInjection -> opNormalizeAndConvert -> opReorderAxes -> opExportSlot -> ExportPath
    #                                                                                    \
    #                                                                                     -> ImageToExport
    
    def __init__(self, *args, **kwargs):
        super( OpFormattedDataExport, self ).__init__(*args, **kwargs)
        self._dirty = True

        opSubRegion = OpSubRegion( parent=self )
        opSubRegion.Input.connect( self.Input )
        self._opSubRegion = opSubRegion
        
        # If normalization parameters are provided, we inject a 'drange' 
        #  metadata item for downstream operators/gui to use.
        opDrangeInjection = OpMetadataInjector( parent=self )
        opDrangeInjection.Input.connect( opSubRegion.Output )
        self._opDrangeInjection = opDrangeInjection

        # Normalization and dtype conversion are performed in one step
        #  using an OpPixelOperator.
        opNormalizeAndConvert = OpPixelOperator( parent=self )
        opNormalizeAndConvert.Input.connect( opDrangeInjection.Output )
        self._opNormalizeAndConvert = opNormalizeAndConvert

        # ConvertedImage shows the full result but WITHOUT axis reordering.
        self.ConvertedImage.connect( self._opNormalizeAndConvert.Output )
        
        opReorderAxes = OpReorderAxes( parent=self )
        opReorderAxes.Input.connect( opNormalizeAndConvert.Output )
        self._opReorderAxes = opReorderAxes

        self.ImageToExport.connect( opReorderAxes.Output )
        
        self._opExportSlot = OpExportSlot( parent=self )
        self._opExportSlot.Input.connect( opReorderAxes.Output )
        self._opExportSlot.OutputFormat.connect( self.OutputFormat )
        
        self.ExportPath.connect( self._opExportSlot.ExportPath )
        self.FormatSelectionErrorMsg.connect( self._opExportSlot.FormatSelectionErrorMsg )
        self.progressSignal = self._opExportSlot.progressSignal

    def setupOutputs(self):
        # Prepare subregion operator
        total_roi = roiFromShape( self.Input.meta.shape )
        total_roi = map( tuple, total_roi )

        # Default to full roi
        new_start, new_stop = total_roi

        if self.RegionStart.ready():
            # RegionStart is permitted to contain 'None' values, which we replace with zeros
            new_start = map(lambda x: x or 0, self.RegionStart.value)

        if self.RegionStop.ready():
            # RegionStop is permitted to contain 'None' values, 
            #  which we replace with the full extent of the corresponding axis
            new_stop = map( lambda (x, extent): x or extent, zip(self.RegionStop.value, total_roi[1]) )

        clipped_start = numpy.maximum(0, new_start)
        clipped_stop = numpy.minimum(total_roi[1], new_stop)
        if (clipped_start != new_start).any() or (clipped_stop != new_stop).any():
            warnings.warn("The ROI you are attempting to export exceeds the extents of your dataset.  Clipping to dataset bounds.")

        new_start, new_stop = tuple(clipped_start), tuple(clipped_stop)

        # If we're in the process of switching input data, 
        #  then the roi dimensionality might not match up.
        #  Just leave the roi disconnected for now.
        if len(self.Input.meta.shape) != len(new_start) or \
           len(self.Input.meta.shape) != len(new_stop):
            self._opSubRegion.Roi.disconnect()
        elif not self._opSubRegion.Roi.ready() or \
           self._opSubRegion.Roi.value != (new_start, new_stop):

            # Provide the coordinate offset, but only for the axes that are present in the output image
            tagged_input_offset = collections.defaultdict( lambda: -1, zip(self.Input.meta.getAxisKeys(), new_start ) )
            output_axes = self._opReorderAxes.AxisOrder.value
            output_offset = [ tagged_input_offset[axis] for axis in output_axes ]
            output_offset = tuple( filter( lambda x: x != -1, output_offset ) )
            self._opExportSlot.CoordinateOffset.setValue( output_offset )

            self._opSubRegion.Roi.setValue( (new_start, new_stop) )

        # Set up normalization and dtype conversion
        export_dtype = self.Input.meta.dtype
        if self.ExportDtype.ready():
            export_dtype = self.ExportDtype.value

        need_normalize = ( self.InputMin.ready() and 
                           self.InputMax.ready() and 
                           self.ExportMin.ready() and 
                           self.ExportMax.ready() )
        if need_normalize:
            minVal, maxVal = self.InputMin.value, self.InputMax.value
            outputMinVal, outputMaxVal = self.ExportMin.value, self.ExportMax.value

            # Force a drange onto the input slot metadata.
            # opNormalizeAndConvert is an OpPixelOperator, 
            #  which transforms the drange correctly in this case.
            self._opDrangeInjection.Metadata.setValue( { 'drange' : (minVal, maxVal) } )
            
            def normalize(a):
                numerator = numpy.float64(outputMaxVal) - numpy.float64(outputMinVal)
                denominator = numpy.float64(maxVal) - numpy.float64(minVal)
                if denominator != 0.0:
                    frac = numpy.float32(numerator / denominator)
                else:
                    # Denominator was zero.  The user is probably just temporarily changing the values.
                    frac = numpy.float32(0.0)
                result = numpy.asarray(outputMinVal + (a - minVal) * frac, export_dtype)
                return result
            self._opNormalizeAndConvert.Function.setValue( normalize )

            # The OpPixelOperator sets the drange correctly using the function we give it.
            output_drange = self._opNormalizeAndConvert.Output.meta.drange
            assert type(output_drange[0]) == export_dtype
            assert type(output_drange[1]) == export_dtype
        else:
            # We have no drange to set.
            # If the original slot metadata had a drange, 
            #  it will be propagated downstream anyway.
            self._opDrangeInjection.Metadata.setValue( {} )

            # No normalization: just identity function with dtype conversion
            self._opNormalizeAndConvert.Function.setValue( lambda a: numpy.asarray(a, export_dtype) )

        # Use user-provided axis order if specified
        if self.OutputAxisOrder.ready():
            self._opReorderAxes.AxisOrder.setValue( self.OutputAxisOrder.value )
        else:
            axistags = self.Input.meta.axistags
            self._opReorderAxes.AxisOrder.setValue( "".join( tag.key for tag in axistags ) )

        # Obtain values for possible name fields
        known_keys = { 'roi' : list(self._opSubRegion.Roi.value) }

        # Blank the internal path while we update the external path
        #  to avoid invalid intermediate states of ExportPath
        self._opExportSlot.OutputInternalPath.setValue( "" )
        
        # use partial formatting to fill in non-coordinate name fields
        name_format = self.OutputFilenameFormat.value
        partially_formatted_path = format_known_keys( name_format, known_keys )
        self._opExportSlot.OutputFilenameFormat.setValue( partially_formatted_path )

        internal_dataset_format = self.OutputInternalPath.value 
        partially_formatted_dataset_name = format_known_keys( internal_dataset_format, known_keys )
        self._opExportSlot.OutputInternalPath.setValue( partially_formatted_dataset_name )
        
    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"
    
    def propagateDirty(self, slot, subindex, roi):
        self._dirty = True

    def run_export(self):
        self._opExportSlot.run_export()

    def run_export_to_array(self):
        return self._opExportSlot.run_export_to_array()
